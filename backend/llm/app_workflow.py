# llm/app_workflow.py

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from utils.config import llm, store_long_term_characteristics_in_pinecone, search_events_near_place
from core.state import GraphState


def generate_trip(state: GraphState) -> GraphState:
    """
    Generate a personalized trip plan based on user characteristics, real-time context, and additional context.
    """
    # Combine characteristics and additional context from state
    characteristics = state["long_term_characteristics"] + state["short_term_characteristics"]
    real_time_context = state.get("real_time_context", "")
    additional_context = "\n".join(state.get("events_metadata", []))  # Join list of strings into a single context string

    # Set the LLM's temperature for controlled output consistency
    llm.temperature = 0.1

    # Define the system prompt
    system_prompt = """
        You are an AI that generates a personalized trip plan.
        You will be provided with:
        - User characteristics/preferences to shape the trip's style.
        - Current or real-time details (e.g., weather) to help with accurate recommendations.
        - Additional contextual information to enhance the trip suggestions; you are not strictly bound to only use it or use all of it. You are encouraged to also do your own research.
        Please generate a trip plan that considers the user's chosen/preferred location, time frame, and any provided details.
    """

    # Format the prompt with the provided state information
    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{prompt}"),
        ]
    )

    prompt = chat_template.format_messages(
        prompt=(
            f"User Characteristics/Preferences: {characteristics}\n"
            f"Real-Time Context: {real_time_context}\n"
            f"Additional Context:\n{additional_context}\n"
            "Please create a personalized trip plan based on this information."
        )
    )
    
    # Invoke the language model to generate the trip plan
    ai_message = llm.invoke(prompt)
    trip_plan = ai_message.content

    # Update the state with the generated trip plan
    state["steps"].append("generate_trip")
    state["trip_plan"] = trip_plan
    
    return state


def parse_trip_details(state: GraphState) -> GraphState:
    """
    Extract the place to visit and length of trip from the given long-term and short-term characteristics
    using GPT, and generate latitude and longitude coordinates for the destination.
    Updates state with 'place_to_visit', 'trip_length_days', 'latitude', and 'longitude'.
    """
    llm_temperature = 0.1  # Adjust for better consistency in extraction

    system_prompt = """
        You are an AI that extracts travel destination and trip length from given user preferences.
        Extract the place they want to visit and the length of the trip in days from the provided preferences.
        Respond ONLY with the destination (place name) and the number of days.
    """

    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{prompt}"),
        ]
    )

    # Prepare input for GPT call
    long_term = state["long_term_characteristics"]
    short_term = state["short_term_characteristics"]

    parse_prompt = chat_template.format_messages(
        prompt=f"Long-term Preferences: {long_term}\nShort-term Preferences: {short_term}\n"
               f"Extract and provide only:\n"
               f"Place to Visit: <destination>\n"
               f"Trip Length in Days: <number>"
    )

    # Use GPT to extract trip details
    response = llm.invoke(parse_prompt)
    response_content = response.content.strip()

    # Parse GPT response
    try:
        place_to_visit = response_content.split("Place to Visit:")[1].split("Trip Length in Days:")[0].strip()
        trip_length_days = response_content.split("Trip Length in Days:")[1].strip()
    except (IndexError, ValueError):
        print("Error extracting place to visit or trip length from response.")
        return

    # Update state with extracted values
    state["place_to_visit"] = place_to_visit
    state["trip_length_days"] = trip_length_days

    print(f"Place to Visit: {state['place_to_visit']}")
    print(f"Trip Length in Days: {state['trip_length_days']}")

    # Generate coordinates using GPT with strict format specification
    coord_prompt = f"Provide the approximate latitude and longitude for the location: {place_to_visit}. Respond ONLY in the format:\nLatitude: <latitude_value>\nLongitude: <longitude_value>."
    coord_response = llm.invoke(coord_prompt).content.strip()

    # Parse the coordinates from the GPT response
    try:
        latitude = coord_response.split("Latitude:")[1].split("Longitude:")[0].strip()
        longitude = coord_response.split("Longitude:")[1].strip()
        state["latitude"] = float(latitude)
        state["longitude"] = float(longitude)
        print(f"Latitude: {state['latitude']}, Longitude: {state['longitude']}")
    except (ValueError, IndexError):
        print("Error extracting coordinates from GPT response.")

def get_real_time_context(state: GraphState) -> GraphState:
    return state

def get_event_details(state: GraphState) -> GraphState:
    # state["events_metadata"] = search_events_near_place(state["place_to_visit"])
    return state