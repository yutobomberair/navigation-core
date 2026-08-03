"""Proactive LINE push notifications from the Streamlit side (e.g. "route
confirmed, navigation started"). Deliberately a raw HTTP call rather than
importing management/ (which depends on line-bot-sdk) — the Streamlit app's
own requirements.txt stays free of that dependency, matching the existing
split between the two processes.

Best-effort: a missing token or a LINE API hiccup should never block the
onboarding flow, so failures are swallowed rather than raised.
"""

import httpx
import streamlit as st

from app_platform.config import LINE_CHANNEL_ACCESS_TOKEN

_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def push_text(line_user_id: str, text: str) -> None:
    token = st.secrets.get(LINE_CHANNEL_ACCESS_TOKEN)
    if not token:
        return

    try:
        httpx.post(
            _PUSH_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"to": line_user_id, "messages": [{"type": "text", "text": text}]},
            timeout=10,
        )
    except httpx.HTTPError:
        pass
