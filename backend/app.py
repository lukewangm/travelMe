# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.config import fetch_long_term_characteristics_from_pinecone
from llm.chat_funtion import extract_characteristics
from llm.app_workflow import generate_trip, parse_trip_details, get_event_details
from core.state import GraphState
from langgraph.graph import StateGraph, START, END

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Initialize the workflow only once
workflow = StateGraph(GraphState)
workflow.add_node("get_event_details", get_event_details)
workflow.add_node("generate_trip", generate_trip)

workflow.add_edge(START, "get_event_details")
workflow.add_edge("get_event_details", "generate_trip")
workflow.add_edge("generate_trip", END)

custom_graph = workflow.compile()  # Compiled workflow ready for use

def create_initial_state():
    """
    Helper function to create and return a new initial state.
    """
    lc = fetch_long_term_characteristics_from_pinecone()
    return GraphState(
        input="",
        long_term_characteristics=lc,
        short_term_characteristics="",
        steps=[],
        place_to_visit="",
        trip_length_days="",
        trip_plan="",
        longitude=0.0,
        latitude=0.0,
        events_metadata=[],
        feedback="",
        real_time_context="",
        trip_plan_ready=False
    )

@app.route("/api/create_initial_state", methods=["GET"])
def create_initial_state_endpoint():
    """
    Endpoint to create and return a new initial state.
    """
    initial_state = create_initial_state()
    return jsonify({"state": initial_state}), 200


@app.route("/api/process_input", methods=["POST"])
def process_input():
    """
    Endpoint to process user input until the trip plan is ready. Called in a while loop and breaks when the plan is ready.
    """
    # Retrieve the input text and existing state from the request
    data = request.get_json()
    user_input = data.get("user_input")
    state = data.get("state")

    if not user_input:
        return jsonify({"error": "User input is required"}), 400
    if not state:
        return jsonify({"error": "State is required"}), 400

    # Update the state with user input and process it
    state["input"] = user_input
    state = extract_characteristics(state)

    # Check if the trip plan is ready and call `parse_trip_details` if true
    if state.get("trip_plan_ready", False):
        state = parse_trip_details(state)

    # Prepare the response data with the updated state
    response_data = {
        "state": state,
        "trip_plan_ready": state.get("trip_plan_ready", False),
        "feedback": state["feedback"]
    }

    return jsonify(response_data), 200



@app.route("/api/generate_trip", methods=["POST"])
def generate_trip_plan():
    """
    Endpoint to execute the workflow for generating the trip plan once `trip_plan_ready` is True.
    """
    # Retrieve the state from the request
    data = request.get_json()
    state = data.get("state")

    if not state or not state.get("trip_plan_ready"):
        return jsonify({"error": "Trip plan is not ready. Complete input in /api/process_input first."}), 400

    # Run the workflow using the existing custom_graph
    output = custom_graph.invoke(state)

    # Prepare the response with the completed trip plan
    response_data = {
        "state": output,
        "trip_plan": output["trip_plan"]
    }

    return jsonify(response_data), 200

if __name__ == "__main__":
    app.run(debug=True)
