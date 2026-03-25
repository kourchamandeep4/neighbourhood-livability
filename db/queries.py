# db/queries.py
# This file talks to our Supabase database
# Main job: check if a suburb already exists (cache check)

from db.client import get_client

# All 14 categories we track
CATEGORIES = [
    "cafes", "parks", "gyms", "childcare", "transport",
    "healthcare", "grocery", "schools", "restaurants",
    "banks_atms", "entertainment", "pet_friendly",
    "libraries", "car_washes"
]

def check_suburb_in_db(suburb_name):
    """
    Checks if ALL 14 categories for this suburb
    are already saved in our database.

    Returns True  → we have the data (cache HIT  ✅)
    Returns False → we need to call Google API (cache MISS ❌)
    """
    # Connect to Supabase
    client = get_client()

    # Ask the database: do we have rows for this suburb?
    result = (
        client.table("raw_places")
        .select("category")
        .eq("suburb_name", suburb_name)
        .execute()
    )

    # Get which categories we already have
    categories_in_db = {row["category"] for row in result.data}

    # Check if we have ALL 14 categories
    all_present = categories_in_db >= set(CATEGORIES)

    return all_present


def get_suburb_metrics(suburb_name):
    """
    Gets the final clean scores for a suburb
    from the suburb_metrics table.
    Returns the data or None if not found.
    """
    client = get_client()

    result = (
        client.table("suburb_metrics")
        .select("*")
        .eq("suburb_name", suburb_name)
        .limit(1)
        .execute()
    )

    # Return first row if found, otherwise None
    return result.data[0] if result.data else None