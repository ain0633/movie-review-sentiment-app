import sqlite3
from contextlib import closing
from pathlib import Path

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    release_date TEXT NOT NULL,
    director     TEXT NOT NULL,
    genre        TEXT NOT NULL,
    poster_url   TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id        INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    author          TEXT NOT NULL,
    content         TEXT NOT NULL,
    sentiment_label TEXT NOT NULL,
    sentiment_score REAL NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def init_db() -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    # sqlite3의 with는 트랜잭션만 관리하고 연결은 닫지 않음 — closing으로 명시적 종료
    with closing(sqlite3.connect(settings.db_path)) as conn:
        conn.executescript(SCHEMA)


def get_db():
    """요청마다 새 연결을 열고 끝나면 닫는 FastAPI 의존성.

    check_same_thread=False 필수: async 엔드포인트에서는 의존성(스레드풀)과
    엔드포인트 본문(이벤트 루프)이 다른 스레드에서 실행되므로, 기본값이면
    "SQLite objects created in a thread can only be used in that same thread" 에러.
    연결이 요청 하나에만 속해 동시 사용이 없으므로 해제해도 안전하다.
    FK 제약(ON DELETE CASCADE)은 연결마다 PRAGMA로 켜야 동작한다.
    """
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능한 dict 유사 행
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
