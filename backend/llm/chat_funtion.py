# chat_function.py

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from utils.config import llm, store_long_term_characteristics_in_pinecone, search_events_near_place
from core.state import GraphState

def extract_characteristics(state: GraphState) -> GraphState:
    """
    Process user input to extract long-term and short-term travel preferences and update the state.
    """
    llm.temperature = 0.1

    # System prompt for gathering preferences
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

    user_input = state["input"]

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

        # Update state based on checks
        if "yes" in location_response and "yes" in length_response:
            state["trip_plan_ready"] = True  # Indicates readiness for trip generation
            state["feedback"] = "Now Creating a Personalized Plan for You"
            return state
        else:
            state["trip_plan_ready"] = False
            if "yes" not in location_response and "yes" not in length_response:
                state["feedback"] = "Please specify both the location and length of the trip, then ask to generate the trip again."
            elif "yes" in location_response:
                state["feedback"] = "Please specify the length of the trip, then ask to generate the trip again."
            else:
                state["feedback"] = "Please specify the location, then ask to generate the trip again."
    else:
        feedback_prompt = chat_template.format_messages(
            prompt=f"User Input: {user_input}\nUpdated Long-term Preferences: {state['long_term_characteristics']}\n"
                   f"Updated Short-term Preferences: {state['short_term_characteristics']}\n"
                   f"Generate a response acknowledging these preferences."
        )

        feedback_message = llm.invoke(feedback_prompt)
        state["feedback"] = feedback_message.content.strip()  # Store feedback in the state for frontend display
    
    return state
