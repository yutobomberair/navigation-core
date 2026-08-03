import streamlit as st

from app_platform import ui
from app_platform.config import LINE_ADD_FRIEND_URL
from app_platform.services import auth_service, checkin_service, goal_service

st.title("🧭 Navigation")
ui.inject_css()

user = auth_service.require_user()
goal = goal_service.get_active_goal(user.id)

if not goal:
    st.switch_page("pages/2_Onboarding.py")

milestones = goal_service.get_milestones(goal.id)
current = next((m for m in milestones if m.status != "done"), None)

st.subheader(f"🎯 {goal.title}")
st.caption(f"期限: {goal.deadline}" if goal.deadline else "期限未設定")

if not user.line_user_id:
    st.link_button("📱 公式LINEを友だち追加して通知を受け取る", LINE_ADD_FRIEND_URL)

# --- Today's Navigation ---
with st.spinner("今日のルートを確認しています..."):
    daily_task = checkin_service.get_or_create_today_tasks(user.id, goal, milestones)

with ui.card("🗺️ Today's Route"):
    for i, task in enumerate(daily_task.tasks):
        ui.task_row(task, daily_task.completed[i])

# --- Mentor Message ---
conversation = checkin_service.get_conversation(user.id)
ai_messages = [m for m in conversation if m.role == "ai"]
if ai_messages:
    ui.mentor_message(ai_messages[-1].message)

# --- Map ---
st.markdown("#### 🗾 Map")
ui.render_map_path(milestones, current.id if current else None)

if current is not None:
    if st.button(f"「{current.name}」を完了する", use_container_width=True):
        goal_service.mark_milestone_done(current.id)
        st.rerun()

# --- Milestone editor: adjust the current route without restarting ---
with st.expander("マイルストーンを追加・編集する"):
    for m in milestones:
        col_name, col_delete = st.columns([5, 1])
        with col_name:
            st.write(f"STEP{m.order} {m.name}")
        with col_delete:
            if st.button("削除", key=f"delete_milestone_{m.id}"):
                goal_service.remove_milestone(m.id)
                st.rerun()

    new_name = st.text_input("新しいマイルストーンの名前", key="new_milestone_name")
    position_options = {"先頭に追加": 0}
    position_options.update({f"STEP{m.order} {m.name} の後に追加": m.order for m in milestones})
    position_label = st.selectbox("挿入位置", list(position_options.keys()), index=len(position_options) - 1)
    if st.button("追加する"):
        if new_name.strip():
            goal_service.add_milestone(goal.id, new_name, position_options[position_label])
            st.rerun()
        else:
            st.warning("名前を入力してください。")

# --- History ---
with st.expander("過去履歴を見る"):
    st.write("Daily Tasks")
    for t in checkin_service.get_task_history(user.id):
        done_count = sum(t.completed)
        st.write(f"{t.date}: {done_count}/{len(t.tasks)} 完了")

    st.write("振り返り")
    for r in checkin_service.get_reflections(user.id):
        st.write(f"{r.date} — できたこと: {r.went_well} / 困ったこと: {r.struggled}")

st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("今日のナビへ", use_container_width=True):
        st.switch_page("pages/3_DailyCheckIn.py")
with col2:
    if st.button("目標を変更する（最初からやり直す）", use_container_width=True):
        st.switch_page("pages/2_Onboarding.py")

if st.session_state.get("confirm_finish"):
    st.warning("この目標のナビゲーションを終了します。よろしいですか？")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("はい、終了する", use_container_width=True):
            goal_service.finish_active_goal(goal.id)
            st.session_state.pop("confirm_finish", None)
            st.switch_page("pages/1_Title.py")
    with col_no:
        if st.button("キャンセル", use_container_width=True):
            st.session_state.pop("confirm_finish", None)
            st.rerun()
else:
    if st.button("🏁 案内終了"):
        st.session_state["confirm_finish"] = True
        st.rerun()
