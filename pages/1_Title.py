import streamlit as st


st.title("🧭 Progress Navi")
st.write(
    "踏み出した一歩を、ゴールまで届ける"
)


# 初回判定
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True


if st.button("旅を始める"):

    if st.session_state.first_visit:
        st.session_state.first_visit = False
        st.switch_page(
            "pages/2_RouteSearch.py"
        )

    else:
        st.switch_page(
            "pages/4_Navigation.py"
        )
        