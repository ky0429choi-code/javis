# JARVIS Backend Dockerfile
# 빌드: docker build -f backend/Dockerfile -t jarvis-backend:latest .
# 실행: docker run -p 8000:8000 jarvis-backend:latest

FROM python:3.10-slim

WORKDIR /app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 먼저 requirements.txt 복사 (캐시 최적화용)
COPY backend/requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# 나머지 애플리케이션 코드 복사
COPY backend/ /app/
COPY prompts/ /app/prompts/

# 로그 디렉토리 생성
RUN mkdir -p /app/logs /app/data

# 헬스 체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 포트 노출
EXPOSE 8000

# 시작 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
