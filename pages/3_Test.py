import streamlit as st


st.title("✈️ Test")


st.write(
    "あなたの現在地を分析しています"
)


if st.button("分析完了"):
    st.switch_page(
        "pages/4_Navigation.py"
    )