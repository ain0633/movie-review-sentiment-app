# CPU 서빙 → 최소 OS 레이어의 slim 베이스
FROM python:3.11-slim

WORKDIR /app

# 변경 빈도 낮은 의존성 설치를 위로 — 코드만 바뀌면 이 레이어는 캐시 재사용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 자주 바뀌는 코드·모델은 아래에
COPY app/ app/
COPY ml_assets/sentiment_int8.onnx ml_assets/
COPY ml_assets/tokenizer.json ml_assets/

# 로그 실시간 출력(버퍼링 끔) + 비root 사용자로 실행
ENV PYTHONUNBUFFERED=1
RUN useradd -m appuser && mkdir -p /app/data && chown appuser /app/data
USER appuser

# 프로세스 생존이 아니라 "모델 로드 완료"를 확인 (실측 기동 ~5초 → 여유 30초)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,json,sys; \
      r=json.load(urllib.request.urlopen('http://localhost:8000/health')); \
      sys.exit(0 if r['model_loaded'] else 1)"

EXPOSE 8000
# Exec 형식 — SIGTERM이 uvicorn에 직접 전달되어 Graceful Shutdown 가능
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
