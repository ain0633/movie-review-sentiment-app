"""3단계 스모크 테스트 — 리뷰 등록·감성분석·평점 반영·CASCADE.

실행: backend/ 에서  python tests/test_reviews.py  (실제 INT8 모델 로드, ~수 초)
"""
import os
import sys
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

MOVIE = {
    "title": "기생충",
    "release_date": "2019-05-30",
    "director": "봉준호",
    "genre": "드라마",
    "poster_url": "https://example.com/parasite.jpg",
}

with TestClient(app) as client:
    # 모델이 lifespan에서 로드됐는지
    assert client.get("/health").json()["model_loaded"] is True

    movie_id = client.post("/movies", json=MOVIE).json()["id"]

    # 긍정 리뷰 → positive, score >= 0.5
    r = client.post("/reviews", json={
        "movie_id": movie_id, "author": "아인", "content": "정말 최고의 영화! 감동적이고 여운이 길다."})
    assert r.status_code == 201, r.text
    pos = r.json()
    assert pos["sentiment_label"] == "positive" and pos["sentiment_score"] >= 0.5, pos

    # 부정 리뷰 → negative
    r = client.post("/reviews", json={
        "movie_id": movie_id, "author": "테스터", "content": "지루하고 돈 아까운 최악의 영화."})
    neg = r.json()
    assert neg["sentiment_label"] == "negative" and neg["sentiment_score"] < 0.5, neg

    # 없는 영화에 리뷰 → 404, 빈 내용 → 422
    assert client.post("/reviews", json={"movie_id": 999, "author": "a", "content": "b"}).status_code == 404
    assert client.post("/reviews", json={"movie_id": movie_id, "author": "a", "content": ""}).status_code == 422

    # 평균 평점 = 두 리뷰 점수의 평균
    rating = client.get(f"/movies/{movie_id}/rating").json()
    expected = (pos["sentiment_score"] + neg["sentiment_score"]) / 2
    assert rating["review_count"] == 2 and abs(rating["avg_score"] - expected) < 1e-6

    # 영화 목록에도 평점 반영
    m = client.get(f"/movies/{movie_id}").json()
    assert m["review_count"] == 2 and abs(m["avg_score"] - expected) < 1e-6

    # recent: 최신순 + limit
    for i in range(11):
        client.post("/reviews", json={"movie_id": movie_id, "author": "봇", "content": f"재미있어요 {i}"})
    recent = client.get("/reviews/recent").json()
    assert len(recent) == 10  # 기본 limit 10
    assert recent[0]["id"] > recent[-1]["id"]  # 최신(큰 id)부터

    # 영화별 필터
    assert all(rv["movie_id"] == movie_id for rv in client.get(f"/reviews?movie_id={movie_id}").json())

    # 리뷰 삭제 → 평점 재계산
    assert client.delete(f"/reviews/{neg['id']}").status_code == 204
    assert client.delete(f"/reviews/{neg['id']}").status_code == 404
    assert client.get(f"/movies/{movie_id}/rating").json()["review_count"] == 12

    # 영화 삭제 → 리뷰 CASCADE 삭제
    client.delete(f"/movies/{movie_id}")
    assert client.get("/reviews").json() == []

print("OK - 3단계 스모크 테스트 전부 통과")
