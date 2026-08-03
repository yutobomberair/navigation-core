from collections import defaultdict

from agent.client import chat_json
from agent.prompts.assessment import ASSESSMENT_SCHEMA, SYSTEM_PROMPT
from app_platform.domain.models import AssessmentQuestion, CurrentState, Goal


def generate_test(goal: Goal, current_state: CurrentState) -> list[AssessmentQuestion]:
    context = (
        f"目標: {goal.title}\n"
        f"自己申告レベル: {current_state.current_ability}"
    )
    data = chat_json(
        SYSTEM_PROMPT, [{"role": "user", "content": context}], ASSESSMENT_SCHEMA, "assessment"
    )
    return [AssessmentQuestion(**q) for q in data["questions"]]


def score(questions: list[AssessmentQuestion], answers: list[int]) -> dict[str, float]:
    """Deterministic, no AI call: % correct per parameter, rounded to whole numbers."""
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
