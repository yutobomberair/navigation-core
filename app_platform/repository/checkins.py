from app_platform.db.client import get_client
from app_platform.domain.models import ConversationMessage, DailyTask, Reflection


def save_daily_tasks(daily_task: DailyTask) -> DailyTask:
    client = get_client()
    payload = daily_task.model_dump(mode="json", exclude={"id"})
    created = (
        client.table("daily_tasks")
        .upsert(payload, on_conflict="user_id,goal_id,date")
        .execute()
    )
    return DailyTask(**created.data[0])


def get_daily_tasks(user_id: str, goal_id: str, date_str: str) -> DailyTask | None:
    client = get_client()
    result = (
        client.table("daily_tasks")
        .select("*")
        .eq("user_id", user_id)
        .eq("goal_id", goal_id)
        .eq("date", date_str)
        .execute()
    )
    if not result.data:
        return None
    return DailyTask(**result.data[0])


def get_task_history(user_id: str, limit: int = 14) -> list[DailyTask]:
    client = get_client()
    result = (
        client.table("daily_tasks")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return [DailyTask(**row) for row in result.data]


def save_reflection(reflection: Reflection) -> Reflection:
    client = get_client()
    payload = reflection.model_dump(mode="json", exclude={"id"})
    created = (
        client.table("reflections")
        .upsert(payload, on_conflict="user_id,goal_id,date")
        .execute()
    )
    return Reflection(**created.data[0])


def get_reflections(user_id: str, limit: int = 14) -> list[Reflection]:
    client = get_client()
    result = (
        client.table("reflections")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return [Reflection(**row) for row in result.data]


def append_message(message: ConversationMessage) -> None:
    client = get_client()
    payload = message.model_dump(mode="json", exclude={"id", "timestamp"})
    client.table("conversation_history").insert(payload).execute()


def get_conversation(user_id: str, channel: str, limit: int = 50) -> list[ConversationMessage]:
    client = get_client()
    result = (
        client.table("conversation_history")
        .select("*")
        .eq("user_id", user_id)
        .eq("channel", channel)
        .order("timestamp")
        .limit(limit)
        .execute()
    )
    return [ConversationMessage(**row) for row in result.data]
