import streamlit as st

from app_platform.services import auth_service

st.set_page_config(
    page_title="Progress Navi",
    page_icon="🧭"
)

# Must run before switch_page: st.switch_page drops query params, so the
# ?u= code has to be captured into session_state here, on the very first
# script run, while it's still readable from the real browser URL.
auth_service.require_user()

st.switch_page("pages/1_Title.py")
