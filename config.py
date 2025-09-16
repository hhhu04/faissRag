# AWS 및 모델 설정
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# AWS S3 설정
BUCKET_NAME = os.getenv('BUCKET_NAME', 'faiss-bucket-dd')
AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# 임베딩 모델 설정
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')

# 청킹 기본 설정
DEFAULT_CHUNK_SIZE = int(os.getenv('DEFAULT_CHUNK_SIZE', '1000'))
DEFAULT_OVERLAP = int(os.getenv('DEFAULT_OVERLAP', '200'))
DEFAULT_BATCH_SIZE = int(os.getenv('DEFAULT_BATCH_SIZE', '32'))

# 검색 기본 설정
DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '5'))