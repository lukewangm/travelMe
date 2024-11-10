#main.py

from utils.config import llm, pc, tavily, fetch_long_term_characteristics_from_pinecone  # Import the configured objects
from llm.analysis import extract_characteristics, generate_trip, parse_trip_details
from core.state import GraphState
from langgraph.graph import StateGraph, START, END

import os
import time

# Start the timer
start_time = time.time()

lc = fetch_long_term_characteristics_from_pinecone()

# Initialize the state
initial_state = GraphState(
    input = "",
    long_term_characteristics = lc,
    short_term_characteristics = "",
    steps=[]
)

# Create the StateGraph
workflow = StateGraph(GraphState)

# Add the nodes (functions)
workflow.add_node("extract_characteristics", extract_characteristics)
workflow.add_node("parse_trip_details", parse_trip_details)
workflow.add_node("generate_trip", generate_trip)

# Define the edges
workflow.add_edge(START, "extract_characteristics")
workflow.add_edge("extract_characteristics", "parse_trip_details")
workflow.add_edge("parse_trip_details", "generate_trip")
workflow.add_edge("generate_trip", END)

# Compile the workflow
custom_graph = workflow.compile()

# Stream the workflow
output = custom_graph.invoke(initial_state)

# Calculate and print elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time:.2f} seconds")

# Print the proactive report
print("long")
print(output["long_term_characteristics"])
print("short")
print(output["short_term_characteristics"])
print("plan")
print(output["trip_plan"])

print("Finished")
