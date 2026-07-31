"""최근 리뷰 — 최근 10개: 영화 ID, 등록일, 리뷰 내용, 감성 분석 결과."""
import streamlit as st

from lib import api_client

st.set_page_config(page_title="최근 리뷰", page_icon="🕘")
api_client.require_backend()

st.title("🕘 최근 리뷰 10개")

reviews = api_client.recent_reviews(limit=10)
if not reviews:
    st.info("아직 등록된 리뷰가 없습니다. **리뷰 등록** 페이지에서 첫 리뷰를 남겨보세요!")
    st.stop()

# 영화 ID → 제목 매핑 (표시는 ID가 요구사항이지만 제목도 함께 보여주면 읽기 쉬움)
titles = {m["id"]: m["title"] for m in api_client.list_movies()}

for rv in reviews:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**영화 ID {rv['movie_id']}** — {titles.get(rv['movie_id'], '(삭제된 영화)')}")
            st.write(rv["content"])
            st.caption(f"{rv['author']} · {rv['created_at']}")
        with right:
            st.markdown(api_client.sentiment_badge(rv["sentiment_label"], rv["sentiment_score"]))
