import uuid

from app_platform.db.client import get_client
from app_platform.domain.models import Person, User


def get_or_create_user(code: str) -> User:
    client = get_client()
    existing = client.table("users").select("*").eq("code", code).execute()
    if existing.data:
        return User(**existing.data[0])

    created = client.table("users").insert({"code": code}).execute()
    return User(**created.data[0])


def get_or_create_by_line_id(line_user_id: str) -> User:
    """LINE users have no 'code' of their own — generate one so they can also
    open the web dashboard via ?u=<code> if they want to."""
    client = get_client()
    existing = client.table("users").select("*").eq("line_user_id", line_user_id).execute()
    if existing.data:
        return User(**existing.data[0])

    code = f"line-{uuid.uuid4().hex[:10]}"
    created = (
        client.table("users").insert({"code": code, "line_user_id": line_user_id}).execute()
    )
    return User(**created.data[0])


def get_user_by_code(code: str) -> User | None:
    client = get_client()
    result = client.table("users").select("*").eq("code", code).execute()
    if not result.data:
        return None
    return User(**result.data[0])


def link_line_id(user_id, line_user_id: str) -> User:
    """Merges a LINE identity into an existing (web-originated) user, so a
    tester who started on the web and then adds the LINE bot ends up as one
    user row instead of two disconnected ones."""
    client = get_client()
    updated = (
        client.table("users")
        .update({"line_user_id": line_user_id})
        .eq("id", str(user_id))
        .execute()
    )
    return User(**updated.data[0])


def save_person(person: Person) -> None:
    client = get_client()
    payload = person.model_dump(mode="json")
    client.table("persons").upsert(payload).execute()


def get_person(user_id: str) -> Person | None:
    client = get_client()
    result = client.table("persons").select("*").eq("user_id", user_id).execute()
    if not result.data:
        return None
    return Person(**result.data[0])
