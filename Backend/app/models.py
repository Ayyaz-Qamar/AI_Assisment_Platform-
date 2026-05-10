"""
Database models. ORM ONLY — no ML or business logic here.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    admin = "admin"


class DifficultyEnum(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.student, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship(
        "TestAttempt", back_populates="user", cascade="all, delete-orphan"
    )


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship(
        "Question", back_populates="test", cascade="all, delete-orphan"
    )
    attempts = relationship(
        "TestAttempt", back_populates="test", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), index=True)
    text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)
    difficulty = Column(Enum(DifficultyEnum), default=DifficultyEnum.medium, index=True)

    test = relationship("Test", back_populates="questions")
    answers = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), index=True)
    score = Column(Float, default=0)
    accuracy = Column(Float, default=0)
    avg_difficulty = Column(Float, default=0)
    attempt_time = Column(Float, default=0)  # seconds
    competency_level = Column(String(50))
    predicted_level = Column(String(50))
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="attempts")
    test = relationship("Test", back_populates="attempts")
    answers = relationship(
        "Answer", back_populates="attempt", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), index=True)
    selected_option = Column(String(1))
    is_correct = Column(Boolean, default=False)
    time_taken = Column(Float, default=0)
    answered_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("TestAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
