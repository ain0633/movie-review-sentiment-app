"""리뷰 비즈니스 로직 — 순수 Python. 감성 결과는 라우터에서 계산해 넘겨받는다."""
import sqlite3


def create_review(
    conn: sqlite3.Connection, data: dict, sentiment_label: str, sentiment_score: float
) -> dict:
    cur = conn.execute(
        "INSERT INTO reviews (movie_id, author, content, sentiment_label, sentiment_score) "
        "VALUES (?, ?, ?, ?, ?)",
        (data["movie_id"], data["author"], data["content"], sentiment_label, sentiment_score),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_reviews(conn: sqlite3.Connection, movie_id: int | None = None, limit: int = 100) -> list[dict]:
    if movie_id is None:
        rows = conn.execute(
            "SELECT * FROM reviews ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE movie_id = ? ORDER BY id DESC LIMIT ?",
            (movie_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_review(conn: sqlite3.Connection, review_id: int) -> bool:
    cur = conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    return cur.rowcount > 0
