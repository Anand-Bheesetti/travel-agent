from models import QueryAnalysisResult, TripPlan, WorkflowState, HotelInfo
from services.query_analyzer import QueryAnalyzer
from services.hotels import HotelFinder
from services.weather import WeatherService
from services.attractions import AttractionFinder
from services.currency import CurrencyConverter
from services.calculator import Calculator
from services.itinerary import ItineraryBuilder
from services.summary import TripSummary
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage
from langgraph.types import Command
from services.llm_utils import get_llm, make_system_prompt
from typing import Optional, Dict, Any, List, Union, Literal
import datetime
import json
from pydantic import ValidationError, BaseModel
from langchain_tavily import TavilySearch
import re
from services.user_prompt_agent import extract_user_fields_from_messages

# Instantiate all agents/tools
query_analyzer = QueryAnalyzer()
hotel_finder = HotelFinder()
weather_service = WeatherService()
attraction_finder = AttractionFinder()
currency_converter = CurrencyConverter()
calculator = Calculator()
itinerary_builder = ItineraryBuilder()
summary_generator = TripSummary()
search_tool = TavilySearch()

def get_today() -> str:
  """Returns today's date in YYYY-MM-DD format."""
  return datetime.date.today().isoformat()

_today = get_today()

# Create a simple travel query evaluator
travel_evaluator = create_react_agent(
  model=get_llm(),
  tools=[],
  prompt=make_system_prompt(
    """
    You are a travel query evaluator. Your job is to determine if a user message is travel-related.
    A travel-related query should mention or imply:
    - A destination or place to visit
    - Travel dates or duration
    - Travel activities, accommodation, or budget
    
    Respond with ONLY "TRAVEL" if it's travel-related, or "NOT_TRAVEL" if it's not.
    """
  )
)

hotel_agent = create_react_agent(
  model=get_llm(),
  tools=[hotel_finder.find_hotels],
  prompt=make_system_prompt(
    f"""
    You are a hotel search expert. Your job is to find hotels and estimate costs. Today is {_today}. Do not use dates in the past.
    Always return a list of hotels in the following strict JSON format (no text, no summary):
    [
      {{
        \"name\": \"...\",
        \"price_per_night\": ..., 
        \"review_count\": ..., 
        \"rating\": ..., 
        \"url\": \"...\"
      }}
    ]
    Do not include photos. Do not return any text or explanation, only the JSON list.
    """
  )
)

weather_agent = create_react_agent(
  model=get_llm(),
  tools=[weather_service.get_weather],
  prompt=make_system_prompt(f"You are a weather expert. Your job is to fetch weather forecasts for the trip destination. Today is {_today}. Do not use dates in the past.")
)

attractions_agent = create_react_agent(
  model=get_llm(),
  tools=[attraction_finder.find_attractions, attraction_finder.estimate_attractions_cost, search_tool],
  prompt=make_system_prompt(f"You are an attractions expert. Your job is to find attractions and estimate their costs. If you are routed back by the supervisor, you may use the search tool to look up the latest information. Today is {_today}. Do not use dates in the past.")
)

calculator_agent = create_react_agent(
  model=get_llm(),
  tools=[calculator.add, calculator.subtract, calculator.multiply, calculator.divide, currency_converter.convert, search_tool],
  prompt=make_system_prompt(f"""
You are a calculator and budget allocation expert. Your job is to:
- Extract all costs you can find from the provided state (e.g., hotel prices, attraction costs, etc.).
- Split the user's budget by these costs and provide a clear breakdown.
- If you are missing any cost or are uncertain about a cost, you may use the search tool to look up the latest prices or estimates for any travel-related expense (e.g., food, transportation, tickets, etc.).
- Use the search tool whenever you feel it is necessary to allocate the budget accurately.
- If currency conversion is needed, use the currency conversion tool.
- Return a clear, itemized breakdown of all costs and any conversions performed.
Today is {_today}. Do not use dates in the past.
""")
)

# Node functions
class TravelEvaluationResult(BaseModel):
  result: Literal["TRAVEL", "NOT_TRAVEL"]

def node_travel_evaluator(state: WorkflowState) -> dict:
  """Check if query is travel-related. If not, end conversation."""
  print("\n---- TRAVEL EVALUATOR ----")
  user_msg = state.messages[-1].content
  result = travel_evaluator.invoke({"messages": [HumanMessage(content=str(user_msg))]})
  response = result['messages'][-1].content
  try:
    TravelEvaluationResult(result=response)
  except ValidationError:
    raise ValueError(f"Invalid travel evaluator output: {response}")
  return response

def node_query_analyzer(state: WorkflowState) -> Command:
  """Analyze the latest user message and update state with extracted trip info. If not travel-related, end."""
  print("\n---- QUERY ANALYZER ----")
  print(f"Messages: {state.messages}")
  user_msg = state.messages[-1].content
  result: QueryAnalysisResult = query_analyzer.analyze(str(user_msg))
  required_fields = ["destination", "budget", "native_currency", "days"]
  is_empty = all(getattr(result, f, None) in (None, "") for f in required_fields)
  if is_empty:
    state.messages.append(AIMessage(content="Sorry, I am a travel agent. Please ask a travel-related question."))
    return Command(goto=END, update=state)
  for k, v in result.model_dump().items():
    setattr(state, k, v)
  state.missing_fields = result.missing_fields
  print(f"Analysis result: {result.model_dump()}")
  state.messages.append(AIMessage(content=f"Analysis result: {result.model_dump()}"))
  return Command(goto="check_missing", update=state)

