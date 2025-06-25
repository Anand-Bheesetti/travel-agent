from models import QueryAnalysisResult, TripPlan, WorkflowState, HotelInfo
from services.query_analyzer import QueryAnalyzer
from services.hotels import HotelFinder
from services.weather import WeatherService
from services.attractions import AttractionFinder
from services.currency import CurrencyConverter
from services.calculator import Calculator
from services.itinerary import ItineraryBuilder
from services.summary import TripSummary
from langchain_core.messages import HumanMessage, AIMessage
from services.llm_utils import get_llm, make_system_prompt
from typing import Literal
import datetime
import json
from pydantic import ValidationError, BaseModel
from langchain_tavily import TavilySearch
import re
from langgraph.types import Command

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
travel_evaluator = make_system_prompt(
    """
    You are a travel query evaluator. Your job is to determine if a user message is travel-related.
    A travel-related query should mention or imply:
    - A destination or place to visit
    - Travel dates or duration
    - Travel activities, accommodation, or budget
    
    Respond with ONLY \"TRAVEL\" if it's travel-related, or \"NOT_TRAVEL\" if it's not.
    """
)

from langgraph.prebuilt import create_react_agent

hotel_agent = create_react_agent(
  model=get_llm(),
  tools=[hotel_finder.find_hotels],
  prompt=make_system_prompt(
    f"""
    You are a hotel search expert. Your job is to find hotels and estimate costs. Today is {_today}. Do not use dates in the past.
    Always return a list of hotels in the following strict JSON format (no text, no summary):
    [
      {{
        \"name\": \"...\",\n        \"price_per_night\": ..., \n        \"review_count\": ..., \n        \"rating\": ..., \n        \"url\": \"...\"\n      }}
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
    eval_result = TravelEvaluationResult(result=response)
  except ValidationError:
    raise ValueError(f"Invalid travel evaluator output: {response}")
  if eval_result.result == "NOT_TRAVEL":
    state.messages.append(AIMessage(content="Sorry, I am a travel agent. Please ask a travel-related question."))
    return {"messages": state.messages}
  return response

def node_query_analyzer(state: WorkflowState) -> Command:
  """Analyze the user message and extract trip info."""
  print("\n---- QUERY ANALYZER ----")
  user_msg = state.messages[-1].content
  result: QueryAnalysisResult = query_analyzer.analyze(str(user_msg))
  for k, v in result.model_dump().items():
    setattr(state, k, v)
  print(f"Analysis result: {result.model_dump()}")
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
  return Command(goto="END", update=state) 