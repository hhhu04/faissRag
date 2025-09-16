FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정 (빌드 시 전달받음)
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG BUCKET_NAME
ARG AWS_REGION
ARG EMBEDDING_MODEL_NAME
ARG DEFAULT_CHUNK_SIZE
ARG DEFAULT_OVERLAP
ARG DEFAULT_BATCH_SIZE
ARG DEFAULT_TOP_K

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV BUCKET_NAME=${BUCKET_NAME}
ENV AWS_REGION=${AWS_REGION}
ENV EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}
ENV DEFAULT_CHUNK_SIZE=${DEFAULT_CHUNK_SIZE}
ENV DEFAULT_OVERLAP=${DEFAULT_OVERLAP}
ENV DEFAULT_BATCH_SIZE=${DEFAULT_BATCH_SIZE}
ENV DEFAULT_TOP_K=${DEFAULT_TOP_K}

# 포트 노출
EXPOSE 8002

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]