def node_check_missing(state: WorkflowState) -> Command:
  print("\n---- CHECK MISSING FIELDS ----")
  required_fields = ["destination", "days", "budget", "native_currency"]
  missing = [f for f in required_fields if not getattr(state, f, None)]
  print(f"Missing fields: {missing}")
  if missing:
    if len(missing) == len(required_fields):
      state.messages.append(AIMessage(content="Sorry, I am a travel agent. Please ask a travel-related question."))
      return Command(goto=END, update=state)
    state.prompt = f"Please provide: {', '.join(missing)}"
    state.missing_fields = missing
    return Command(goto="user_prompt", update=state)
  state.missing_fields = []
  return Command(goto="hotel_agent", update=state)

def node_user_prompt(state: WorkflowState) -> Command:
  print("\n---- USER INPUT FOR MISSING FIELDS (LLM AGENT) ----")
  try:
    result, llm_message = extract_user_fields_from_messages(state)
    for k, v in result.items():
      if k != "messages" and k in (state.missing_fields or []):
        setattr(state, k, v)
    state.messages.append(HumanMessage(content=state.messages[-1].content))
    state.messages.append(llm_message)
    print(f"Updated fields: {result}")
  except Exception as e:
    state.messages.append(AIMessage(content=f"Failed to extract fields: {e}"))
    print(f"Failed to extract fields: {e}")
  state.missing_fields = []
  return Command(goto="hotel_agent", update=state)

def node_hotel_agent(state: WorkflowState) -> Command:
  print("\n---- HOTEL AGENT ----")
  result = hotel_agent.invoke(state)
  raw_content = result['messages'][-1].content
  try:
    hotels_data = json.loads(raw_content)
    hotels = [HotelInfo(**h) for h in hotels_data]
    state.hotels = hotels
    print(f"Hotels: {hotels}")
  except (json.JSONDecodeError, ValidationError, TypeError) as e:
    print(f"Hotel agent error: {e}")
    state.hotels = []
  return Command(goto="weather_agent", update=state)

def node_weather_agent(state: WorkflowState) -> Command:
  print("\n---- WEATHER AGENT ----")
  result = weather_agent.invoke({"messages": state.messages})
  state.weather = result['messages'][-1].content
  print(f"Weather: {state.weather}")
  return Command(goto="attractions_agent", update=state)

def node_attractions_agent(state: WorkflowState) -> Command:
  print("\n---- ATTRACTIONS AGENT ----")
  result = attractions_agent.invoke(state)
  state.attractions = result['messages'][-1].content
  print(f"Attractions found: {state.attractions}")
  return Command(goto="calculator_agent", update=state)

def node_calculator_agent(state: WorkflowState) -> Command:
  print("\n---- CALCULATOR AGENT ----")
  result = calculator_agent.invoke(state)
  state.calculator_result = result['messages'][-1].content
  print(f"Calculator result: {state.calculator_result}")
  return Command(goto="itinerary_agent", update=state)

def node_itinerary_agent(state: WorkflowState) -> Command:
  print("\n---- ITINERARY AGENT ----")
  itinerary = itinerary_builder.build(state)
  state.itinerary = itinerary
  print(f"Itinerary: {itinerary}")
  return Command(goto="summary_agent", update=state)

def node_summary_agent(state: WorkflowState) -> Command:
  print("\n---- SUMMARY AGENT ----")
  summary = summary_generator.generate_summary({
    'messages': state.messages,
    "destination": state.destination,
    "days": state.days,
    "attractions": state.attractions or [],
    "hotel_info": state.hotels,
    "weather": state.weather,
    "itinerary": state.itinerary,
    "calculator_result": state.calculator_result
  })
  state.summary = summary
  print(f"Summary: {summary}")
  return Command(goto=END, update=state)

# Build the simplified graph
workflow = StateGraph(WorkflowState)
workflow.add_node("query_analyzer", node_query_analyzer)
workflow.add_node("check_missing", node_check_missing)
workflow.add_node("user_prompt", node_user_prompt)
workflow.add_node("hotel_agent", node_hotel_agent)
workflow.add_node("weather_agent", node_weather_agent)
workflow.add_node("attractions_agent", node_attractions_agent)
workflow.add_node("calculator_agent", node_calculator_agent)
workflow.add_node("itinerary_agent", node_itinerary_agent)
workflow.add_node("summary_agent", node_summary_agent)

# Conditional edge for travel_evaluator
workflow.add_conditional_edges(
    START,
    node_travel_evaluator,
    {"TRAVEL": "query_analyzer", "NOT_TRAVEL": END}
)

workflow.add_edge("query_analyzer", "check_missing")
workflow.add_edge("check_missing", "user_prompt")
workflow.add_edge("check_missing", "hotel_agent")
workflow.add_edge("user_prompt", "query_analyzer")
workflow.add_edge("hotel_agent", "weather_agent")
workflow.add_edge("weather_agent", "attractions_agent")
workflow.add_edge("attractions_agent", "calculator_agent")
workflow.add_edge("calculator_agent", "itinerary_agent")
workflow.add_edge("itinerary_agent", "summary_agent")
workflow.add_edge("summary_agent", END)
workflow.add_edge("query_analyzer", END)

app = workflow.compile()

# For CLI/manual test
if __name__ == "__main__":
  state = WorkflowState(
    destination=None,
    budget=None,
    native_currency=None,
    days=None,
    group_size=None,
    activity_preferences=None,
    accommodation_type=None,
    dietary_restrictions=None,
    transportation_preferences=None,
    messages=[HumanMessage(content="I want to go to Paris for 3 days, my budget is 1000 EUR, I like art and culture, my currency is USD")]
  )
  result = app.invoke(state)