import requests
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Yelp Fusion API credentials
YELP_API_KEY = os.getenv('YELP_API_KEY')
HEADERS = {'Authorization': f'Bearer {YELP_API_KEY}'}

def get_top_places(location, term="top places to visit", limit=50):
    url = 'https://api.yelp.com/v3/businesses/search'
    params = {
        'location': location,
        'term': term,
        'sort_by': 'rating',
        'limit': limit
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()  # Check for HTTP errors
        businesses = response.json().get('businesses', [])
        
        # Collect data on each place
        top_places = []
        for business in businesses:
            business_data = {
                "name": business['name'],
                "rating": business['rating'],
                "address": ", ".join(business['location']['display_address']),
                "category": ", ".join([category['title'] for category in business['categories']]),
                "review_count": business['review_count'],
                "url": business['url'],
                "id": business['id']
            }
            # Get the top 3 reviews for the business
            # reviews = get_top_reviews(business['id'])
            # business_data.update(reviews)
            top_places.append(business_data)
        
        return top_places
    except requests.exceptions.RequestException as e:
        print("Error fetching top places:", e)
        return []

def get_top_reviews(business_id):
    url = f'https://api.yelp.com/v3/businesses/{business_id}/reviews'
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        reviews_data = response.json().get('reviews', [])
        
        # Prepare the top 3 reviews as a dictionary
        reviews = {}
        for idx, review in enumerate(reviews_data[:3], 1):
            reviews[f"review_{idx}_text"] = review['text']
            reviews[f"review_{idx}_rating"] = review['rating']
            reviews[f"review_{idx}_user"] = review['user']['name']
            reviews[f"review_{idx}_date"] = review['time_created']
        
        return reviews
    except requests.exceptions.RequestException as e:
        print(f"Error fetching reviews for {business_id}:", e)
        return {}

def save_to_csv(top_places, filename="yelp_top_places_ny.csv"):
    # Define column headers
    headers = [
        "name", "rating", "address", "category", "review_count", "url", "id"
    ]
    #     "review_1_text", "review_1_rating", "review_1_user", "review_1_date",
    #     "review_2_text", "review_2_rating", "review_2_user", "review_2_date",
    #     "review_3_text", "review_3_rating", "review_3_user", "review_3_date"
    # ]

    # Write data to CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for place in top_places:
            writer.writerow(place)
    
    print(f"Data saved to {filename}")

# Main function to fetch and save data
def main(location):
    top_places = get_top_places(location)
    if top_places:
        save_to_csv(top_places)

# Example usage
# location = 'Los Angeles, CA'
location = 'New York, NY'
main(location)
