from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.adaptive_engine import AdaptiveEngine
from app.ai.scoring import calculate_score, get_competency_level
from app.database import get_db
from app.ml.predict import predict_level
from app.models import Answer, Question, Test, TestAttempt, User
from app.schemas import AnswerSubmit, AttemptStart, NextQuestionResponse, QuestionOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/adaptive", tags=["Adaptive Test"])

MAX_QUESTIONS_PER_ATTEMPT = 10


@router.post("/start")
def start_attempt(
    payload: AttemptStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = db.query(Test).filter(Test.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    total_q = db.query(Question).filter(Question.test_id == payload.test_id).count()
    if total_q == 0:
        raise HTTPException(status_code=400, detail="Test has no questions yet")

    attempt = TestAttempt(
        user_id=current_user.id,
        test_id=payload.test_id,
        started_at=datetime.utcnow(),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    first_q = AdaptiveEngine.get_next_question(
        db, payload.test_id, attempt.id, "medium", user_id=current_user.id
    )

    return {
        "attempt_id": attempt.id,
        "test_id": payload.test_id,
        "test_title": test.title,
        "total_questions": total_q,
        "max_questions": min(MAX_QUESTIONS_PER_ATTEMPT, total_q),
        "question": QuestionOut.model_validate(first_q) if first_q else None,
    }


@router.post("/submit-answer", response_model=NextQuestionResponse)
def submit_answer(
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = (
        db.query(TestAttempt)
        .filter(
            TestAttempt.id == payload.attempt_id,
            TestAttempt.user_id == current_user.id,
        )
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.completed:
        raise HTTPException(status_code=400, detail="Attempt already completed")

    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.test_id != attempt.test_id:
        raise HTTPException(status_code=400, detail="Question doesn't belong to this test")

    selected = payload.selected_option.upper()
    is_correct = selected == question.correct_option.upper()

    db.add(Answer(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_option=selected,
        is_correct=is_correct,
        time_taken=payload.time_taken,
    ))
    db.commit()

    # Adaptive: choose next difficulty
    next_difficulty = AdaptiveEngine.get_next_difficulty(
        question.difficulty.value, is_correct
    )

    answered_count = (
        db.query(Answer).filter(Answer.attempt_id == attempt.id).count()
    )
    total_q = db.query(Question).filter(Question.test_id == attempt.test_id).count()
    cap = min(MAX_QUESTIONS_PER_ATTEMPT, total_q)

    if answered_count >= cap:
        return _finalize_attempt(db, attempt)

    next_q = AdaptiveEngine.get_next_question(
        db, attempt.test_id, attempt.id, next_difficulty, user_id=current_user.id
    )
    if not next_q:
        return _finalize_attempt(db, attempt)

    return NextQuestionResponse(
        question=QuestionOut.model_validate(next_q),
        finished=False,
        attempt_id=attempt.id,
    )


def _finalize_attempt(db: Session, attempt: TestAttempt) -> NextQuestionResponse:
    answers = db.query(Answer).filter(Answer.attempt_id == attempt.id).all()
    pairs = [(a.is_correct, a.question.difficulty.value) for a in answers]

    score, accuracy, avg_diff = calculate_score(pairs)
    total_time = sum(a.time_taken for a in answers)
    competency = get_competency_level(score)

    try:
        predicted, _conf = predict_level(accuracy, avg_diff, total_time)
    except Exception:
        predicted = competency

    attempt.score = score
    attempt.accuracy = accuracy
    attempt.avg_difficulty = avg_diff
    attempt.attempt_time = total_time
    attempt.competency_level = competency
    attempt.predicted_level = predicted
    attempt.completed = True
    attempt.completed_at = datetime.utcnow()
    db.commit()

    return NextQuestionResponse(question=None, finished=True, attempt_id=attempt.id)