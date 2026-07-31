"""메인 페이지 — 영화 목록. 왓챠피디아풍 포스터 그리드 (제목 · 포스터 · 평균 평점)."""
import html

import streamlit as st

from lib import api_client

st.set_page_config(page_title="영화 리뷰 감성 분석", page_icon="🎬", layout="wide")
api_client.require_backend()

st.title("🎬 영화 리뷰 감성 분석")
st.caption("리뷰를 남기면 AI가 자동으로 긍정/부정을 분석합니다. 평점 = 리뷰들의 긍정 확률 평균(5점 환산).")

movies = api_client.list_movies()

if not movies:
    # 빈 상태 대응 — 빈 화면 대신 다음 행동 안내
    st.info("아직 등록된 영화가 없습니다. 왼쪽 사이드바의 **영화 추가** 페이지에서 첫 영화를 등록해보세요!")
    st.stop()

COLS = 6  # 왓챠피디아처럼 한 줄 6개


def movie_card(movie: dict) -> str:
    """포스터·제목·별점 카드 HTML. 고정 템플릿 + 사용자 입력은 전부 escape (XSS 방어)."""
    title = html.escape(movie["title"])
    poster = html.escape(movie["poster_url"], quote=True)
    meta = html.escape(f"{movie['director']} · {movie['genre']}")
    if movie["avg_score"] is not None:
        stars = round(movie["avg_score"] * 5, 1)  # 긍정확률 0~1 → 별점 5점 환산
        rating = (f'<span style="color:#ff2f6e;font-weight:600;">'
                  f'평균★{stars}</span>'
                  f'<span style="color:#8a8d93;"> · 리뷰 {movie["review_count"]}</span>')
    else:
        rating = '<span style="color:#8a8d93;">리뷰 없음</span>'
    return f"""
    <div style="margin-bottom:1.4rem;">
      <img src="{poster}" alt="{title} 포스터" onerror="this.src='https://placehold.co/400x600?text=No+Poster'"
           style="width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:6px;background:#1e2023;">
      <div style="font-weight:600;margin-top:.5rem;line-height:1.3;">{title}</div>
      <div style="font-size:.78rem;color:#8a8d93;margin:.15rem 0;">{meta}</div>
      <div style="font-size:.85rem;">{rating}</div>
    </div>"""


for row_start in range(0, len(movies), COLS):
    cols = st.columns(COLS)
    for col, movie in zip(cols, movies[row_start:row_start + COLS]):
        with col:
            st.markdown(movie_card(movie), unsafe_allow_html=True)
