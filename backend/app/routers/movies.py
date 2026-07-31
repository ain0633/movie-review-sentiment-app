import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.schemas import MovieCreate, MovieResponse, RatingResponse
from app.services import movie_service

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.post("", response_model=MovieResponse, status_code=201, summary="영화 등록")
def create_movie(body: MovieCreate, conn: sqlite3.Connection = Depends(get_db)):
    data = body.model_dump()
    data["release_date"] = data["release_date"].isoformat()
    data["poster_url"] = str(data["poster_url"])  # HttpUrl -> str
    return movie_service.create_movie(conn, data)


@router.get("", response_model=list[MovieResponse], summary="전체 영화 조회 (평균 평점 포함)")
def list_movies(conn: sqlite3.Connection = Depends(get_db)):
    return movie_service.list_movies(conn)


@router.get("/{movie_id}", response_model=MovieResponse, summary="특정 영화 조회")
def get_movie(movie_id: int, conn: sqlite3.Connection = Depends(get_db)):
    movie = movie_service.get_movie(conn, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie


@router.delete("/{movie_id}", status_code=204, summary="영화 삭제 (리뷰 연쇄 삭제)")
def delete_movie(movie_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if not movie_service.delete_movie(conn, movie_id):
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")


@router.get("/{movie_id}/rating", response_model=RatingResponse, summary="평균 평점 조회")
def get_rating(movie_id: int, conn: sqlite3.Connection = Depends(get_db)):
    if movie_service.get_movie(conn, movie_id) is None:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie_service.get_rating(conn, movie_id)
