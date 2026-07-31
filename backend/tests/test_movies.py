"""1단계 스모크 테스트 — 영화 CRUD + 평점 + 검증 실패 케이스.

실행: backend/ 에서  python tests/test_movies.py
"""
import os
import sys
import tempfile

# 임시 DB로 격리한 뒤 앱 임포트 (config가 env를 읽으므로 먼저 설정)
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

MOVIE = {
    "title": "인셉션",
    "release_date": "2010-07-21",
    "director": "크리스토퍼 놀란",
    "genre": "SF",
    "poster_url": "https://example.com/inception.jpg",
}

with TestClient(app) as client:  # with 블록이어야 lifespan(init_db) 실행됨
    # 헬스체크
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok", r.text

    # 등록
    r = client.post("/movies", json=MOVIE)
    assert r.status_code == 201, r.text
    movie_id = r.json()["id"]
    assert r.json()["avg_score"] is None and r.json()["review_count"] == 0

    # 입력 방어: 빈 제목·잘못된 URL → 422
    assert client.post("/movies", json={**MOVIE, "title": ""}).status_code == 422
    assert client.post("/movies", json={**MOVIE, "poster_url": "낫유알엘"}).status_code == 422

    # 조회
    assert len(client.get("/movies").json()) == 1
    assert client.get(f"/movies/{movie_id}").json()["title"] == "인셉션"
    assert client.get("/movies/999").status_code == 404

    # 평점 (리뷰 없음)
    r = client.get(f"/movies/{movie_id}/rating")
    assert r.status_code == 200 and r.json()["review_count"] == 0

    # 삭제
    assert client.delete(f"/movies/{movie_id}").status_code == 204
    assert client.delete(f"/movies/{movie_id}").status_code == 404
    assert client.get("/movies").json() == []

print("OK - 1단계 스모크 테스트 전부 통과")
