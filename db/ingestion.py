# db/ingestion.py
import sys
import os
from dotenv import load_dotenv

load_dotenv(r"C:\Project-Demografy\Neighbourhood_Livability\.env")
sys.path.insert(0, r"C:\Project-Demografy\Neighbourhood_Livability")

from db.client import get_client
from db.google_api import fetch_all_categories
from db.queries import check_suburb_in_db


def save_raw_places(suburb_name, category, places):
    client = get_client()
    client.table("raw_places").insert({
        "suburb_name":  suburb_name,
        "category":     category,
        "api_response": places,
        "place_count":  len(places),
    }).execute()


def compute_and_save_metrics(suburb_name):
    client = get_client()

    result = (
        client.table("raw_places")
        .select("category, place_count")
        .eq("suburb_name", suburb_name)
        .execute()
    )

    metrics = {
        "suburb_name":     suburb_name,
        "cafes":           0,
        "parks":           0,
        "gyms":            0,
        "childcare":       0,
        "transport_stops": 0,
        "healthcare":      0,
        "grocery":         0,
        "schools":         0,
        "restaurants":     0,
        "banks_atms":      0,
        "entertainment":   0,
        "pet_friendly":    0,
        "libraries":       0,
        "car_washes":      0,
    }

    for row in result.data:
        cat   = row["category"]
        count = row["place_count"] or 0
        if cat == "transport":
            metrics["transport_stops"] = count
        elif cat in metrics:
            metrics[cat] = count

    client.table("suburb_metrics").upsert(
        metrics,
        on_conflict="suburb_name"
    ).execute()

    return metrics


def run_pipeline(suburb_name, progress_callback=None, radius_km=2):
    suburb_clean = suburb_name.strip().title()

    # Step 1 — Cache check
    if progress_callback:
        progress_callback(10, "Checking database...")

    already_exists = check_suburb_in_db(suburb_clean)

    if already_exists:
        # Cache HIT — load from DB, skip Google
        if progress_callback:
            progress_callback(70, "Found in database! Loading...")

        client = get_client()
        result = (
            client.table("suburb_metrics")
            .select("*")
            .eq("suburb_name", suburb_clean)
            .limit(1)
            .execute()
        )

        if progress_callback:
            progress_callback(100, "Done!")

        return result.data[0] if result.data else None

    # Step 2 — Cache MISS, call Google
    if progress_callback:
        progress_callback(20, f"Fetching from Google ({radius_km}km radius)...")

    all_places, lat, lng = fetch_all_categories(suburb_clean, radius_km)

    # Step 3 — Save raw data
    if progress_callback:
        progress_callback(60, "Saving to database...")

    for category, places in all_places.items():
        save_raw_places(suburb_clean, category, places)

    # Step 4 — Compute metrics
    if progress_callback:
        progress_callback(80, "Computing livability scores...")

    metrics = compute_and_save_metrics(suburb_clean)

    if progress_callback:
        progress_callback(100, "Done!")

    return metrics


