from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import databases
import sqlalchemy
import uuid
import os
import asyncpg
from dotenv import load_dotenv
from auth.auth import get_current_user  # pastikan get_current_user mengembalikan email pengguna

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


class AnswerItem(BaseModel):
    question_id: str
    selected_option: str
    is_correct: bool


class QuizResultIn(BaseModel):
    level: str
    score: int
    answers: List[AnswerItem]


class QuizResultOut(QuizResultIn):
    id: str
    user_id: str
    created_at: Optional[str]


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
        answers=[answer.dict() for answer in quiz.answers],
    )

    try:
        await database.execute(query_insert)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": quiz_id,
        "user_id": str(user["id"]),   # convert ke string
        "level": quiz.level,
        "score": quiz.score,
        "answers": quiz.answers,
        "created_at": None,
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
            id=str(r["id"]),           # convert ke string
            user_id=str(r["user_id"]), # convert ke string
            level=r["level"],
            score=r["score"],
            answers=r["answers"],
            created_at=r["created_at"].isoformat() if r["created_at"] else None,
        )
        for r in results
    ]
