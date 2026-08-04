from collections import defaultdict

from agent.client import chat_json
from agent.prompts.assessment import (
    ASSESSMENT_ROUND_SCHEMA,
    ROUND1_SYSTEM_PROMPT,
    ROUND2_SYSTEM_PROMPT,
)
from app_platform.domain.models import AssessmentQuestion, CurrentState, Goal


def generate_round1(goal: Goal, current_state: CurrentState) -> list[AssessmentQuestion]:
    context = f"目標: {goal.title}\n自己申告レベル: {current_state.current_ability}"
    data = chat_json(
        ROUND1_SYSTEM_PROMPT,
        [{"role": "user", "content": context}],
        ASSESSMENT_ROUND_SCHEMA,
        "assessment_round1",
    )
    return [AssessmentQuestion(**q) for q in data["questions"]]


def generate_round2(
    goal: Goal, round1_questions: list[AssessmentQuestion], round1_answers: list[int]
) -> list[AssessmentQuestion]:
    lines = [f"目標: {goal.title}", "1問目の結果:"]
    for q, a in zip(round1_questions, round1_answers):
        correct = a == q.correct_index
        lines.append(f"parameter={q.parameter}, できていた={'○' if correct else '×'}")
    context = "\n".join(lines)

    data = chat_json(
        ROUND2_SYSTEM_PROMPT,
        [{"role": "user", "content": context}],
        ASSESSMENT_ROUND_SCHEMA,
        "assessment_round2",
    )
    return [AssessmentQuestion(**q) for q in data["questions"]]


def score(questions: list[AssessmentQuestion], answers: list[int]) -> dict[str, float]:
    """Deterministic, no AI call: % correct per parameter across both rounds,
    rounded to whole numbers."""
    correct_by_param: dict[str, int] = defaultdict(int)
    total_by_param: dict[str, int] = defaultdict(int)

    for question, answer in zip(questions, answers):
        total_by_param[question.parameter] += 1
        if answer == question.correct_index:
            correct_by_param[question.parameter] += 1

    return {
        parameter: round(100 * correct_by_param[parameter] / total)
        for parameter, total in total_by_param.items()
    }
