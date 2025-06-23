import os
from typing import TypedDict, List, Annotated

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from models import QueryAnalysisResult
from services import QueryAnalyzer

load_dotenv()

# Ensure the OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
  raise ValueError(
    "OPENAI_API_KEY environment variable not set. "
    "Please create a .env file with your API key."
  )


class AgentState(TypedDict):
  """AgentState is more complex than a simple Q/A chat bot. 
  It tracks conversation history AND structured trip data.
  The trip_plan field persists the extracted information between nodes.
  Each node can read/write to trip_plan as the workflow progresses.
  Why this matters:
  Node 1 (QueryAnalyzer) extracts destination, budget, etc. → stores in trip_plan
  Node 2 (WeatherService) reads destination from trip_plan → adds weather data
  Node 3 (HotelCalculator) reads budget from trip_plan → calculates costs
  The conversation context AND the structured data flow together through the graph

  Args:
      TypedDict (_type_): _description_
  """
  messages: Annotated[List[BaseMessage], lambda x, y: x + y]
  trip_plan: QueryAnalysisResult
  phase: str  # "collecting", "planning", "refining"
  complete_plan: dict  # The full generated plan


class TravelWorkflow:
  def __init__(self):
    self.query_analyzer = QueryAnalyzer()
    self.graph = self._build_graph()

  def _build_graph(self):
    workflow = StateGraph(AgentState)

    workflow.add_node("query_analyzer", self.query_analyzer_node)
    # We will add more nodes here for planning, collecting info, etc.
    # workflow.add_node("interactive_collector", self.interactive_collector_node)
    # workflow.add_node("trip_planner", self.trip_planner_node)

    workflow.set_entry_point("query_analyzer")

    # For now, a simple path, this will become more complex
    workflow.add_edge("query_analyzer", END)

    memory = SqliteSaver.from_conn_string(":memory:")
    # SqliteSaver providing checkpointing - the ability to pause/resume conversations
    return workflow.compile(checkpointer=memory)

  def query_analyzer_node(self, state: AgentState):
    """
    Analyzes the user's query to extract key information and identify missing fields.
    """
    last_message = state["messages"][-1].content
    analysis_result = self.query_analyzer.analyze(last_message)

    # In a real scenario, we'd have a system message directing the LLM
    # For now, we'll just return the placeholder response
    response_message = (
      f"Analysis complete. "
      f"Destination: {analysis_result.destination}. "
      f"Missing info: {analysis_result.missing_fields}"
    )

    return {
      "messages": [HumanMessage(content=response_message)],
      "trip_plan": analysis_result,
    }

  def run(self, query: str, thread_id: str):
    """
    Executes the workflow with a user query.
    """
    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": thread_id}}
# Purpose:
# Tells LangGraph "this conversation belongs to thread_id X"
# LangGraph uses this to load the correct checkpointed state
# Without it, every message would start a new conversation
# Why thread_id:
# Multiple users can use the app simultaneously
# Each gets their own conversation thread
# Streamlit session state provides the thread_id
    return self.graph.stream(inputs, config=config) # stream is used to send the response in chunks
#graph.invoke() - runs entire graph and returns final result
# graph.stream() - runs graph step-by-step, yielding events
# graph.batch() - runs multiple inputs in parallel
#<eof>