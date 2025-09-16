# FAISS RAG 시스템

S3에 저장된 다양한 형식의 문서들을 벡터 인덱싱하여 의미적 검색을 제공하는 시스템입니다.

## 주요 기능

### 🔍 다중 파일 형식 지원
- **PDF**: pypdf를 사용한 텍스트 추출
- **DOCX/DOC**: python-docx를 사용한 문서 처리
- **TXT/MD**: 일반 텍스트 및 마크다운 파일
- **HWP**: olefile을 사용한 한글 문서 처리
- **CSV**: 특정 컬럼 데이터 처리
- **JSON**: content 키 기반 데이터 추출

### 📊 벡터 검색 시스템
- **FAISS**: 고성능 벡터 유사도 검색
- **Sentence Transformers**: 임베딩 모델 (all-MiniLM-L6-v2)
- **청크 기반 처리**: 긴 문서를 적절한 크기로 분할
- **하이브리드 검색**: 파일명 매칭 + 벡터 유사도 검색

### ☁️ S3 연동
- 문서 파일 자동 읽기
- 인덱스/메타데이터 자동 저장
- 폴더 단위 일괄 처리

## 시스템 구조

### 핵심 모듈

#### `main.py` - FastAPI 엔드포인트
```python
POST /index     # 인덱스 생성
GET  /search    # 문서 검색
```

#### `service.py` - 비즈니스 로직
- `s3_read_and_index()`: 파일 읽기 → 청킹 → 인덱싱
- `query_index()`: 검색 쿼리 처리

#### `file_reader.py` - 파일 처리
- S3에서 다양한 형식의 파일 읽기
- 형식별 텍스트 추출
- 청크 데이터 생성

#### `faiss_index.py` - 벡터 인덱싱
- 임베딩 생성 및 FAISS 인덱스 구축
- S3에 인덱스/메타데이터 저장
- 검색 및 결과 반환

#### `text_processor.py` - 텍스트 처리
- 텍스트 청킹 (크기, 오버랩 설정)
- 소스 파일 정보 포함

#### `embedding.py` - 임베딩
- Sentence Transformers 모델 사용
- 배치 처리 지원

#### `s3_client.py` - S3 연동
- AWS S3 클라이언트 관리
- 파일 업로드/다운로드

#### `config.py` - 설정 관리
- 환경변수 기반 설정
- 기본값 제공

## 데이터 플로우

### 인덱싱 과정
1. **파일 읽기**: S3에서 폴더 내 모든 지원 파일 읽기
2. **텍스트 추출**: 파일 형식별 텍스트 추출
3. **청킹**: 설정된 크기로 텍스트 분할 (오버랩 포함)
4. **임베딩**: Sentence Transformers로 벡터 변환
5. **인덱싱**: FAISS L2 인덱스 구축
6. **저장**: S3에 `.index`와 `_metadata.pkl` 저장

### 검색 과정
1. **인덱스 로드**: S3에서 인덱스/메타데이터 다운로드
2. **파일명 매칭**: 짧은 쿼리(3자 이하)에서 파일명 우선 검색
3. **벡터 검색**: 쿼리 임베딩과 문서 벡터 간 유사도 계산
4. **결과 반환**: 거리 순으로 정렬된 청크 리스트

## 저장 구조

### S3 파일 구조
```
bucket/
├── {file_path}/
│   ├── document1.pdf
│   ├── document2.docx
│   └── ...
└── {file_path}/
    ├── {index_name}.index      # FAISS 벡터 인덱스
    └── {index_name}_metadata.pkl # 청크 메타데이터
```

### 메타데이터 구조
```python
{
    'chunks': [
        {
            'content': '청크 텍스트 내용',
            'source': '원본 파일 경로',
            'filename': '파일명',
            'chunk_index': 0,
            'total_chunks': 10
        },
        ...
    ],
    'index_info': {
        'total_vectors': 100,
        'dimension': 384,
        'created_at': '2025-01-01T00:00:00',
        'index_name': 'test'
    }
}
```

## 검색 결과 형식
```python
{
    'rank': 1,
    'distance': 0.25,           # 낮을수록 유사
    'content': '매칭된 청크 내용',
    'source': '원본 파일 경로',
    'filename': '파일명',
    'chunk_index': 2,
    'total_chunks': 10,
    'match_type': 'vector'      # 'vector' or 'filename'
}
```

## 환경 설정

### 필수 환경 변수
```bash
# AWS 설정
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BUCKET_NAME=your-bucket-name
AWS_REGION=ap-northeast-2

# 모델 설정 (옵션)
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# 청킹 설정 (옵션)
DEFAULT_CHUNK_SIZE=1000
DEFAULT_OVERLAP=200
DEFAULT_BATCH_SIZE=32

# 검색 설정 (옵션)
DEFAULT_TOP_K=5
```
