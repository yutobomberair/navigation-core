"""Canned AI responses used when PROGRESS_NAVI_MOCK_AI=1.

Lets self-testing (Playwright, smoke scripts) exercise the full app —
including the JSON parsing / DB-write code paths that are the usual source
of bugs — without spending real OpenAI credits. Never enabled for real
deployments; only set by test drivers.
"""

MOCK_ASSESSMENT = {
    "questions": [
        {
            "question": "（モック問1）Vocabulary",
            "choices": ["A", "B", "C", "D"],
            "correct_index": 0,
            "parameter": "Vocabulary",
        },
        {
            "question": "（モック問2）Vocabulary",
            "choices": ["A", "B", "C", "D"],
            "correct_index": 1,
            "parameter": "Vocabulary",
        },
        {
            "question": "（モック問3）Listening",
            "choices": ["A", "B", "C", "D"],
            "correct_index": 2,
            "parameter": "Listening",
        },
        {
            "question": "（モック問4）Listening",
            "choices": ["A", "B", "C", "D"],
            "correct_index": 3,
            "parameter": "Listening",
        },
    ]
}

MOCK_ROUTE = {
    "estimated_arrival": "（モック）約4ヶ月後",
    "milestones": [
        {
            "name": "モックステップ1：単語",
            "kpi": "単語1000語",
            "tasks": ["単語帳1周", "復習テスト"],
            "estimated_effort": "1ヶ月",
            "buffer": "1週間",
        },
        {
            "name": "モックステップ2：リスニング",
            "kpi": "模試スコア700",
            "tasks": ["リスニング教材30分/日"],
            "estimated_effort": "1ヶ月",
            "buffer": "1週間",
        },
    ]
}

MOCK_MORNING = {
    "message": "（モック）おはようございます。今日も一歩ずつ進みましょう。",
    "tasks": ["モックタスク1", "モックタスク2"],
}

MOCK_TEXT_REPLY = "（モック応答）お疲れ様でした。無理せず進めましょう。"

_JSON_RESPONSES = {
    "assessment": MOCK_ASSESSMENT,
    "route": MOCK_ROUTE,
    "morning": MOCK_MORNING,
}


def mock_chat_json(schema_name: str) -> dict:
    return _JSON_RESPONSES[schema_name]


def mock_chat_text() -> str:
    return MOCK_TEXT_REPLY


def mock_chat_with_tools():
    """Mimics an OpenAI message object that chose not to call a tool —
    reroute *decision-making* only makes sense to test against the real
    model, so the mock just proves the code path doesn't crash."""
    from types import SimpleNamespace

    return SimpleNamespace(content=MOCK_TEXT_REPLY, tool_calls=None)
