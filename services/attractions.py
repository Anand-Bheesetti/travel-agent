import os
import requests
from typing import List, Dict, Any
from langchain.tools import tool

class AttractionFinder:
    """
    Finds attractions and activities using the Geoapify Places API.
    """
    API_URL = "https://api.geoapify.com/v2/places"
    GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

    @staticmethod
    @tool
    def find_attractions(destination: str, activity_preferences: List[str]) -> List[Dict[str, Any]]:
        """
        Finds attractions for a given destination and preferences.

        Args:
            destination (str): The city or country to search for attractions.
            activity_preferences (List[str]): List of activity types (e.g., 'culture', 'art').

        Returns:
            List[Dict[str, Any]]: A list of attractions, each as a dictionary with name, address, and category.
        """
        api_key = os.getenv("GEOAPIFY_API_KEY")
        if not api_key:
            raise ValueError("GEOAPIFY_API_KEY not set. Attraction finder cannot function.")
        coords = AttractionFinder._get_coordinates(destination, api_key)
        if not coords:
            raise ValueError(f"Could not find coordinates for {destination}.")
        categories = AttractionFinder._map_preferences_to_categories(activity_preferences)
        params = {
            "categories": ",".join(categories),
            "filter": f"circle:{coords['lon']},{coords['lat']},5000",
            "limit": 10,
            "apiKey": api_key
        }
        response = requests.get(AttractionFinder.API_URL, params=params, timeout=10)
        response.raise_for_status()
        return AttractionFinder._process_attractions(response.json())

    @staticmethod
    def _get_coordinates(destination: str, api_key: str) -> Dict[str, float] | None:
        """Helper to get the coordinates for a destination."""
        params = {"text": destination, "apiKey": api_key, "limit": 1}
        response = requests.get(AttractionFinder.GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("features"):
            props = data["features"][0]["properties"]
            return {"lat": props["lat"], "lon": props["lon"]}
        return None

    @staticmethod
    def _map_preferences_to_categories(preferences: List[str]) -> List[str]:
        """Maps user's high-level preferences to specific Geoapify categories."""
        category_map = {
            "culture": ["entertainment.culture.theatre", "entertainment.culture.arts_centre", "entertainment.culture.gallery"],
            "adventure": ["natural.forest", "natural.mountain.peak", "entertainment.theme_park"],
            "relaxation": ["leisure.park", "leisure.spa"],
            "nightlife": ["catering.bar", "adult.nightclub"],
            "history": ["heritage.unesco", "tourism.sights.castle", "tourism.sights.archaeological_site", "tourism.sights.monastery"],
            "art": ["entertainment.culture.gallery"]
        }
        # Default to tourism.attraction if no preferences match
        if not preferences:
            return ["tourism.attraction"]

        selected_categories = set()
        for pref in preferences:
            selected_categories.update(category_map.get(pref.lower(), []))
        
        return list(selected_categories) if selected_categories else ["tourism.attraction"]

    @staticmethod
    def _process_attractions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processes the raw API response into a clean list of attractions."""
        attractions = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            attractions.append({
                "name": props.get("name"),
                "address": props.get("formatted"),
                "category": props.get("categories")[0] if props.get("categories") else "unknown"
            })
        return attractions 