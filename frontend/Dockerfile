# 로컬 통합 실행(docker compose)용 — 실제 배포는 Streamlit Cloud
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY pages/ pages/
COPY lib/ lib/
COPY .streamlit/config.toml .streamlit/config.toml

ENV PYTHONUNBUFFERED=1
RUN useradd -m appuser
USER appuser

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless", "true", "--server.address", "0.0.0.0"]
