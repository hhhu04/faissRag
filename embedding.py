# 임베딩 모델 관리 및 벡터 생성
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME, DEFAULT_BATCH_SIZE

# 전역 모델 변수 (메모리 최적화)
_embedding_model = None

# 임베딩 모델을 싱글톤 패턴으로 관리
def get_embedding_model():
    """임베딩 모델을 가져오거나 초기화 (싱글톤 패턴)"""
    global _embedding_model
    if _embedding_model is None:
        print(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL_NAME}")
        try:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            print("임베딩 모델 로딩 완료")
        except Exception as e:
            print(f"임베딩 모델 로딩 실패: {e}")
            raise e
    return _embedding_model

# 대량의 텍스트를 배치 단위로 효율적으로 임베딩
def encode_texts_batch(texts: list, batch_size: int = DEFAULT_BATCH_SIZE):
    """텍스트들을 배치 단위로 임베딩 생성"""
    model = get_embedding_model()
    
    if len(texts) <= batch_size:
        return model.encode(texts, show_progress_bar=True)
    
    all_vectors = []
    print(f"배치 처리 중 (배치 크기: {batch_size}, 총 {len(texts)}개 텍스트)")
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"배치 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} 처리 중...")
        
        try:
            batch_vectors = model.encode(batch_texts, show_progress_bar=False)
            all_vectors.extend(batch_vectors)
        except Exception as e:
            print(f"배치 {i//batch_size + 1} 처리 중 에러: {e}")
            raise e
    
    return np.array(all_vectors)

# 단일 쿼리 임베딩 생성
def encode_query(query: str):
    """단일 쿼리 텍스트를 임베딩"""
    model = get_embedding_model()
    query_vector = model.encode([query])
    return np.array(query_vector, dtype=np.float32)