# core/state.py

from typing import List
from typing_extensions import TypedDict

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        input: User's most recent input
        long_term_characteristics: Persistent preferences
        short_term_characteristics: Temporary or context-specific preferences
        place_to_visit: Destination for the trip
        trip_length_days: Duration of the trip in days
        real_time_context: Context such as weather or other real-time info
        events_metadata: List of additional event descriptions
        trip_plan_ready: Indicates if it's time to generate the trip plan
        trip_plan: Final trip plan based on the characteristics
        feedback: Dynamic feedback message for the user
        steps: List of steps executed in the workflow
        longitude: Longitude of the destination
        latitude: Latitude of the destination
    """
    input: str
    long_term_characteristics: str
    short_term_characteristics: str
    place_to_visit: str
    trip_length_days: str
    real_time_context: str
    events_metadata: List[str]
    trip_plan_ready: bool
    trip_plan: str
    feedback: str
    steps: List[str]
    longitude: float
    latitude: float


