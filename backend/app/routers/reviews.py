import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.database import get_db
from app.ml import predictor
from app.schemas import ReviewCreate, ReviewResponse
from app.services import movie_service, review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=201,
             summary="리뷰 등록 (감성 분석 자동 실행)")
async def create_review(body: ReviewCreate, conn: sqlite3.Connection = Depends(get_db)):
    if movie_service.get_movie(conn, body.movie_id) is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    # 동기 ONNX 추론을 스레드 풀로 위임 — 이벤트 루프 블로킹 방지
    score = await run_in_threadpool(predictor.predict, body.content)
    label = "positive" if score >= 0.5 else "negative"
    return review_service.create_review(conn, body.model_dump(), label, score)


# 고정 경로(/recent)는 매개변수 경로(/{review_id})보다 위에 정의
@router.get("/recent", response_model=list[ReviewResponse], summary="최근 리뷰 N개")
def recent_reviews(
    limit: int = Query(default=10, ge=1, le=50),
    conn: sqlite3.Connection = Depends(get_db),
):
    return review_service.list_reviews(conn, limit=limit)


@router.get("", response_model=list[ReviewResponse], summary="리뷰 조회 (전체/영화별)")
def list_reviews(
    movie_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_db),
):
    return review_service.list_reviews(conn, movie_id=movie_id, limit=limit)


@router.delete("/{review_id}", status_code=204, summary="리뷰 삭제")
def delete_review(review_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not review_service.delete_review(conn, review_id):
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
