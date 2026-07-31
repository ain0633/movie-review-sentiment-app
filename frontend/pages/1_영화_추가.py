"""영화 추가 — st.form으로 묶어 제출 시에만 API 호출."""
import datetime

import requests
import streamlit as st

from lib import api_client

st.set_page_config(page_title="영화 추가", page_icon="➕")
api_client.require_backend()

st.title("➕ 영화 추가")

with st.form("movie_form"):
    title = st.text_input("제목 *")
    release_date = st.date_input(
        "개봉일 *", value=datetime.date.today(),
        min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(),
    )
    director = st.text_input("감독 *")
    genre = st.text_input("장르 *", placeholder="예: 드라마, SF, 로맨스")
    poster_url = st.text_input("포스터 URL *", placeholder="https://... (나무위키 이미지 주소 참고)")
    submitted = st.form_submit_button("등록", type="primary")

if submitted:
    if not all([title.strip(), director.strip(), genre.strip(), poster_url.strip()]):
        st.error("모든 항목을 입력해주세요.")
    else:
        try:
            movie = api_client.create_movie({
                "title": title.strip(),
                "release_date": release_date.isoformat(),
                "director": director.strip(),
                "genre": genre.strip(),
                "poster_url": poster_url.strip(),
            })
            st.success(f"등록 완료: **{movie['title']}** (ID {movie['id']})")
            st.image(movie["poster_url"], width=200)
        except requests.HTTPError as e:
            st.error(f"등록 실패: {api_client.http_error_message(e)}")
