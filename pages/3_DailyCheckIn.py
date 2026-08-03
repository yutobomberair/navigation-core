from datetime import date

import streamlit as st

from app_platform import ui
from app_platform.services import auth_service, checkin_service, goal_service

st.title("📱 Daily Check-in")
ui.inject_css()

user = auth_service.require_user()
goal = goal_service.get_active_goal(user.id)

if not goal:
    st.switch_page("pages/2_Onboarding.py")

milestones = goal_service.get_milestones(goal.id)

mode = st.radio(
    "今日は何をしますか？",
    ["🌅 朝のナビ", "🌙 夜の振り返り", "💬 相談"],
    horizontal=True,
)

if mode == "🌅 朝のナビ":
    with st.spinner("今日のルートを準備しています..."):
        daily_task = checkin_service.get_or_create_today_tasks(user.id, goal, milestones)

    with ui.card("🗺️ Today's Route"):
        for i, task in enumerate(daily_task.tasks):
            checked = st.checkbox(
                task, value=daily_task.completed[i], key=f"task_{daily_task.date}_{i}"
            )
            if checked != daily_task.completed[i]:
                daily_task = checkin_service.toggle_task(daily_task, i)

elif mode == "🌙 夜の振り返り":
    todays_reflections = [
        r
        for r in checkin_service.get_reflections(user.id)
        if r.date == date.today() and r.goal_id == goal.id
    ]

    if todays_reflections:
        reflection = todays_reflections[0]
        with ui.card("今日の振り返り（記録済み）"):
            st.write(f"できたこと: {reflection.went_well}")
            st.write(f"困ったこと: {reflection.struggled}")
    else:
        st.write("今日の振り返りです。")
        went_well = st.text_area("できたことは？")
        struggled = st.text_area("困ったことは？")
        if st.button("振り返りを送信"):
            with st.spinner("..."):
                reply = checkin_service.submit_reflection(user.id, goal.id, went_well, struggled)
            ui.mentor_message(reply)

else:
    for message in checkin_service.get_conversation(user.id):
        with st.chat_message("assistant" if message.role == "ai" else "user"):
            st.write(message.message)

    consult_input = st.chat_input("相談してみましょう")
    if consult_input:
        with st.chat_message("user"):
            st.write(consult_input)
        with st.spinner("..."):
            reply = checkin_service.send_consultation(user.id, consult_input, goal)
        with st.chat_message("assistant"):
            st.write(reply)

st.divider()
if st.button("地図を見る"):
    st.switch_page("pages/4_Navigation.py")
