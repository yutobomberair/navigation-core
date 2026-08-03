from app_platform.db.client import get_client
from app_platform.domain.models import Assessment


def save_assessment(assessment: Assessment) -> Assessment:
    client = get_client()
    payload = assessment.model_dump(mode="json", exclude={"id", "created_at"})
    created = client.table("assessments").insert(payload).execute()
    return Assessment(**created.data[0])


def save_answers(assessment_id, answers: list[int]) -> Assessment:
    client = get_client()
    updated = (
        client.table("assessments")
        .update({"answers": answers})
        .eq("id", str(assessment_id))
        .execute()
    )
    return Assessment(**updated.data[0])
