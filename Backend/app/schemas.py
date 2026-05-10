from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class RoleEnum(str, Enum):
    student = "student"
    admin = "admin"


class DifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# ========== USER ==========
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[RoleEnum] = RoleEnum.student


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ========== QUESTION ==========
class QuestionCreate(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str = Field(..., pattern="^[A-Da-d]$")
    difficulty: DifficultyEnum = DifficultyEnum.medium


class QuestionOut(BaseModel):
    """Public version (no correct answer leaked to students)."""
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    difficulty: DifficultyEnum

    class Config:
        from_attributes = True


class QuestionAdminOut(QuestionOut):
    correct_option: str
    test_id: int


# ========== TEST ==========
class TestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None


class TestOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    question_count: int = 0

    class Config:
        from_attributes = True


class TestDetailOut(TestOut):
    questions: List[QuestionAdminOut] = []


# ========== ATTEMPT / ADAPTIVE ==========
class AttemptStart(BaseModel):
    test_id: int


class AnswerSubmit(BaseModel):
    attempt_id: int
    question_id: int
    selected_option: str = Field(..., pattern="^[A-Da-d]$")
    time_taken: float = 0


class NextQuestionResponse(BaseModel):
    question: Optional[QuestionOut] = None
    finished: bool
    attempt_id: int


class AttemptOut(BaseModel):
    id: int
    user_id: int
    test_id: int
    test_title: Optional[str] = None
    score: float
    accuracy: float
    avg_difficulty: float
    attempt_time: float
    competency_level: Optional[str] = None
    predicted_level: Optional[str] = None
    completed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== RESULT ==========
class ResultOut(BaseModel):
    attempt_id: int
    score: float
    accuracy: float
    total_questions: int
    correct_answers: int
    competency_level: str
    predicted_level: Optional[str] = None
    avg_difficulty: float
    attempt_time: float
    recommendations: List[str]
    weak_areas: List[dict]


# ========== ML ==========
class PredictionRequest(BaseModel):
    accuracy: float
    avg_difficulty: float
    attempt_time: float


class PredictionResponse(BaseModel):
    predicted_level: str
    confidence: float
