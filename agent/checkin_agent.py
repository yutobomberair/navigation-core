from agent.client import chat_json, chat_text
from agent.prompts.checkin import (
    CONSULT_SYSTEM_PROMPT,
    EVENING_SYSTEM_PROMPT,
    MORNING_SCHEMA,
    MORNING_SYSTEM_PROMPT,
)
from app_platform.domain.models import Goal, Milestone


def morning_message(goal: Goal, milestones: list[Milestone]) -> dict:
    current = next((m for m in milestones if m.status != "done"), None)
    context = f"目標: {goal.title}\n現在のマイルストーン: {current.name if current else '未設定'}"
    if current:
        context += f"\nマイルストーンのタスク候補: {', '.join(current.tasks)}"
    return chat_json(
        MORNING_SYSTEM_PROMPT, [{"role": "user", "content": context}], MORNING_SCHEMA, "morning"
    )


def evening_reply(went_well: str, struggled: str) -> str:
    content = f"できたこと: {went_well}\n困ったこと: {struggled}"
    return chat_text(EVENING_SYSTEM_PROMPT, [{"role": "user", "content": content}])


def consult_reply(history: list[dict], goal: Goal | None) -> str:
    messages = list(history)
    if goal:
        messages = [
            {"role": "system", "content": f"ユーザーの目標: {goal.title}（期限: {goal.deadline}）"}
        ] + messages
    return chat_text(CONSULT_SYSTEM_PROMPT, messages)
