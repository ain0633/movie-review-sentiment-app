from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class MovieCreate(BaseModel):
    """요청 스키마 = 입력 방어. 신뢰할 수 없는 외부 입력을 입구에서 검증한다."""

    title: str = Field(min_length=1, max_length=200, description="영화 제목")
    release_date: date = Field(description="개봉일 (YYYY-MM-DD)")
    director: str = Field(min_length=1, max_length=100, description="감독")
    genre: str = Field(min_length=1, max_length=50, description="장르")
    poster_url: HttpUrl = Field(description="포스터 이미지 URL")


class MovieResponse(BaseModel):
    """응답 스키마 = 출력 계약. avg_score는 리뷰 감성 점수의 평균(리뷰 없으면 null)."""

    id: int
    title: str
    release_date: date
    director: str
    genre: str
    poster_url: str
    avg_score: float | None = Field(default=None, ge=0.0, le=1.0)
    review_count: int = 0
    created_at: datetime


class RatingResponse(BaseModel):
    movie_id: int
    avg_score: float | None
    review_count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class SentimentLabel(str, Enum):
    """Enum으로 선택지 제한 — 오타 라벨이 저장·응답되는 것을 입구에서 차단."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


class ReviewCreate(BaseModel):
    movie_id: int = Field(ge=1, description="리뷰 대상 영화 ID")
    author: str = Field(min_length=1, max_length=50, description="작성자 이름")
    content: str = Field(min_length=1, max_length=2000, description="리뷰 내용")


class ReviewResponse(BaseModel):
    id: int
    movie_id: int
    author: str
    content: str
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(ge=0.0, le=1.0, description="긍정 확률")
    created_at: datetime
