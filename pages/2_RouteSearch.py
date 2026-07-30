import streamlit as st


st.title("🗺 Route Search")

st.write(
    "目的地を設定してください"
)


goal = st.text_input(
    "あなたの目標"
)


if st.button("搭乗手続きへ"):
    st.switch_page(
        "pages/3_Test.py"
    )
    