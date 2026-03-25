# db/client.py
import os
from supabase import create_client
from dotenv import load_dotenv

# Exact path to .env
load_dotenv(r"C:\Project-Demografy\Neighbourhood_Livability\.env")

def get_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY in your .env file!")

    return create_client(url, key)