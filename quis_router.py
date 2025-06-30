from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import databases
import sqlalchemy
import uuid
import os
import asyncpg
from dotenv import load_dotenv
from auth.auth import get_current_user 
from datetime import datetime


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

database = databases.Database(DATABASE_URL, statement_cache_size=0)
metadata = sqlalchemy.MetaData()

quiz_results = sqlalchemy.Table(
    "quiz_results",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("level", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("score", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("total_questions", sqlalchemy.Integer, nullable=True), 
    sqlalchemy.Column("percentage", sqlalchemy.Numeric(5, 2), nullable=True),  
    sqlalchemy.Column("time_spent", sqlalchemy.Integer, nullable=True),        
    sqlalchemy.Column("answers", sqlalchemy.JSON, nullable=False),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.TIMESTAMP(timezone=True),
        server_default=sqlalchemy.text("timezone('utc', now())")
    ),
)

users = sqlalchemy.Table(  # kamu harus pastikan ada tabel `users` di database
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, nullable=False, unique=True),
)

router = APIRouter()


class AnswerDetail(BaseModel):
    question: str
    selected_option: str
    correct_option: str
    is_correct: bool

class QuizResultIn(BaseModel):
    level: str
    score: int
    total_questions: int
    percentage: float
    answers: List[AnswerDetail]
    time_spent: Optional[int] = None


class QuizResultOut(BaseModel):
    id: str
    level: str
    score: int
    total_questions: int  # <-- ini wajib, tapi datanya tidak ada
    percentage: float     # <-- ini juga wajib
    time_spent: int
    created_at: datetime


@router.on_event("startup")
async def startup():
    await database.connect()


@router.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@router.post("/quiz-results", response_model=QuizResultOut)
async def submit_quiz_result(
    quiz: QuizResultIn,
    current_user_email: str = Depends(get_current_user)
):
    # Ambil user_id dari email
    query_user = users.select().where(users.c.email == current_user_email)
    user = await database.fetch_one(query_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    quiz_id = str(uuid.uuid4())
    query_insert = quiz_results.insert().values(
        id=quiz_id,
        user_id=user["id"],
        level=quiz.level,
        score=quiz.score,
        total_questions=quiz.total_questions,
        percentage=quiz.percentage,
        time_spent=quiz.time_spent,
        answers=[answer.dict() for answer in quiz.answers],
    )

    try:
        await database.execute(query_insert)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    query_select = quiz_results.select().where(quiz_results.c.id == quiz_id)
    result = await database.fetch_one(query_select)

    return {
        "id": result["id"],
        "level": result["level"],
        "score": result["score"],
        "total_questions": result["total_questions"],
        "percentage": float(result["percentage"]),
        "time_spent": result["time_spent"],
        "created_at": result["created_at"],
    }


@router.get("/quiz-results/me", response_model=List[QuizResultOut])
async def get_my_quiz_results(current_user_email: str = Depends(get_current_user)):
    query_user = users.select().where(users.c.email == current_user_email)
    user = await database.fetch_one(query_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query_results = (
        quiz_results.select()
        .where(quiz_results.c.user_id == user["id"])
        .order_by(quiz_results.c.created_at.desc())
    )

    results = await database.fetch_all(query_results)

    return [
        QuizResultOut(
            id=str(r["id"]),
            level=r["level"],
            score=r["score"],
            total_questions=r["total_questions"] if r["total_questions"] is not None else 0,
            percentage=float(r["percentage"]) if r["percentage"] is not None else 0.0,
            time_spent=r["time_spent"] if r["time_spent"] is not None else 0,
            created_at=r["created_at"],
        )
        for r in results
    ]

@router.get("/quiz-results/has-taken/{level}", response_model=bool)
async def has_taken_quiz(level: str, current_user_email: str = Depends(get_current_user)):
    query_user = users.select().where(users.c.email == current_user_email)
    user = await database.fetch_one(query_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = (
        quiz_results.select()
        .where((quiz_results.c.user_id == user["id"]) & (quiz_results.c.level == level))
    )

    result = await database.fetch_one(query)
    return result is not None 

