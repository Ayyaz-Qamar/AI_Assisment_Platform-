"""
Adaptive Test Engine — with smart repeat prevention.
- Start: medium difficulty
- Correct -> harder
- Wrong   -> easier
- Skips questions the user attempted in the last 30 days
  (falls back gracefully when fresh pool is exhausted)
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Answer, Question, TestAttempt

DIFFICULTY_ORDER = ["easy", "medium", "hard"]
REPEAT_PREVENTION_DAYS = 30


class AdaptiveEngine:

    @staticmethod
    def get_next_difficulty(current: str, was_correct: Optional[bool]) -> str:
        if was_correct is None:
            return "medium"
        if current not in DIFFICULTY_ORDER:
            return "medium"

        idx = DIFFICULTY_ORDER.index(current)
        if was_correct and idx < len(DIFFICULTY_ORDER) - 1:
            return DIFFICULTY_ORDER[idx + 1]
        if (not was_correct) and idx > 0:
            return DIFFICULTY_ORDER[idx - 1]
        return current

    @staticmethod
    def _recently_attempted_question_ids(
        db: Session, user_id: int, test_id: int
    ) -> set[int]:
        """Question IDs the user attempted in this test within the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=REPEAT_PREVENTION_DAYS)
        rows = (
            db.query(Answer.question_id)
            .join(TestAttempt, TestAttempt.id == Answer.attempt_id)
            .filter(
                TestAttempt.user_id == user_id,
                TestAttempt.test_id == test_id,
                Answer.answered_at >= cutoff,
            )
            .all()
        )
        return {r[0] for r in rows}

    @staticmethod
    def get_next_question(
        db: Session,
        test_id: int,
        attempt_id: int,
        target_difficulty: str,
        user_id: Optional[int] = None,
    ) -> Optional[Question]:
        # 1. Always exclude questions answered in THIS attempt
        answered_in_attempt = {
            row[0]
            for row in db.query(Answer.question_id)
            .filter(Answer.attempt_id == attempt_id)
            .all()
        }

        # 2. Prefer to also exclude recently-attempted questions across past attempts
        recently_seen = set()
        if user_id is not None:
            recently_seen = AdaptiveEngine._recently_attempted_question_ids(
                db, user_id, test_id
            )

        base = db.query(Question).filter(Question.test_id == test_id)

        # ---------- Strategy 1: avoid both (best — fresh question) ----------
        avoid = answered_in_attempt | recently_seen
        q1 = base.filter(
            ~Question.id.in_(avoid) if avoid else True,
            Question.difficulty == target_difficulty,
        ).first()
        if q1:
            return q1

        # ---------- Strategy 2: relax repeat prevention, still target difficulty ----------
        q2 = base.filter(
            ~Question.id.in_(answered_in_attempt) if answered_in_attempt else True,
            Question.difficulty == target_difficulty,
        ).first()
        if q2:
            return q2

        # ---------- Strategy 3: same exclusions, ANY difficulty ----------
        q3 = base.filter(
            ~Question.id.in_(answered_in_attempt) if answered_in_attempt else True
        ).first()
        return q3

    @staticmethod
    def determine_last_state(
        db: Session, attempt_id: int
    ) -> Tuple[str, Optional[bool]]:
        last = (
            db.query(Answer)
            .filter(Answer.attempt_id == attempt_id)
            .order_by(Answer.id.desc())
            .first()
        )
        if not last:
            return "medium", None
        return last.question.difficulty.value, last.is_correct