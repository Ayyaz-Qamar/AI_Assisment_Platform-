"""
Scoring engine: pure functions, no ML, no DB writes.
"""
from typing import List, Tuple

DIFFICULTY_WEIGHTS = {"easy": 1, "medium": 2, "hard": 3}


def calculate_score(
    answers: List[Tuple[bool, str]]
) -> Tuple[float, float, float]:
    """
    answers: list of (is_correct, difficulty_string)
    returns: (weighted_score_pct, accuracy_pct, avg_difficulty)
    """
    if not answers:
        return 0.0, 0.0, 0.0

    total_weight = 0
    earned_weight = 0
    correct_count = 0

    for is_correct, difficulty in answers:
        w = DIFFICULTY_WEIGHTS.get(difficulty, 1)
        total_weight += w
        if is_correct:
            earned_weight += w
            correct_count += 1

    score_pct = (earned_weight / total_weight) * 100 if total_weight else 0
    accuracy = (correct_count / len(answers)) * 100
    avg_diff = total_weight / len(answers)

    return round(score_pct, 2), round(accuracy, 2), round(avg_diff, 2)


def get_competency_level(score: float) -> str:
    if score < 50:
        return "Beginner"
    if score < 80:
        return "Intermediate"
    return "Expert"
