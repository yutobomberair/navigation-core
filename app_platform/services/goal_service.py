from uuid import UUID

from agent import assessment_agent
from agent.route_agent import generate_route, rough_estimate
from app_platform.domain.models import Assessment, CurrentState, Goal, Milestone
from app_platform.repository import assessments as assessments_repo
from app_platform.repository import goals as goals_repo


def get_rough_estimate(goal_title: str) -> str:
    """Shown right after the destination is entered, before current position
    is known — the navigation-style 'searching route...' moment."""
    return rough_estimate(goal_title)


def save_goal_and_current_state(
    user_id: UUID, goal_title: str, current_ability: str
) -> tuple[Goal, CurrentState]:
    # A user should only ever have one active goal. Onboarding can be re-entered
    # either from a true fresh state or via "目標を変更する" on an existing
    # journey — in both cases, retire whatever was active first so it doesn't
    # resurface once the new goal is later finished.
    previous = goals_repo.get_latest_goal(str(user_id))
    if previous:
        goals_repo.finish_goal(previous.id)

    goal = goals_repo.create_goal(Goal(user_id=user_id, title=goal_title))
    current_state = goals_repo.save_current_state(
        CurrentState(user_id=user_id, goal_id=goal.id, current_ability=current_ability)
    )
    return goal, current_state


def create_assessment(goal: Goal, current_state: CurrentState) -> Assessment:
    """Round 1 only — round 2 depends on round 1's answers, so it can't be
    generated yet."""
    questions = assessment_agent.generate_round1(goal, current_state)
    return assessments_repo.save_assessment(
        Assessment(user_id=goal.user_id, goal_id=goal.id, questions=questions)
    )


def generate_round2_assessment(
    goal: Goal, assessment: Assessment, round1_answers: list[int]
) -> Assessment:
    """Appends round-2 questions (difficulty adjusted per parameter based on
    round-1 correctness) onto the assessment's question list."""
    round2_questions = assessment_agent.generate_round2(
        goal, assessment.questions, round1_answers
    )
    combined = assessment.questions + round2_questions
    return assessments_repo.update_questions(assessment.id, combined)


def score_and_finalize_route(
    goal: Goal, current_state: CurrentState, assessment: Assessment, answers: list[int]
) -> tuple[CurrentState, list[Milestone], str]:
    """Scores the diagnostic test and generates the route in one pass — unlike
    the earlier chat-based flow, there's no provisional route to replace here
    since the test always runs before any route is generated."""
    parameters = assessment_agent.score(assessment.questions, answers)
    assessments_repo.save_answers(assessment.id, answers)
    updated_current_state = goals_repo.update_current_state_parameters(
        current_state.id, parameters
    )

    milestones, estimated_arrival = generate_route(goal, updated_current_state)
    saved_milestones = goals_repo.save_milestones(goal.id, milestones)
    goals_repo.update_estimated_arrival(goal.id, estimated_arrival)

    return updated_current_state, saved_milestones, estimated_arrival


def get_active_goal(user_id: UUID) -> Goal | None:
    return goals_repo.get_latest_goal(str(user_id))


def get_milestones(goal_id: UUID) -> list[Milestone]:
    return goals_repo.get_milestones(str(goal_id))


def mark_milestone_done(milestone_id: UUID) -> None:
    goals_repo.update_milestone_status(str(milestone_id), "done")


def add_milestone(goal_id: UUID, name: str, insert_after_order: int = 0) -> list[Milestone]:
    """insert_after_order=0 inserts at the very front; otherwise it's placed
    right after the milestone currently holding that order number. Existing
    milestones are renumbered around it (id/status of untouched ones is
    preserved, matching how reroute_agent already rewrites the whole route)."""
    existing = goals_repo.get_milestones(str(goal_id))
    new_milestone = Milestone(goal_id=goal_id, order=0, name=name, status="not_started")

    reordered = []
    if insert_after_order == 0:
        reordered.append(new_milestone)
    for m in existing:
        reordered.append(m)
        if m.order == insert_after_order:
            reordered.append(new_milestone)

    for i, m in enumerate(reordered, start=1):
        m.order = i

    goals_repo.delete_milestones(str(goal_id))
    return goals_repo.save_milestones(str(goal_id), reordered)


def remove_milestone(milestone_id: UUID) -> None:
    goals_repo.delete_milestone(milestone_id)


def finish_active_goal(goal_id: UUID) -> None:
    """Ends the current journey — the goal stops being picked up by
    get_active_goal, so the next Title visit starts a fresh Onboarding.
    Past data (goal, milestones, daily tasks, reflections) is kept for
    history rather than deleted."""
    goals_repo.finish_goal(goal_id)
