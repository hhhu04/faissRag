FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 기본 환경 변수 설정 (민감하지 않은 정보만)
ARG EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
ARG DEFAULT_CHUNK_SIZE=1000
ARG DEFAULT_OVERLAP=200
ARG DEFAULT_BATCH_SIZE=32
ARG DEFAULT_TOP_K=5
ARG AWS_REGION=ap-northeast-2

ENV EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}
ENV DEFAULT_CHUNK_SIZE=${DEFAULT_CHUNK_SIZE}
ENV DEFAULT_OVERLAP=${DEFAULT_OVERLAP}
ENV DEFAULT_BATCH_SIZE=${DEFAULT_BATCH_SIZE}
ENV DEFAULT_TOP_K=${DEFAULT_TOP_K}
ENV AWS_REGION=${AWS_REGION}

# 포트 노출
EXPOSE 8002

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]