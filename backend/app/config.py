from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경변수(.env)로 덮어쓸 수 있는 앱 설정. 민감값은 코드에 하드코딩하지 않는다."""

    db_path: str = str(Path(__file__).resolve().parent.parent / "data" / "movies.db")
    allowed_origins: list[str] = ["http://localhost:8501"]  # Streamlit 로컬 기본 포트
    model_path: str = str(
        Path(__file__).resolve().parent.parent / "ml_assets" / "sentiment_int8.onnx"
    )

    class Config:
        env_file = ".env"


settings = Settings()
