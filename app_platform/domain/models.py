from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID | None = None
    code: str
    # Set when the user's identity originated from LINE (management/) rather
    # than a web ?u= link; the two entry points share this one users row.
    line_user_id: str | None = None
    nickname: str | None = None
    created_at: datetime | None = None


class Person(BaseModel):
    user_id: UUID
    age: int | None = None
    personality: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    lifestyle: str | None = None
    available_time: str | None = None
    motivation_type: str | None = None


class Goal(BaseModel):
    id: UUID | None = None
    user_id: UUID
    title: str
    deadline: date | None = None
    background: str | None = None
    reason: str | None = None
    ideal_state: str | None = None
    status: Literal["active", "finished"] = "active"
    created_at: datetime | None = None


class CurrentState(BaseModel):
    id: UUID | None = None
    user_id: UUID
    goal_id: UUID
    current_ability: str | None = None
    issues: str | None = None
    missing_elements: str | None = None
    distance_to_goal: str | None = None
    # Per-parameter estimate (0-100) from the diagnostic assessment, e.g.
    # {"Vocabulary": 70, "Listening": 40}. Parameter names are chosen by the
    # AI per goal domain, so this is a free-form dict rather than fixed columns.
    parameters: dict[str, float] | None = None
    updated_at: datetime | None = None


class AssessmentQuestion(BaseModel):
    question: str
    choices: list[str]
    correct_index: int
    parameter: str


class Assessment(BaseModel):
    id: UUID | None = None
    user_id: UUID
    goal_id: UUID
    questions: list[AssessmentQuestion] = []
    answers: list[int] | None = None
    created_at: datetime | None = None


class Milestone(BaseModel):
    id: UUID | None = None
    goal_id: UUID
    order: int
    name: str
    kpi: str | None = None
    tasks: list[str] = []
    estimated_effort: str | None = None
    buffer: str | None = None
    status: Literal["not_started", "in_progress", "done"] = "not_started"


class DailyTask(BaseModel):
    id: UUID | None = None
    user_id: UUID
    # Nullable so rows created before this field existed still deserialize;
    # every row written by the app from now on always sets it, since "today's
    # tasks" must be scoped per goal — otherwise switching goals mid-day
    # resurfaces the previous goal's tasks (the unique key includes goal_id).
    goal_id: UUID | None = None
    date: date
    tasks: list[str] = []
    completed: list[bool] = []


class ConversationMessage(BaseModel):
    id: UUID | None = None
    user_id: UUID
    channel: Literal["checkin"] = "checkin"
    role: Literal["user", "ai"]
    message: str
    timestamp: datetime | None = None


class Reflection(BaseModel):
    id: UUID | None = None
    user_id: UUID
    goal_id: UUID | None = None  # see DailyTask.goal_id — same per-goal scoping reason
    date: date
    went_well: str | None = None
    struggled: str | None = None
