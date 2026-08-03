import streamlit as st

from app_platform.domain.models import User
from app_platform.repository import users as users_repo


def get_or_create_user(code: str) -> User:
    return users_repo.get_or_create_user(code)


def require_user() -> User:
    """Identify the current tester from the ?u= link code.

    There is no password-based auth in this mock — the per-tester link
    (e.g. https://<app>/?u=abc123) sent to each interview participant is
    the identity boundary, so they land on the same data across days.
    """
    # st.switch_page drops query params on navigation (confirmed: this happens
    # on every switch_page call, not just the app.py entry redirect), so the
    # code must also be remembered in session_state and re-asserted into the
    # URL — query_params alone does not survive past the first page.
    code = st.query_params.get("u") or st.session_state.get("user_code")
    if not code:
        st.title("🧭 Progress Navi")
        st.write("あなたのコードを入力してください。")
        entered = st.text_input("コード", label_visibility="collapsed", placeholder="例: test1")
        if st.button("ログイン", type="primary") and entered.strip():
            # Only set query_params here — session_state["user_code"] must stay
            # unset so the block below still runs get_or_create_user() on the
            # next rerun (it's gated on user_code being *out of sync* with code).
            st.query_params["u"] = entered.strip()
            st.rerun()
        st.caption("個別リンク（例: ?u=あなたのコード）からのアクセスでも入れます。")
        st.stop()

    st.query_params["u"] = code

    if st.session_state.get("user_code") != code:
        st.session_state["user"] = users_repo.get_or_create_user(code)
        st.session_state["user_code"] = code

    return st.session_state["user"]
