# db/google_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv(r"C:\Project-Demografy\Neighbourhood_Livability\.env")

CATEGORY_SEARCHES = {
    "cafes":         "cafes and coffee shops",
    "parks":         "parks and gardens",
    "gyms":          "gyms and fitness centres",
    "childcare":     "childcare and preschools",
    "transport":     "train stations and bus stops",
    "healthcare":    "hospitals clinics and pharmacies",
    "grocery":       "supermarkets and grocery stores",
    "schools":       "primary schools and high schools",
    "restaurants":   "restaurants and dining",
    "banks_atms":    "banks and ATMs",
    "entertainment": "cinemas theatres and entertainment",
    "pet_friendly":  "vets and dog parks",
    "libraries":     "libraries and community centres",
    "car_washes":    "car wash",
}

def get_api_key():
    """Gets Google API key from Streamlit secrets or .env"""
    try:
        import streamlit as st
        key = st.secrets.get("GOOGLE_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GOOGLE_API_KEY")


def get_suburb_coordinates(suburb_name):
    """
    Uses Google Geocoding API to get
    exact lat/lng centre of a suburb.
    """
    api_key = get_api_key()

    if not api_key:
        raise Exception("Missing GOOGLE_API_KEY!")

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": f"{suburb_name} Australia",
        "key": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data["status"] != "OK":
        raise Exception(f"Could not find suburb: {suburb_name}")

    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def fetch_places_for_category(suburb_name, category, lat, lng, radius_km=2):
    """
    Searches for one category within
    radius_km of the suburb centre.
    """
    api_key = get_api_key()

    if not api_key:
        raise Exception("Missing GOOGLE_API_KEY!")

    search_term = CATEGORY_SEARCHES[category]
    query = f"{search_term} in {suburb_name} Australia"

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type":     "application/json",
        "X-Goog-Api-Key":   api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
    }

    body = {
        "textQuery": query,
        "maxResultCount": 20,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude":  lat,
                    "longitude": lng
                },
                "radius": radius_km * 1000
            }
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(
            f"Google API error: {response.status_code} - {response.text}"
        )

    data = response.json()
    places = data.get("places", [])
    return places


def fetch_all_categories(suburb_name, radius_km=2):
    """
    Fetches all 14 categories for a suburb
    within the given radius.
    """
    print(f"Finding coordinates for {suburb_name}...")
    lat, lng = get_suburb_coordinates(suburb_name)
    print(f"Found: lat={lat}, lng={lng}")

    results = {}

    for category in CATEGORY_SEARCHES.keys():
        print(f"Fetching {category} within {radius_km}km...")
        try:
            places = fetch_places_for_category(
                suburb_name, category, lat, lng, radius_km
            )
            results[category] = places
            print(f"Found {len(places)} {category}")
        except Exception as e:
            print(f"Error fetching {category}: {e}")
            results[category] = []

    return results, lat, lng
