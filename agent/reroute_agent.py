import json

from agent.client import chat_with_tools
from agent.prompts.reroute import SYSTEM_PROMPT, UPDATE_ROUTE_TOOL
from app_platform.domain.models import Goal, Milestone


def _milestones_context(goal: Goal, milestones: list[Milestone]) -> str:
    lines = [f"目標: {goal.title}", "現在のマイルストーン:"]
    for m in milestones:
        lines.append(f"{m.order}. {m.name}（KPI: {m.kpi}, status: {m.status}）")
    return "\n".join(lines)


def reply(
    history: list[dict], goal: Goal, milestones: list[Milestone]
) -> tuple[str, list[Milestone] | None]:
    """Returns (reply_text, new_milestones). new_milestones is None unless the
    model decided this message was a reroute request."""
    context = [{"role": "system", "content": _milestones_context(goal, milestones)}]
    message = chat_with_tools(SYSTEM_PROMPT, context + history, [UPDATE_ROUTE_TOOL])

    if message.tool_calls:
        args = json.loads(message.tool_calls[0].function.arguments)
        new_milestones = [
            Milestone(goal_id=goal.id, order=i + 1, **m)
            for i, m in enumerate(args["milestones"])
        ]
        return args["reply"], new_milestones

    return message.content, None
