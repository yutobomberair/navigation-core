from datetime import date

from agent.client import chat_json, chat_text
from agent.prompts.route import (
    ROUGH_ESTIMATE_SYSTEM_PROMPT,
    ROUTE_SCHEMA,
    SYSTEM_PROMPT_TEMPLATE,
)
from app_platform.domain.models import CurrentState, Goal, Milestone


def rough_estimate(goal_title: str) -> str:
    """Quick, current-state-agnostic estimate shown right after the destination
    is entered — the 'searching route...' moment before we know the user's
    current position."""
    return chat_text(
        ROUGH_ESTIMATE_SYSTEM_PROMPT, [{"role": "user", "content": f"目標: {goal_title}"}]
    )


def _build_context(goal: Goal, current_state: CurrentState) -> str:
    lines = [f"目標: {goal.title}"]
    if goal.deadline:
        lines.append(f"期限: {goal.deadline}")
    if goal.background:
        lines.append(f"背景: {goal.background}")
    if goal.reason:
        lines.append(f"達成理由: {goal.reason}")
    if goal.ideal_state:
        lines.append(f"理想状態: {goal.ideal_state}")
    if current_state.current_ability:
        lines.append(f"自己申告レベル: {current_state.current_ability}")
    if current_state.issues:
        lines.append(f"現状課題: {current_state.issues}")
    if current_state.missing_elements:
        lines.append(f"不足要素: {current_state.missing_elements}")
    if current_state.parameters:
        params = ", ".join(f"{k} {v}%" for k, v in current_state.parameters.items())
        lines.append(f"診断テストによる実力推定: {params}")
    return "\n".join(lines)


def generate_route(goal: Goal, current_state: CurrentState) -> tuple[list[Milestone], str]:
    context = _build_context(goal, current_state)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())
    data = chat_json(system_prompt, [{"role": "user", "content": context}], ROUTE_SCHEMA, "route")
    milestones = [
        Milestone(goal_id=goal.id, order=i + 1, **milestone)
        for i, milestone in enumerate(data["milestones"])
    ]
    return milestones, data["estimated_arrival"]
