import requests
import glob
import pandas as pd
# import json
from transformers import AutoTokenizer, AutoModel
import torch
import pinecone
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Change pinecone API key to Will's in .env file
load_dotenv()

# Initialize Pinecone connection
pc = pinecone.Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

model_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')
api_version = os.getenv('AZURE_OPENAI_API_VERSION')
embedding_endpoint = os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT')

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
  index_name = "user-information"   # Change?
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

def embed_text(text, tokenizer, model):
   inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
   with torch.no_grad():
       embeddings = model(**inputs).last_hidden_state.mean(dim=1)
   return embeddings[0].numpy()

def main():
  # Load the data from the CSV files
  # Inspo: https://learn.microsoft.com/en-us/azure/ai-services/openai/tutorials/embeddings?tabs=python-new%2Ccommand-line&pivots=programming-language-python
  data_files = glob.glob("top_places_data/*.csv")
  all_top_places = pd.concat(
    [pd.read_csv(data_files[0])] +
    [pd.read_csv(file, header=None) for file in data_files[1:]],
    ignore_index=True
  )

  #### EMBEDDING AND STORAGE INTO VECTOR DATABASE CODE
  tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
  model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

  all_top_places['json'] = all_top_places.apply(lambda x: x.to_json(), axis=1)

  for idx, row in all_top_places.iterrows():
    # Embed the description of the place
    # text = f"{row['name']} - {row['category']} - {row['address']} - {row['url']} - {row['rating']} - Top review count: {row['review_count']}"
    # embedding = model.encoder(text).tolist()
    
    embedding = get_azure_openai_embedding(row['json'])

    metadata = {
      'name': row['name'],
      'rating': row['rating'],
      'address': row['address'],
      'category': row['category'],
      'review_count': row['review_count'],
      'url': row['url']
    }

    # Store the embedding in Pinecone
    index_name = "top-places" # Change?
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

    upsert_data = [(row["id"], embedding, metadata)]
    index.upsert(upsert_data)

  print("Embeddings and descriptions successfully stored in Pinecone!")

if __name__ == "__main__":
  main()