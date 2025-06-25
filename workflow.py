from services.workflow_nodes import (
  node_travel_evaluator,
  node_query_analyzer,
  node_hotel_agent,
  node_weather_agent,
  node_attractions_agent,
  node_calculator_agent,
  node_itinerary_agent,
  node_summary_agent,
)
from models import WorkflowState
from langgraph.graph import StateGraph, START, END

# Build the simplified graph
workflow = StateGraph(WorkflowState)
workflow.add_node("query_analyzer", node_query_analyzer)
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

workflow.add_edge("query_analyzer", "hotel_agent")
workflow.add_edge("hotel_agent", "weather_agent")
workflow.add_edge("weather_agent", "attractions_agent")
workflow.add_edge("attractions_agent", "calculator_agent")
workflow.add_edge("calculator_agent", "itinerary_agent")
workflow.add_edge("itinerary_agent", "summary_agent")
workflow.add_edge("summary_agent", END)

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