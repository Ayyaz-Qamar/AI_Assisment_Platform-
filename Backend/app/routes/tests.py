from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Question, Test, User
from app.schemas import (
    QuestionAdminOut, QuestionCreate, TestCreate, TestDetailOut, TestOut,
)
from app.utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/tests", tags=["Tests"])


@router.get("/", response_model=List[TestOut])
def list_tests(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    # Single grouped query — no N+1
    rows = (
        db.query(Test, func.count(Question.id).label("qc"))
        .outerjoin(Question, Question.test_id == Test.id)
        .group_by(Test.id)
        .order_by(Test.created_at.desc())
        .all()
    )
    out: List[TestOut] = []
    for test, qc in rows:
        item = TestOut.model_validate(test)
        item.question_count = int(qc or 0)
        out.append(item)
    return out


@router.get("/{test_id}", response_model=TestDetailOut)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    # Eager-load questions to avoid N+1 (admin view, includes correct_option)
    test = (
        db.query(Test)
        .options(joinedload(Test.questions))
        .filter(Test.id == test_id)
        .first()
    )
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    detail = TestDetailOut.model_validate(test)
    detail.question_count = len(test.questions)
    return detail


@router.post("/", response_model=TestOut, status_code=201)
def create_test(
    payload: TestCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    test = Test(**payload.model_dump(), created_by=admin.id)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.delete("/{test_id}", status_code=200)
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    db.delete(test)
    db.commit()
    return {"message": "Test deleted"}


# ---- Questions ----
@router.post("/{test_id}/questions", response_model=QuestionAdminOut, status_code=201)
def add_question(
    test_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not db.query(Test).filter(Test.id == test_id).first():
        raise HTTPException(status_code=404, detail="Test not found")

    data = payload.model_dump()
    data["correct_option"] = data["correct_option"].upper()
    q = Question(test_id=test_id, **data)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/{test_id}/questions", response_model=List[QuestionAdminOut])
def list_questions(
    test_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(Question).filter(Question.test_id == test_id).all()


@router.delete("/questions/{question_id}", status_code=200)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Question deleted"}
