import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from langchain.tools import tool

class HotelCalculator:
    """
    Finds hotels and calculates costs using the Booking.com API via RapidAPI.
    """
    SEARCH_URL = "https://booking-com18.p.rapidapi.com/v1/hotels/search"
    LOCATION_URL = "https://booking-com18.p.rapidapi.com/v1/hotels/locations"

    @staticmethod
    @tool
    def search_hotels(destination: str, days: str, group_size: str, accommodation_type: Optional[str]) -> List[Dict[str, Any]]:
        """
        Finds hotels using the Booking.com API.

        Args:
            destination (str): The city or location to search hotels in.
            days (str): Number of days to stay.
            group_size (str): Number of people in the group.
            accommodation_type (Optional[str]): Type of accommodation (e.g., hotel, hostel).

        Returns:
            List[Dict[str, Any]]: A list of hotel options, each as a dictionary with name, rating, cost, currency, and url.
        """
        api_key = os.getenv("RAPIDAPI_KEY")
        if not api_key:
            raise ValueError("RAPIDAPI_KEY not set. Hotel calculator cannot function.")
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }
        try:
            num_days = int(days)
            num_adults = int(group_size)
        except (ValueError, TypeError):
            num_days = 1
            num_adults = 1
        checkin_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        checkout_date = (datetime.now() + timedelta(days=1 + num_days)).strftime("%Y-%m-%d")
        location_data = HotelCalculator._get_location_data(destination, headers)
        if not location_data:
            raise HTTPException(status_code=404, detail=f"Could not find location data for {destination}.")
        params = {
            "dest_id": location_data["dest_id"],
            "dest_type": location_data["dest_type"],
            "checkin_date": checkin_date,
            "checkout_date": checkout_date,
            "adults_number": num_adults,
            "order_by": "popularity",
            "units": "metric",
            "room_number": '1',
            "filter_by_currency": "USD",
            "locale": "en-gb",
            "page_number": '0',
            "include_adjacency": 'true'
        }
        if accommodation_type and accommodation_type.lower() in ['hotel', 'hostel', 'resort', 'villa', 'apartment']:
            params["hotel_type"] = accommodation_type.lower()
        response = requests.get(HotelCalculator.SEARCH_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return HotelCalculator._process_hotels(response.json())

    @staticmethod
    def _get_location_data(destination: str, headers: dict) -> Optional[Dict[str, str]]:
        params = {"query": destination}
        response = requests.get("https://booking-com18.p.rapidapi.com/stays/auto-complete", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and "data" in data and len(data["data"]) > 0:
            first_result = data["data"][0]
            return {"dest_id": first_result["dest_id"], "dest_type": first_result["dest_type"]}
        return None

    @staticmethod
    def _process_hotels(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        hotels = []
        results = data.get("result", [])
        if not results:
            return []
        for hotel_data in results[:5]:
            price_info = hotel_data.get("composite_price_breakdown", {})
            gross_amount = price_info.get("gross_amount", {}).get("value")
            if gross_amount:
                hotels.append({
                    "name": hotel_data.get("hotel_name"),
                    "rating": hotel_data.get("review_score"),
                    "total_cost": gross_amount,
                    "currency": hotel_data.get("currency_code", "USD"),
                    "url": hotel_data.get("url")
                })
        if not hotels:
            raise HTTPException(status_code=404, detail="No hotels with available prices found.")
        return hotels 