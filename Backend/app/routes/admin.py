from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Question, RoleEnum, Test, TestAttempt, User
from app.utils.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """
    Single grouped query — no N+1.
    """
    sub = (
        db.query(
            TestAttempt.user_id.label("uid"),
            func.count(TestAttempt.id).label("attempts"),
            func.avg(TestAttempt.score).label("avg_score"),
        )
        .filter(TestAttempt.completed.is_(True))
        .group_by(TestAttempt.user_id)
        .subquery()
    )

    rows = (
        db.query(
            User,
            func.coalesce(sub.c.attempts, 0).label("attempts"),
            func.coalesce(sub.c.avg_score, 0).label("avg_score"),
        )
        .outerjoin(sub, sub.c.uid == User.id)
        .all()
    )

    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "created_at": u.created_at.isoformat(),
            "total_attempts": int(attempts),
            "avg_score": round(float(avg_score), 2),
        }
        for u, attempts, avg_score in rows
    ]


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_students = (
        db.query(func.count(User.id)).filter(User.role == RoleEnum.student).scalar() or 0
    )
    total_tests = db.query(func.count(Test.id)).scalar() or 0
    total_questions = db.query(func.count(Question.id)).scalar() or 0
    total_attempts = (
        db.query(func.count(TestAttempt.id))
        .filter(TestAttempt.completed.is_(True))
        .scalar()
        or 0
    )
    avg_score = (
        db.query(func.avg(TestAttempt.score))
        .filter(TestAttempt.completed.is_(True))
        .scalar()
        or 0
    )

    dist_rows = (
        db.query(TestAttempt.competency_level, func.count(TestAttempt.id))
        .filter(TestAttempt.completed.is_(True))
        .group_by(TestAttempt.competency_level)
        .all()
    )

    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_tests": total_tests,
        "total_questions": total_questions,
        "total_attempts": total_attempts,
        "avg_score": round(float(avg_score), 2),
        "level_distribution": {
            (lvl or "Unknown"): count for lvl, count in dist_rows
        },
    }


@router.get("/users/{user_id}/performance")
def user_performance(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    attempts = (
        db.query(TestAttempt)
        .options(joinedload(TestAttempt.test))
        .filter(
            TestAttempt.user_id == user_id,
            TestAttempt.completed.is_(True),
        )
        .order_by(TestAttempt.completed_at.desc())
        .all()
    )
    return [
        {
            "attempt_id": a.id,
            "test_title": a.test.title if a.test else "N/A",
            "score": a.score,
            "accuracy": a.accuracy,
            "level": a.competency_level,
            "predicted_level": a.predicted_level,
            "date": a.completed_at.isoformat() if a.completed_at else None,
        }
        for a in attempts
    ]
