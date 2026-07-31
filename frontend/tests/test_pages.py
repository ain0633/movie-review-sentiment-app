"""4단계 스모크 테스트 — AppTest로 4개 페이지 실제 실행 + 리뷰 등록 풀 플로우.

전제: 백엔드가 localhost:8000에서 모델 로드 완료 상태로 실행 중.
실행: frontend/ 에서  python tests/test_pages.py
"""
import sys
from pathlib import Path

import requests
from streamlit.testing.v1 import AppTest

FRONT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FRONT))
BASE = "http://localhost:8000"

# 백엔드 살아있는지 먼저 확인
assert requests.get(f"{BASE}/health", timeout=5).json()["model_loaded"], "백엔드를 먼저 실행하세요"

# 테스트 데이터 초기화: 영화 하나 등록
movie = requests.post(f"{BASE}/movies", json={
    "title": "테스트영화", "release_date": "2024-01-01", "director": "감독",
    "genre": "드라마", "poster_url": "https://example.com/p.jpg"}).json()

def run(page):
    at = AppTest.from_file(str(FRONT / page))
    at.secrets["BACKEND_URL"] = BASE
    return at.run(timeout=60)

# 1) 메인: 영화 목록 렌더링 + 영화 제목 표시 (왓챠풍 HTML 카드)
at = run("app.py")
assert not at.exception, at.exception
grid = " ".join(str(md.value) for md in at.markdown)
assert "테스트영화" in grid, "영화 카드 미표시"
assert "평균★" in grid or "리뷰 없음" in grid, "평점 영역 미표시"
print("1) 영화 목록 페이지 OK")

# 1-1) XSS 방어: 악성 제목이 이스케이프되어 렌더링되는지
# 주의: api_client.create_movie를 써야 목록 캐시(ttl=30)가 무효화됨 (requests 직접 호출 시 캐시 미스매치)
from lib import api_client  # noqa: E402

evil = api_client.create_movie({
    "title": "<script>alert(1)</script>", "release_date": "2024-01-01", "director": "d",
    "genre": "g", "poster_url": "https://example.com/x.jpg"})
at = run("app.py")
grid = " ".join(str(md.value) for md in at.markdown)
assert "<script>" not in grid and "&lt;script&gt;" in grid, "XSS 이스케이프 실패!"
requests.delete(f"{BASE}/movies/{evil['id']}")
import streamlit as st  # noqa: E402

st.cache_data.clear()  # 삭제도 캐시 밖에서 했으니 다음 테스트를 위해 비움
print("1-1) XSS 이스케이프 OK")

# 2) 영화 추가 페이지: 렌더링 + 빈 제출 시 에러 표시
at = run("pages/1_영화_추가.py")
assert not at.exception
at.button[0].click()
at.run(timeout=60)
assert at.error, "빈 폼 제출 시 에러 안내가 없음"
print("2) 영화 추가 페이지 OK (빈 폼 방어 포함)")

# 3) 리뷰 등록 페이지: 폼 작성 → 제출 → 감성 결과 표시 (풀 플로우)
at = run("pages/2_리뷰_등록.py")
assert not at.exception
at.selectbox[0].select(next(m for m in at.selectbox[0].options if "테스트영화" in m))
at.text_input[0].input("아인")
at.text_area[0].input("정말 감동적이고 최고의 영화였습니다!")
at.button[0].click()
at.run(timeout=60)
assert not at.exception, at.exception
assert at.success, "등록 성공 메시지 없음"
assert any("긍정" in str(md.value) for md in at.markdown), "감성 분석 결과 미표시"
print("3) 리뷰 등록 풀 플로우 OK (감성 결과 표시 확인)")

# 4) 최근 리뷰 페이지: 방금 등록한 리뷰 표시
at = run("pages/3_최근_리뷰.py")
assert not at.exception
body = " ".join(str(md.value) for md in at.markdown)
assert "영화 ID" in body, "리뷰 항목 미표시"
print("4) 최근 리뷰 페이지 OK")

# 정리
requests.delete(f"{BASE}/movies/{movie['id']}")
print("\nOK - 4단계 스모크 테스트 전부 통과")
