from typing import List, Optional

from pydantic import BaseModel, Field


class TripPlan(BaseModel):
  """Data model for the user's trip plan."""
  destination: str = Field(None, description="Destination city/country")
  budget: float = Field(None, description="Budget for the trip")
  native_currency: str = Field(None, description="User's native currency")
  days: int = Field(None, description="Duration of the trip in days")
  group_size: int = Field(1, description="Number of people traveling")
  activity_preferences: Optional[List[str]] = Field(
    None, description="Preferences like adventure, culture, relaxation"
  )
  accommodation_type: Optional[str] = Field(
    None, description="Preferred accommodation type (e.g., hotel, hostel, airbnb)"
  )
  dietary_restrictions: Optional[List[str]] = Field(
    None, description="Any dietary restrictions"
  )
  transportation_preferences: Optional[List[str]] = Field(
    None, description="Preferred mode of transport"
  ) #<TripPlan>


class QueryAnalysisResult(TripPlan):
  """Data model for the output of the QueryAnalyzer."""
  missing_fields: List[str] = Field(
    default_factory=list, # default_factory=list ensures that a new list is created for each instance, avoiding shared state
    description="List of required fields that are missing from the user query",
  ) #<QueryAnalysisResult>

# default_factory=list means that if missing_fields is not provided
# when creating a QueryAnalysisResult, it will default to [] (a new, empty list).
# This avoids potential issues with all instances sharing the same list.
#<eof>