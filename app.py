import streamlit as st

st.set_page_config(
    page_title="Navigation Core",
    page_icon="🧭",
    layout="wide"
)

st.title("🧭 Navigation Core")
st.caption("Goal Achievement Navigation System")

# ---------------------------------
# レイアウト
# ---------------------------------
col_nav, col_chat, col_system = st.columns([3, 5, 2])

# ==========================================
# Navigation
# ==========================================
with col_nav:

    st.subheader("🗺 Navigation")

    st.markdown("### 🎯 Goal")
    st.info("TOEIC 800")

    st.markdown("### 📍 Progress")

    st.progress(0.42)
    st.write("42%")

    st.markdown("### 🛣 Milestones")

    st.checkbox("Goal Fixed", value=True, disabled=True)
    st.checkbox("Current Analysis", value=True, disabled=True)
    st.checkbox("KPI Designed", value=False, disabled=True)
    st.checkbox("Execution", value=False, disabled=True)
    st.checkbox("Review", value=False, disabled=True)

    st.markdown("---")

    st.markdown("### 📈 KPI")

    st.metric("Reading", "620", "+20")
    st.metric("Listening", "590", "+15")


# ==========================================
# Chat
# ==========================================
with col_chat:

    st.subheader("💬 Agent")

    with st.chat_message("assistant"):
        st.write(
            "こんにちは。\n\n"
            "私はあなたの目標達成をサポートするNavigation Agentです。\n\n"
            "まずはあなたの目標を教えてください。"
        )

    with st.chat_message("user"):
        st.write("TOEIC800点取りたい")

    st.chat_input("メッセージを入力...")


# ==========================================
# System
# ==========================================
with col_system:

    st.subheader("⚙ System")

    st.markdown("### Management")
    st.success("Idle")

    st.markdown("### Agent")
    st.info("Waiting")

    st.markdown("### Sensor")
    st.success("Connected")

    st.markdown("### Timer")
    st.info("20:00")

    st.markdown("---")

    st.markdown("### State")

    st.code(
        """INITIAL

Goal Fixed

Current Analysis

Planning...
"""
    )