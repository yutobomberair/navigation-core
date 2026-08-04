from app_platform.db.client import get_client
from app_platform.domain.models import CurrentState, Goal, Milestone


def create_goal(goal: Goal) -> Goal:
    client = get_client()
    payload = goal.model_dump(mode="json", exclude={"id", "created_at"})
    created = client.table("goals").insert(payload).execute()
    return Goal(**created.data[0])


def get_latest_goal(user_id: str) -> Goal | None:
    client = get_client()
    result = (
        client.table("goals")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return Goal(**result.data[0])


def finish_goal(goal_id) -> None:
    client = get_client()
    client.table("goals").update({"status": "finished"}).eq("id", str(goal_id)).execute()


def update_estimated_arrival(goal_id, estimated_arrival: str) -> Goal:
    client = get_client()
    updated = (
        client.table("goals")
        .update({"estimated_arrival": estimated_arrival})
        .eq("id", str(goal_id))
        .execute()
    )
    return Goal(**updated.data[0])


def save_current_state(state: CurrentState) -> CurrentState:
    client = get_client()
    payload = state.model_dump(mode="json", exclude={"id", "updated_at"})
    created = client.table("current_states").insert(payload).execute()
    return CurrentState(**created.data[0])


def get_current_state(goal_id: str) -> CurrentState | None:
    client = get_client()
    result = (
        client.table("current_states")
        .select("*")
        .eq("goal_id", goal_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    return CurrentState(**result.data[0])


def save_milestones(goal_id: str, milestones: list[Milestone]) -> list[Milestone]:
    client = get_client()
    payload = [
        m.model_dump(mode="json", exclude={"id"}) | {"goal_id": str(goal_id)}
        for m in milestones
    ]
    created = client.table("milestones").insert(payload).execute()
    return [Milestone(**row) for row in created.data]


def get_milestones(goal_id: str) -> list[Milestone]:
    client = get_client()
    result = (
        client.table("milestones")
        .select("*")
        .eq("goal_id", goal_id)
        .order("order")
        .execute()
    )
    return [Milestone(**row) for row in result.data]


def update_milestone_status(milestone_id: str, status: str) -> None:
    client = get_client()
    client.table("milestones").update({"status": status}).eq("id", milestone_id).execute()


def delete_milestones(goal_id: str) -> None:
    client = get_client()
    client.table("milestones").delete().eq("goal_id", str(goal_id)).execute()


def delete_milestone(milestone_id) -> None:
    client = get_client()
    client.table("milestones").delete().eq("id", str(milestone_id)).execute()


def update_current_state_parameters(
    current_state_id, parameters: dict[str, float]
) -> CurrentState:
    client = get_client()
    updated = (
        client.table("current_states")
        .update({"parameters": parameters})
        .eq("id", str(current_state_id))
        .execute()
    )
    return CurrentState(**updated.data[0])
