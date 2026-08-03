import streamlit as st


def get_secret(key: str) -> str:
    value = st.secrets.get(key)
    if not value:
        raise RuntimeError(
            f"Missing secret '{key}'. Set it in .streamlit/secrets.toml "
            "(local) or the app's Secrets settings (Streamlit Cloud)."
        )
    return value


SUPABASE_URL = "SUPABASE_URL"
SUPABASE_KEY = "SUPABASE_KEY"
OPENAI_API_KEY = "OPENAI_API_KEY"
LINE_CHANNEL_ACCESS_TOKEN = "LINE_CHANNEL_ACCESS_TOKEN"

# Not a secret (LINE's add-friend URLs are meant to be shared publicly) —
# a plain constant rather than routed through get_secret().
LINE_ADD_FRIEND_URL = "https://line.me/R/ti/p/@150picqb"
