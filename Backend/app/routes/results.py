from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.ai.recommendation import RecommendationEngine
from app.database import get_db
from app.models import RoleEnum, TestAttempt, User
from app.schemas import AttemptOut, ResultOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/results", tags=["Results & Analytics"])


@router.get("/me", response_model=List[AttemptOut])
def my_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempts = (
        db.query(TestAttempt)
        .options(joinedload(TestAttempt.test))
        .filter(
            TestAttempt.user_id == current_user.id,
            TestAttempt.completed.is_(True),
        )
        .order_by(TestAttempt.completed_at.desc())
        .all()
    )
    # Enrich with test_title
    result = []
    for a in attempts:
        out = AttemptOut.model_validate(a)
        out.test_title = a.test.title if a.test else None
        result.append(out)
    return result


@router.get("/{attempt_id}", response_model=ResultOut)
def get_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = (
        db.query(TestAttempt)
        .options(joinedload(TestAttempt.answers))
        .filter(TestAttempt.id == attempt_id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Access denied")

    total = len(attempt.answers)
    correct = sum(1 for a in attempt.answers if a.is_correct)
    weak, recs = RecommendationEngine.analyze_weak_areas(db, attempt_id)

    return ResultOut(
        attempt_id=attempt.id,
        score=attempt.score,
        accuracy=attempt.accuracy,
        total_questions=total,
        correct_answers=correct,
        competency_level=attempt.competency_level or "Unknown",
        predicted_level=attempt.predicted_level,
        avg_difficulty=attempt.avg_difficulty,
        attempt_time=attempt.attempt_time,
        recommendations=recs,
        weak_areas=weak,
    )


@router.get("/me/analytics")
def my_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempts = (
        db.query(TestAttempt)
        .filter(
            TestAttempt.user_id == current_user.id,
            TestAttempt.completed.is_(True),
        )
        .order_by(TestAttempt.completed_at.asc())
        .all()
    )

    if not attempts:
        return {
            "total_attempts": 0,
            "avg_score": 0,
            "avg_accuracy": 0,
            "level_distribution": {},
            "score_history": [],
        }

    avg_score = sum(a.score for a in attempts) / len(attempts)
    avg_acc = sum(a.accuracy for a in attempts) / len(attempts)

    dist = {}
    for a in attempts:
        lvl = a.competency_level or "Unknown"
        dist[lvl] = dist.get(lvl, 0) + 1

    history = [
        {
            "attempt_id": a.id,
            "score": a.score,
            "accuracy": a.accuracy,
            "level": a.competency_level,
            "date": a.completed_at.isoformat() if a.completed_at else None,
        }
        for a in attempts
    ]

    return {
        "total_attempts": len(attempts),
        "avg_score": round(avg_score, 2),
        "avg_accuracy": round(avg_acc, 2),
        "level_distribution": dist,
        "score_history": history,
    }
