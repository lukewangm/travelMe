# utils/config.py

import pinecone
from langchain_openai import AzureChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

model_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')
api_version = os.getenv('AZURE_OPENAI_API_VERSION')
embedding_endpoint = os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT')
tavily_key = os.getenv('TAVILY_API_KEY')

# Azure OpenAI LLM Configuration
llm = AzureChatOpenAI(
    api_key=api_key,
    openai_api_version=api_version,
    azure_deployment=model_name,
    temperature=0.1,  # Default temperature, can be changed later
)

# Pinecone Configuration
pc = pinecone.Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Tavily Search Tool Configuration
tavily = TavilySearchResults(
    api_key=tavily_key,
    max_results=2,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
)

# Check if the Pinecone index exists or create it

def get_azure_openai_embedding(text):
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key,
    }
    data = {
        "input": text
    }
    
    response = requests.post(embedding_endpoint, headers=headers, json=data)
    response.raise_for_status()
    embeddings = response.json()['data'][0]['embedding']
    return embeddings

def store_long_term_characteristics_in_pinecone(characteristics_text):
    embedding = get_azure_openai_embedding(characteristics_text)
    index_name = "user-information"
    if index_name not in [idx.name for idx in pc.list_indexes().indexes]:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=pinecone.ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
    index = pc.Index(index_name)

    upsert_data = [("user_long_term_characteristics", embedding, {'text': characteristics_text})]
    index.upsert(upsert_data)
    print("Long-term characteristics successfully stored in Pinecone.")


def fetch_long_term_characteristics_from_pinecone():
    index_name = "user-information"
    if index_name not in [idx.name for idx in pc.list_indexes().indexes]:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=pinecone.ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
    index = pc.Index(index_name)
    response = index.fetch(["user_long_term_characteristics"])
    
    # Retrieve and return only the text if it's available
    if response and "user_long_term_characteristics" in response['vectors']:
        return response['vectors']["user_long_term_characteristics"]['metadata'].get('text', "")
    
    return ""

def search_events_near_place(place_to_visit):
    """
    Performs a vector similarity search in Pinecone to find events or related content near the specified place.
    Returns a list of event descriptions (as strings) from the metadata.
    """
    if not place_to_visit:
        print("No place to visit specified.")
        return []

    # Generate query embedding
    query_text = f"Details for events around {place_to_visit}"
    query_embedding = get_azure_openai_embedding(query_text)

    # Initialize Pinecone and define the index name
    index_name = "trip-planner-context"
    if index_name not in [idx.name for idx in pc.list_indexes().indexes]:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric='cosine',
            spec=pinecone.ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
    # Connect to the Pinecone index
    index = pc.Index(index_name)

    # Perform the similarity search
    search_results = index.query(
        vector=query_embedding,
        top_k=5,  # Adjust the number of results as needed
        include_metadata=True
    )

    # Extract and return only the "text" field from each match's metadata
    event_descriptions = [match["metadata"].get("text", "No description available.") for match in search_results["matches"]]
    return event_descriptions

