"""백엔드 API 호출 단일 창구 — 모든 페이지는 이 모듈을 통해서만 통신한다.

데이터는 전부 백엔드에서 관리(미션 제약). Streamlit 쪽 저장 기능은 쓰지 않는다.
"""
import requests
import streamlit as st

try:
    BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")
except Exception:  # secrets 파일이 아예 없는 환경(로컬 기본값으로 동작)
    BACKEND_URL = "http://localhost:8000"
TIMEOUT = 30  # 감성 분석 포함 여유


def require_backend() -> None:
    """페이지 최상단에서 호출 — 백엔드가 죽어 있으면 이하 렌더링 중단."""
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5).json()
    except requests.RequestException:
        st.error(f"백엔드({BACKEND_URL})에 연결할 수 없습니다. 서버를 먼저 실행해주세요.\n\n"
                 "`backend/` 폴더에서 `uvicorn app.main:app` 실행")
        st.stop()
    if not health.get("model_loaded"):
        st.warning("백엔드는 켜져 있지만 감성 분석 모델이 아직 로드되지 않았습니다.")
        st.stop()


@st.cache_data(ttl=30)
def list_movies() -> list[dict]:
    r = requests.get(f"{BACKEND_URL}/movies", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def recent_reviews(limit: int = 10) -> list[dict]:
    r = requests.get(f"{BACKEND_URL}/reviews/recent", params={"limit": limit}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def create_movie(payload: dict) -> dict:
    r = requests.post(f"{BACKEND_URL}/movies", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    st.cache_data.clear()  # 목록 캐시 무효화 — 새 영화가 바로 보이게
    return r.json()


def create_review(payload: dict) -> dict:
    r = requests.post(f"{BACKEND_URL}/reviews", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    st.cache_data.clear()  # 평점·리뷰 목록 갱신
    return r.json()


def http_error_message(e: requests.HTTPError) -> str:
    """백엔드 오류 응답을 사람이 읽을 문장으로. 422의 detail은 리스트라 펼쳐준다."""
    try:
        detail = e.response.json().get("detail", e.response.text)
    except ValueError:
        return e.response.text
    if isinstance(detail, list):  # FastAPI 검증 오류: [{loc, msg, ...}, ...]
        return "; ".join(
            f"{'.'.join(str(p) for p in d.get('loc', [])[1:])}: {d.get('msg', '')}" for d in detail
        )
    return str(detail)


def sentiment_badge(label: str, score: float) -> str:
    """감성 결과를 이모지 뱃지 문자열로 — 여러 페이지에서 공통 사용."""
    if label == "positive":
        return f"😊 긍정 ({score:.0%})"
    return f"😞 부정 (긍정확률 {score:.0%})"
