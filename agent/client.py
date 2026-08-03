import json
import os

import streamlit as st
from openai import OpenAI

from agent.mock import mock_chat_json, mock_chat_text, mock_chat_with_tools
from app_platform.config import OPENAI_API_KEY, get_secret

DEFAULT_MODEL = "gpt-4o-mini"


def _mock_enabled() -> bool:
    return os.environ.get("PROGRESS_NAVI_MOCK_AI") == "1"


@st.cache_resource
def get_client() -> OpenAI:
    return OpenAI(api_key=get_secret(OPENAI_API_KEY))


def _model() -> str:
    return st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)


def chat_text(system_prompt: str, messages: list[dict]) -> str:
    if _mock_enabled():
        return mock_chat_text()

    client = get_client()
    response = client.chat.completions.create(
        model=_model(),
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return response.choices[0].message.content


def chat_json(system_prompt: str, messages: list[dict], schema: dict, schema_name: str) -> dict:
    if _mock_enabled():
        return mock_chat_json(schema_name)

    client = get_client()
    response = client.chat.completions.create(
        model=_model(),
        messages=[{"role": "system", "content": system_prompt}, *messages],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": schema, "strict": True},
        },
    )
    return json.loads(response.choices[0].message.content)


def chat_with_tools(system_prompt: str, messages: list[dict], tools: list[dict]):
    """Lets the model optionally call a tool instead of just replying with
    text — used for the LINE reroute conversation, where the AI decides for
    itself whether a message is asking to change the route. Returns the raw
    message object; callers check `.tool_calls` vs `.content`."""
    if _mock_enabled():
        return mock_chat_with_tools()

    client = get_client()
    response = client.chat.completions.create(
        model=_model(),
        messages=[{"role": "system", "content": system_prompt}, *messages],
        tools=tools,
        tool_choice="auto",
    )
    return response.choices[0].message
