import os
from services.llm_utils import get_llm, get_default_prompt
from typing import List, Dict, Any

class ItineraryBuilder:
    """
    Builds a day-by-day itinerary for a trip using an LLM.
    """
    def __init__(self):
        self.llm = get_llm()
        system_prompt = (
            "You are a travel assistant. Given a destination, number of days, a list of attractions, and hotel info, generate a detailed, day-by-day itinerary. Be specific, logical, and concise. Mention both the local and user's currency if possible. If any required info is missing, raise an error."
        )
        human_prompt = "Destination: {destination}\nDays: {days}\nAttractions: {attractions}\nHotel Info: {hotel_info}"
        self.prompt = get_default_prompt(system_prompt, human_prompt)

    def build(self, destination: str, days: int, attractions: list, hotel_info: dict) -> dict:
        """
        Generates a detailed, day-by-day itinerary using an LLM.

        Args:
            destination (str): The city or country for the trip.
            days (int): Number of days for the trip.
            attractions (list): List of attractions to include.
            hotel_info (dict): Information about the hotel.

        Returns:
            dict: Dictionary with the generated itinerary.
        """
        if not destination or not days or not attractions or not hotel_info:
            raise ValueError("Missing required trip information for itinerary generation.")
        chain = self.prompt | self.llm
        result = chain.invoke({
            "destination": destination,
            "days": days,
            "attractions": attractions,
            "hotel_info": hotel_info
        })
        return {"itinerary": result.content} 