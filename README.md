# 미션 18 — 영화 리뷰 감성 분석 웹 서비스 (5팀 이아인)

Streamlit(프론트) + FastAPI(백엔드) + ONNX INT8 감성 분석 모델(KoELECTRA-small, NSMC).
설계 근거는 [기술문서.md](기술문서.md), 단계별 학습 정리는 [학습자료/](학습자료/) 참고.

## 로컬 실행

```bash
# 1) 백엔드 (모델 파일이 없으면 먼저: python scripts/export_onnx.py — torch/transformers 필요)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000        # http://localhost:8000/docs

# 2) 시드 데이터 (선택 — 영화 3개 + 리뷰 33개)
python scripts/seed_db.py

# 3) 프론트엔드 (새 터미널)
cd frontend
pip install -r requirements.txt
streamlit run app.py                    # http://localhost:8501
```

## Docker (통합 실행)

```bash
docker compose up --build               # backend 모델 로드 완료 후 frontend 기동
```

## 테스트

```bash
cd backend  && python tests/test_movies.py && python tests/test_reviews.py
cd frontend && python tests/test_pages.py   # 백엔드 실행 중이어야 함
```

## 구조

```
backend/   FastAPI — routers(HTTP) → services(로직) → SQLite / ml(ONNX 추론)
frontend/  Streamlit — app.py(영화 그리드) + pages/(추가·리뷰·최근) + lib/api_client.py
```
