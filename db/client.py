# db/client.py
import os
from supabase import create_client
from dotenv import load_dotenv

# Try loading .env for local development
load_dotenv(r"C:\Project-Demografy\Neighbourhood_Livability\.env")

def get_client():
    # Try Streamlit secrets first (cloud)
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        url = None
        key = None

    # Fall back to .env (local)
    if not url or not key:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY!")

    return create_client(url, key)