"""
Recommendation engine — detects weak difficulty levels and proposes a learning path.
"""
from collections import defaultdict
from typing import List, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models import Answer, Test


class RecommendationEngine:

    @staticmethod
    def analyze_weak_areas(
        db: Session, attempt_id: int
    ) -> Tuple[List[dict], List[str]]:
        # Eager-load questions to avoid N+1
        answers = (
            db.query(Answer)
            .options(joinedload(Answer.question))
            .filter(Answer.attempt_id == attempt_id)
            .all()
        )

        stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for a in answers:
            diff = a.question.difficulty.value
            stats[diff]["total"] += 1
            if a.is_correct:
                stats[diff]["correct"] += 1

        weak: List[dict] = []
        recs: List[str] = []

        for diff in ["easy", "medium", "hard"]:
            s = stats.get(diff)
            if not s or s["total"] == 0:
                continue
            acc = (s["correct"] / s["total"]) * 100
            if acc < 60:
                weak.append({
                    "difficulty": diff,
                    "correct": s["correct"],
                    "total": s["total"],
                    "accuracy": round(acc, 2),
                })
                recs.append(
                    f"Focus on practicing more {diff}-level questions to strengthen this area."
                )

        if not weak:
            recs.append(
                "Excellent performance across all levels — try a more advanced test."
            )
        else:
            recs.append("Review the topics you missed before retaking.")
            recs.append("Build fundamentals before moving to harder material.")

        return weak, recs

    @staticmethod
    def suggest_next_tests(
        db: Session, current_test_id: int, limit: int = 5
    ) -> List[dict]:
        rows = (
            db.query(Test)
            .filter(Test.id != current_test_id)
            .order_by(Test.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{"id": t.id, "title": t.title, "category": t.category} for t in rows]
