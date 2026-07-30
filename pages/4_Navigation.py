import streamlit as st


st.title("🧭 Navigation")


st.write(
    "現在地からゴールまで案内します"
)


if st.button("ルート変更"):
    st.switch_page(
        "pages/2_RouteSearch.py"
    )
    