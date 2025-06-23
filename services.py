from models import QueryAnalysisResult


class QueryAnalyzer:
  def analyze(self, user_query: str) -> QueryAnalysisResult:
    """
    Parses the user query to extract trip details and identify missing information.
    """
    print("Analyzing query...")
    # This will use an LLM with function calling to populate QueryAnalysisResult
    # For now, returning a dummy object.
    return QueryAnalysisResult(
      destination="Paris", missing_fields=["days", "budget", "native_currency"]
    )


class WeatherService:
  def get_weather(self, destination: str, days: int):
    """
    Fetches the weather forecast for the destination.
    """
    print(f"Getting weather for {destination} for {days} days...")
    return {"forecast": "Sunny with a chance of clouds."}


class AttractionFinder:
  def find_attractions(self, destination: str, activity_preferences: list):
    """
    Finds attractions and activities based on user preferences.
    """
    print(
      f"Finding attractions in {destination} for preferences: {activity_preferences}"
    )
    return [{"name": "Eiffel Tower"}, {"name": "Louvre Museum"}]


class HotelCalculator:
  def calculate_cost(
    self, destination: str, days: int, accommodation_type: str, group_size: int
  ):
    """
    Calculates the estimated hotel cost.
    """
    print(f"Calculating hotel cost in {destination} for {days} days.")
    return {"estimated_cost": 500.00, "currency": "USD"}


class CurrencyConverter:
  def convert(self, amount: float, from_currency: str, to_currency: str):
    """
    Converts currency.
    """
    print(f"Converting {amount} from {from_currency} to {to_currency}")
    return {"converted_amount": amount * 0.9, "target_currency": to_currency}


class ItineraryBuilder:
  def build(self, destination: str, days: int, attractions: list, hotel_info: dict):
    """
    Generates a day-by-day itinerary.
    """
    print(f"Building itinerary for {destination} for {days} days.")
    return {"itinerary": "Day 1: Visit Eiffel Tower. Day 2: Visit Louvre."}


class TripSummary:
  def generate_summary(self, trip_plan: dict):
    """
    Generates a final summary of the trip plan.
    """
    print("Generating trip summary...")
    return "This is your amazing trip plan to Paris!"


class Calculator:
  def add(self, a: float, b: float) -> float:
    """Adds two numbers."""
    return a + b

  def multiply(self, a: float, b: float) -> float:
    """Multiplies two numbers."""
    return a * b

  def divide(self, a: float, b: float) -> float:
    """Divides two numbers, handles division by zero."""
    if b == 0:
      raise ValueError("Cannot divide by zero.")
    return a / b 