"""앱 조립만 담당 — 라우터 등록, 미들웨어, lifespan."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.ml.loader import model_manager
from app.routers import movies, reviews
from app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()                              # startup: 테이블 생성
    model_manager.load(settings.model_path)  # startup: ONNX 모델 1회 로드
    yield
    model_manager.unload()                 # shutdown: 리소스 해제


app = FastAPI(
    title="영화 리뷰 감성 분석 API",
    description="영화 정보·리뷰를 관리하고 리뷰 감성을 자동 분석하는 미션 18 백엔드",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # 와일드카드 금지 — 프론트 도메인만
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(reviews.router)


@app.get("/health", response_model=HealthResponse, tags=["System"], summary="헬스체크")
def health():
    return {"status": "ok", "model_loaded": model_manager.loaded}
