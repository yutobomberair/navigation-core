import streamlit as st

from app_platform import ui
from app_platform.config import LINE_ADD_FRIEND_URL
from app_platform.repository import users as users_repo
from app_platform.services import auth_service, goal_service, line_notify

ui.inject_css()

st.title("🧭 ルート検索")

user = auth_service.require_user()

if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = "destination"

step = st.session_state.wizard_step

# --- Step 1: destination ---
if step == "destination":
    st.subheader("あなたの目的地は？")
    goal_title = st.text_input("目標", label_visibility="collapsed", placeholder="例: TOEIC800点")

    if st.button("ルートを検索する", type="primary"):
        if not goal_title.strip():
            st.warning("目的地を入力してください。")
        else:
            with st.spinner("ルートを検索しています..."):
                rough = goal_service.get_rough_estimate(goal_title)
            st.session_state.wizard_goal_title = goal_title
            st.session_state.wizard_rough_estimate = rough
            st.session_state.wizard_step = "line_connect"
            st.rerun()

# --- Step 2: introduce LINE early, as a companion rather than a final chore ---
elif step == "line_connect":
    st.subheader("「" + st.session_state.wizard_goal_title + "」、いいですね 🎉")
    st.write("ここから一緒に進めていきましょう。")

    fresh_user = users_repo.get_user_by_code(user.code)
    if fresh_user and fresh_user.line_user_id:
        st.success("✅ LINE連携済みです。日々のやり取りはLINEで届きます。")
    else:
        st.write(
            "日々の振り返りや相談、ルートの調整はLINEで行います。"
            "先に友だち追加をしておくと、この後の通知もすぐに届きます。"
        )
        st.link_button("📱 公式LINEを友だち追加する", LINE_ADD_FRIEND_URL)
        st.caption(f"友だち追加後、最初のメッセージでこのコードを送ってください: `{user.code}`")
        st.caption("（後からでも連携できます。今はスキップして進めても大丈夫です）")

    if st.button("続ける", type="primary"):
        st.session_state.wizard_step = "current_position"
        st.rerun()

# --- Step 3: current position ---
elif step == "current_position":
    st.info(f"🔍 {st.session_state.wizard_rough_estimate}")

    st.subheader("あなたの現在地を教えてください")
    current_ability = st.text_input(
        "現在地", label_visibility="collapsed", placeholder="例: TOEIC500点くらい"
    )

    if st.button("距離を算出する", type="primary"):
        if not current_ability.strip():
            st.warning("現在地を入力してください。")
        else:
            with st.spinner("ゴールまでの距離を算出しています..."):
                goal, current_state = goal_service.save_goal_and_current_state(
                    user.id, st.session_state.wizard_goal_title, current_ability
                )
                assessment = goal_service.create_assessment(goal, current_state)

            st.session_state.wizard_goal = goal
            st.session_state.wizard_current_state = current_state
            st.session_state.wizard_assessment = assessment
            st.session_state.wizard_step = "checkpoint_round1"
            st.rerun()

# --- Step 4a: diagnostic test round 1, framed as a pre-drive checkpoint ---
elif step == "checkpoint_round1":
    st.subheader("🚗 ナビ開始前のご確認")
    st.caption("レンタカーのご利用前と同じように、簡単な確認をさせてください（実力診断）。")

    assessment = st.session_state.wizard_assessment

    with st.form("checkpoint_round1_form"):
        selections = []
        for i, q in enumerate(assessment.questions):
            choice = st.radio(q.question, q.choices, key=f"checkpoint_r1_q_{i}", index=None)
            selections.append(choice)

        submitted = st.form_submit_button("次へ")

    if submitted:
        if any(s is None for s in selections):
            st.warning("すべての項目に回答してください。")
        else:
            round1_answers = [
                q.choices.index(selections[i]) for i, q in enumerate(assessment.questions)
            ]
            with st.spinner("回答に合わせて次の質問を調整しています..."):
                updated_assessment = goal_service.generate_round2_assessment(
                    st.session_state.wizard_goal, assessment, round1_answers
                )

            st.session_state.wizard_assessment = updated_assessment
            st.session_state.wizard_round1_answers = round1_answers
            st.session_state.wizard_step = "checkpoint_round2"
            st.rerun()

# --- Step 4b: diagnostic test round 2 — difficulty adjusted per parameter ---
elif step == "checkpoint_round2":
    st.subheader("🚗 ナビ開始前のご確認（続き）")
    st.caption("さきほどの回答に合わせて、もう少しだけ確認させてください。")

    assessment = st.session_state.wizard_assessment
    round1_count = len(st.session_state.wizard_round1_answers)
    round2_questions = assessment.questions[round1_count:]

    with st.form("checkpoint_round2_form"):
        selections = []
        for i, q in enumerate(round2_questions):
            choice = st.radio(q.question, q.choices, key=f"checkpoint_r2_q_{i}", index=None)
            selections.append(choice)

        submitted = st.form_submit_button("確認を完了する")

    if submitted:
        if any(s is None for s in selections):
            st.warning("すべての項目に回答してください。")
        else:
            round2_answers = [
                q.choices.index(selections[i]) for i, q in enumerate(round2_questions)
            ]
            all_answers = st.session_state.wizard_round1_answers + round2_answers
            with st.spinner("ルートを確定しています..."):
                _, milestones, estimated_arrival = goal_service.score_and_finalize_route(
                    st.session_state.wizard_goal,
                    st.session_state.wizard_current_state,
                    assessment,
                    all_answers,
                )

            st.session_state.wizard_milestones = milestones
            st.session_state.wizard_estimated_arrival = estimated_arrival
            st.session_state.wizard_step = "confirm"
            st.rerun()

# --- Step 5: confirm and start navigation ---
else:
    st.subheader("ゴールまでの距離が算出されました")
    st.metric("到着予定", st.session_state.wizard_estimated_arrival)

    st.write("ルート:")
    for m in st.session_state.wizard_milestones:
        st.write(f"📍 STEP{m.order} {m.name}")

    st.caption(
        "※ これは今の情報から作った一旦のルートです。進めながらいつでも調整できるので、"
        "まずは一歩踏み出してみましょう。"
    )

    st.divider()
    # Re-fetch rather than trust the cached session user — linking happens
    # out-of-band on the LINE side while this page may already be open.
    fresh_user = users_repo.get_user_by_code(user.code)
    if fresh_user and fresh_user.line_user_id:
        st.success("✅ LINE連携済みです。ナビゲーション開始と同時にLINEにも通知します。")
    else:
        st.link_button("📱 公式LINEを友だち追加する", LINE_ADD_FRIEND_URL)
        st.caption(f"友だち追加後、最初のメッセージでこのコードを送ってください: `{user.code}`")

    st.write("このルートでよろしいですか？")
    if st.button("🚗 ナビゲーション開始", type="primary"):
        fresh_user = users_repo.get_user_by_code(user.code)
        if fresh_user and fresh_user.line_user_id:
            line_notify.push_text(
                fresh_user.line_user_id,
                f"🚗 ナビゲーション開始！「{st.session_state.wizard_goal.title}」に向けて、"
                "今日から一歩ずつ進みましょう。",
            )
        for key in list(st.session_state.keys()):
            if key.startswith("wizard_"):
                st.session_state.pop(key)
        st.switch_page("pages/4_Navigation.py")
