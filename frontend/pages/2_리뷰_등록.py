"""리뷰 등록 — 영화 선택 후 작성, 제출하면 감성 분석 결과가 바로 표시된다."""
import requests
import streamlit as st

from lib import api_client

st.set_page_config(page_title="리뷰 등록", page_icon="✍️")
api_client.require_backend()

st.title("✍️ 리뷰 등록")

movies = api_client.list_movies()
if not movies:
    st.info("먼저 **영화 추가** 페이지에서 영화를 등록해주세요.")
    st.stop()

with st.form("review_form"):
    movie = st.selectbox(
        "영화 선택 *", movies,
        format_func=lambda m: f"{m['title']} ({m['release_date'][:4]})",
    )
    author = st.text_input("작성자 이름 *")
    content = st.text_area("리뷰 내용 *", height=150,
                           placeholder="영화를 보고 느낀 점을 자유롭게 적어주세요.")
    submitted = st.form_submit_button("리뷰 등록", type="primary")

if submitted:
    if not author.strip() or not content.strip():
        st.error("작성자 이름과 리뷰 내용을 입력해주세요.")
    else:
        try:
            with st.spinner("감성 분석 중..."):
                review = api_client.create_review({
                    "movie_id": movie["id"],
                    "author": author.strip(),
                    "content": content.strip(),
                })
            st.success("리뷰가 등록되었습니다!")
            st.markdown(
                f"### AI 감성 분석 결과: "
                f"{api_client.sentiment_badge(review['sentiment_label'], review['sentiment_score'])}"
            )
        except requests.HTTPError as e:
            st.error(f"등록 실패: {api_client.http_error_message(e)}")
