import streamlit as st
from supabase import Client, create_client

from app_platform.config import SUPABASE_KEY, SUPABASE_URL, get_secret


@st.cache_resource
def get_client() -> Client:
    return create_client(get_secret(SUPABASE_URL), get_secret(SUPABASE_KEY))
