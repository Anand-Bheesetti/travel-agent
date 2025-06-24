from services.llm_utils import get_llm
from services.attractions import AttractionFinder
from services.weather import WeatherService
from services.hotels import HotelCalculator
from services.currency import CurrencyConverter
from services.itinerary import ItineraryBuilder
from services.summary import TripSummary
from services.calculator import Calculator
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# 1. Instantiate tool classes
attractions = AttractionFinder()
weather = WeatherService()
hotels = HotelCalculator()
currency = CurrencyConverter()
itinerary = ItineraryBuilder()
summary = TripSummary()
calculator = Calculator()

# 2. Collect all @tool methods (NO itinerary, NO summary)
TOOLS = [
  attractions.find_attractions,
  weather.get_weather,
  hotels.search_hotels,
  currency.convert,
  calculator.add,
  calculator.multiply,
  calculator.divide,
  calculator.subtract
]

# 3. Get LLM and create react agent
llm = get_llm()
react_agent = create_react_agent(llm, tools=TOOLS)

# 4. Main block for CLI/manual test
# After agent run, call itinerary.build(...) and summary.generate_summary(...)
def main():
  print("Travel Agent REACT workflow. Type your query:")
  while True:
    user_input = input("You: ")
    if user_input.lower() in {"exit", "quit"}:
      break
    messages = [HumanMessage(content=user_input)]
    result = react_agent.invoke({"messages": messages})
    # Gathered info from tools (simulate, or extract from result as needed)
    # For demo, just use dummy data:
    trip_info = {
      "destination": "Paris",
      "days": 3,
      "attractions": [{"name": "Louvre"}, {"name": "Eiffel Tower"}],
      "hotel_info": {"name": "Hotel Paris"}
    }
    itinerary_result = itinerary.build(
      destination=trip_info["destination"],
      days=trip_info["days"],
      attractions=trip_info["attractions"],
      hotel_info=trip_info["hotel_info"]
    )
    print("\n--- Itinerary ---")
    print(itinerary_result["itinerary"])
    summary_result = summary.generate_summary(trip_info)
    print("\n--- Summary ---")
    print(summary_result["summary"])

if __name__ == "__main__":
  main()