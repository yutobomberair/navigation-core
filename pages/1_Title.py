import streamlit as st

from app_platform import ui
from app_platform.services import auth_service, goal_service

ui.inject_css()

st.title("🧭 Progress Navi")
st.write(
    "踏み出した一歩を、ゴールまで届ける"
)

user = auth_service.require_user()

if st.button("旅を始める"):
    goal = goal_service.get_active_goal(user.id)

    if goal:
        st.switch_page(
            "pages/4_Navigation.py"
        )
    else:
        st.switch_page(
            "pages/2_Onboarding.py"
        )
