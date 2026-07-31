"""영화 비즈니스 로직 — FastAPI에 의존하지 않는 순수 Python (재사용 가능 계층).

모든 쿼리는 파라미터화 쿼리(? 플레이스홀더)만 사용한다. f-string 포매팅 금지.
"""
import sqlite3

# 영화 + 평균 평점(리뷰 감성 점수 AVG)을 한 번에 가져오는 공통 SELECT
_SELECT_WITH_RATING = """
SELECT m.*, AVG(r.sentiment_score) AS avg_score, COUNT(r.id) AS review_count
FROM movies m
LEFT JOIN reviews r ON r.movie_id = m.id
"""


def create_movie(conn: sqlite3.Connection, data: dict) -> dict:
    cur = conn.execute(
        "INSERT INTO movies (title, release_date, director, genre, poster_url) "
        "VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["release_date"], data["director"], data["genre"], data["poster_url"]),
    )
    conn.commit()
    return get_movie(conn, cur.lastrowid)


def list_movies(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(_SELECT_WITH_RATING + " GROUP BY m.id ORDER BY m.id DESC").fetchall()
    return [dict(row) for row in rows]


def get_movie(conn: sqlite3.Connection, movie_id: int) -> dict | None:
    row = conn.execute(
        _SELECT_WITH_RATING + " WHERE m.id = ? GROUP BY m.id", (movie_id,)
    ).fetchone()
    return dict(row) if row else None


def delete_movie(conn: sqlite3.Connection, movie_id: int) -> bool:
    cur = conn.execute("DELETE FROM movies WHERE id = ?", (movie_id,))  # 리뷰는 FK CASCADE로 삭제
    conn.commit()
    return cur.rowcount > 0


def get_rating(conn: sqlite3.Connection, movie_id: int) -> dict:
    row = conn.execute(
        "SELECT AVG(sentiment_score) AS avg_score, COUNT(id) AS review_count "
        "FROM reviews WHERE movie_id = ?",
        (movie_id,),
    ).fetchone()
    return {"movie_id": movie_id, "avg_score": row["avg_score"], "review_count": row["review_count"]}
