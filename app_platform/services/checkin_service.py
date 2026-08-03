from datetime import date
from uuid import UUID

from agent import checkin_agent
from app_platform.domain.models import ConversationMessage, DailyTask, Goal, Milestone, Reflection
from app_platform.repository import checkins as checkins_repo


def get_or_create_today_tasks(
    user_id: UUID, goal: Goal, milestones: list[Milestone]
) -> DailyTask:
    today = date.today()
    existing = checkins_repo.get_daily_tasks(str(user_id), str(goal.id), today.isoformat())
    if existing:
        return existing

    result = checkin_agent.morning_message(goal, milestones)
    daily_task = DailyTask(
        user_id=user_id,
        goal_id=goal.id,
        date=today,
        tasks=result["tasks"],
        completed=[False] * len(result["tasks"]),
    )
    saved = checkins_repo.save_daily_tasks(daily_task)
    checkins_repo.append_message(
        ConversationMessage(user_id=user_id, channel="checkin", role="ai", message=result["message"])
    )
    return saved


def toggle_task(daily_task: DailyTask, index: int) -> DailyTask:
    completed = list(daily_task.completed)
    completed[index] = not completed[index]
    daily_task.completed = completed
    return checkins_repo.save_daily_tasks(daily_task)


def get_task_history(user_id: UUID) -> list[DailyTask]:
    return checkins_repo.get_task_history(str(user_id))


def submit_reflection(user_id: UUID, goal_id: UUID, went_well: str, struggled: str) -> str:
    checkins_repo.save_reflection(
        Reflection(
            user_id=user_id,
            goal_id=goal_id,
            date=date.today(),
            went_well=went_well,
            struggled=struggled,
        )
    )
    reply = checkin_agent.evening_reply(went_well, struggled)
    checkins_repo.append_message(
        ConversationMessage(user_id=user_id, channel="checkin", role="ai", message=reply)
    )
    return reply


def get_reflections(user_id: UUID) -> list[Reflection]:
    return checkins_repo.get_reflections(user_id=str(user_id))


def get_conversation(user_id: UUID) -> list[ConversationMessage]:
    return checkins_repo.get_conversation(str(user_id), "checkin")


def send_consultation(user_id: UUID, user_message: str, goal: Goal | None) -> str:
    checkins_repo.append_message(
        ConversationMessage(user_id=user_id, channel="checkin", role="user", message=user_message)
    )
    history = [
        {"role": "user" if m.role == "user" else "assistant", "content": m.message}
        for m in checkins_repo.get_conversation(str(user_id), "checkin")
    ]
    reply = checkin_agent.consult_reply(history, goal)
    checkins_repo.append_message(
        ConversationMessage(user_id=user_id, channel="checkin", role="ai", message=reply)
    )
    return reply
