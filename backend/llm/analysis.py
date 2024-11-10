# llm/analysis.py

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from utils.config import llm, store_long_term_characteristics_in_pinecone, search_events_near_place
from core.state import GraphState

def extract_characteristics(state: GraphState) -> GraphState:
    print("Currently, these are my " + state["long_term_characteristics"])
    # Initial greeting to the user
    print("Bot: Hello! I am here to assist you with trip planning. Tell me about your travel preferences, including the destination and length of your trip.")

    # Adjust the temperature for this specific function
    llm.temperature = 0.1

    system_prompt = """
        You are an AI that converses with a human to gather travel preferences. 
        Classify each preference as either 'long-term' or 'short-term.' 
        Long-term preferences are general or ongoing (e.g., 'I love hiking'), while short-term preferences are specific to the current context or trip (e.g., 'I'd like to go to Paris').
        Ensure that both a location ('place to visit') and a 'length of trip' (in days) are specified in the preferences before generating a trip.
        If either is missing, prompt the user to provide the missing information.
        """

    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{prompt}"),
        ]
    )

    while True:
        # Ask for user input
        user_input = input("You: ")
        state["input"] = user_input

        # Check if the user intends to generate the trip
        intent_check_prompt = chat_template.format_messages(
            prompt=f"Does the following input indicate the user wants to finalize and generate/plan the trip? Respond with yes or no. Input: '{user_input}'"
        )
        intent_response = llm.invoke(intent_check_prompt).content.strip().lower()

        # Process the input for new characteristics regardless of intent to generate a trip
        refine_prompt = chat_template.format_messages(
            prompt=f"Current Long-term Preferences: {state['long_term_characteristics']}\n"
                   f"Current Short-term Preferences: {state['short_term_characteristics']}\n"
                   f"New Input: {user_input}\n"
                   f"Update and classify the preferences as 'long-term' or 'short-term'. Respond ONLY with the updated preferences in the following strict format:\n\n"
                   f"Long-term: <list of updated long-term preferences>\n"
                   f"Short-term: <list of updated short-term preferences>\n\n"
                   f"Do not include any extra commentary or additional text."
        )

        ai_message = llm.invoke(refine_prompt)
        updated_preferences = ai_message.content.strip()

        # Split the updated preferences into long-term and short-term categories
        long_term, short_term = updated_preferences.split("Short-term:") if "Short-term:" in updated_preferences else (updated_preferences, "")
        short_term = "Short-term:" + short_term

        # Update the state with refined characteristics
        state["steps"].append("extract_characteristics")
        state["long_term_characteristics"] = long_term.strip()
        store_long_term_characteristics_in_pinecone(state["long_term_characteristics"])
        state["short_term_characteristics"] = short_term.strip()

        # Check if 'place to visit' and 'trip length' are included
        if "yes" in intent_response:
            location_check_prompt = chat_template.format_messages(
                prompt=f"Does the following input specify a place to visit? Respond with yes or no. Preferences: '{state['long_term_characteristics']} {state['short_term_characteristics']}'"
            )
            location_response = llm.invoke(location_check_prompt).content.strip().lower()

            length_check_prompt = chat_template.format_messages(
                prompt=f"Does the following input specify a length for the trip in days? Respond with yes or no. Preferences: '{state['long_term_characteristics']} {state['short_term_characteristics']}'"
            )
            length_response = llm.invoke(length_check_prompt).content.strip().lower()

            # Check if both location and length are specified
            if "yes" in location_response and "yes" in length_response:
                print("Bot: Got it! I’ll generate your trip plan now.")
                break
            elif "no" in location_response:
                print("Bot: It looks like you haven’t specified a destination yet. Could you let me know where you’d like to go?")
            elif "no" in length_response:
                print("Bot: I also need to know the length of your trip in days. How long would you like your trip to be?")

        # Generate dynamic feedback using the updated characteristics
        feedback_prompt = chat_template.format_messages(
            prompt=f"User Input: {user_input}\nUpdated Long-term Preferences: {state['long_term_characteristics']}\n"
                   f"Updated Short-term Preferences: {state['short_term_characteristics']}\n"
                   f"Generate a response acknowledging these preferences."
        )
        feedback_message = llm.invoke(feedback_prompt)
        response = feedback_message.content

        # Provide dynamic feedback to the user
        print(f"Bot: {response}")

    return state

def generate_trip(state: GraphState) -> GraphState:
    
    characteristics = state["long_term_characteristics"] + state["short_term_characteristics"]

    # Adjust the temperature for this specific function
    llm.temperature = 0.1

    system_prompt = """
        You are an AI that plans a trip based on a person's provided characteristics/preferences.
        """

    chat_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{prompt}"),
        ]
    )

    prompt = chat_template.format_messages(prompt=f"User Characteristcs/Preferences: {characteristics}\n")
    ai_message = llm.invoke(prompt)
    trip_plan = ai_message.content

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

def get_event_metadata(state: GraphState) -> GraphState:
    state["events_metadata"] = search_events_near_place(state["place_to_visit"])
    return state