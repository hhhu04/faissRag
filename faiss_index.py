# FAISS 인덱스 생성 및 검색
import pickle
import faiss
import numpy as np
import tempfile
import os
from datetime import datetime
from embedding import encode_texts_batch, encode_query
from s3_client import get_s3_client, get_bucket_name
from config import DEFAULT_BATCH_SIZE, DEFAULT_TOP_K

# 청크들을 임베딩하여 FAISS 인덱스 생성 후 S3 저장
def create_and_save_faiss_index(file_path: str, chunks: list, index_name: str, batch_size: int = DEFAULT_BATCH_SIZE):
    """청크들을 임베딩하고 FAISS 인덱스 생성 후 S3에 저장"""
    if not chunks:
        print("청크가 없습니다. 인덱스를 생성할 수 없습니다.")
        return False
    
    print(f"총 {len(chunks)}개 청크를 임베딩 중...")
    
    # 청크들의 텍스트만 추출
    texts = [chunk['content'] for chunk in chunks]
    
    # 임베딩 생성 (배치 처리)
    try:
        vectors_array = encode_texts_batch(texts, batch_size)
        vectors_array = vectors_array.astype(np.float32)
        print(f"임베딩 완료: {vectors_array.shape}")
    except Exception as e:
        print(f"임베딩 생성 중 에러: {e}")
        return False
    
    # FAISS 인덱스 생성
    dimension = vectors_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors_array)
    
    print(f"FAISS 인덱스 생성 완료: {index.ntotal}개 벡터, 차원: {dimension}")
    
    # 메타데이터 준비
    metadata = {
        'chunks': chunks,
        'index_info': {
            'total_vectors': int(index.ntotal),
            'dimension': dimension,
            'created_at': datetime.now().isoformat(),
            'index_name': index_name
        }
    }
    
    # 임시 파일로 저장 후 S3에 업로드
    try:
        s3 = get_s3_client()
        bucket_name = get_bucket_name()
        
        # FAISS 인덱스 저장
        tmp_index = tempfile.NamedTemporaryFile(delete=False, suffix='.index')
        tmp_index_path = tmp_index.name
        tmp_index.close()  # 파일 핸들 명시적 종료
        faiss.write_index(index, tmp_index_path)
        
        # 메타데이터 저장
        tmp_meta = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl', mode='wb')
        tmp_meta_path = tmp_meta.name
        pickle.dump(metadata, tmp_meta)
        tmp_meta.close()  # 파일 핸들 명시적 종료
        
        # S3에 업로드
        index_key = f"{file_path.lstrip('/')}/{index_name}.index"
        metadata_key = f"{file_path.lstrip('/')}/{index_name}_metadata.pkl"
        
        # 인덱스 파일 업로드
        s3.upload_file(tmp_index_path, bucket_name, index_key)
        print(f"FAISS 인덱스 업로드 완료: s3://{bucket_name}/{index_key}")
        
        # 메타데이터 파일 업로드
        s3.upload_file(tmp_meta_path, bucket_name, metadata_key)
        print(f"메타데이터 업로드 완료: s3://{bucket_name}/{metadata_key}")
        
        # 임시 파일 삭제
        os.unlink(tmp_index_path)
        os.unlink(tmp_meta_path)
        
        return True
        
    except Exception as e:
        print(f"S3 업로드 중 에러: {e}")
        return False

# S3에서 FAISS 인덱스 로드 후 유사도 검색 수행
def search_faiss_index(file_path: str, query: str, index_name: str, top_k: int = DEFAULT_TOP_K):
    """S3에서 FAISS 인덱스를 로드하고 질의에 대한 유사한 청크 검색"""

    index_key = f"{file_path.lstrip('/')}/{index_name}.index"
    metadata_key = f"{file_path.lstrip('/')}/{index_name}_metadata.pkl"

    try:
        s3 = get_s3_client()
        bucket_name = get_bucket_name()

        # S3에서 인덱스와 메타데이터 다운로드
        tmp_index = tempfile.NamedTemporaryFile(delete=False, suffix='.index')
        tmp_index_path = tmp_index.name
        tmp_index.close()  # 파일 핸들 명시적 종료
        s3.download_file(bucket_name, index_key, tmp_index_path)

        tmp_meta = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl')
        tmp_meta_path = tmp_meta.name
        tmp_meta.close()  # 파일 핸들 명시적 종료
        s3.download_file(bucket_name, metadata_key, tmp_meta_path)

        # FAISS 인덱스 로드
        index = faiss.read_index(tmp_index_path)

        # 메타데이터 로드
        with open(tmp_meta_path, 'rb') as f:
            metadata = pickle.load(f)

        chunks = metadata['chunks']

        # 파일명 기반 필터링 (query가 파일명의 주요 단어와 정확히 일치하는 경우만)
        query_lower = query.lower().strip()
        filename_matched_chunks = []

        # 짧은 쿼리(3자 이하)이고 파일명에 정확히 포함된 경우만 파일명 매칭
        if len(query_lower) <= 3:
            for idx, chunk in enumerate(chunks):
                if 'filename' in chunk and query_lower in chunk['filename'].lower():
                    filename_matched_chunks.append((idx, chunk))

        # 파일명 매칭된 청크가 있고 쿼리가 짧은 경우만 우선 반환
        if filename_matched_chunks and len(query_lower) <= 3:
            results = []
            for i, (idx, chunk) in enumerate(filename_matched_chunks[:top_k]):
                results.append({
                    'rank': i + 1,
                    'distance': 0.0,  # 파일명 매칭은 거리 0
                    'content': chunk['content'],
                    'source': chunk['source'],
                    'filename': chunk.get('filename', ''),
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'match_type': 'filename'
                })
            return results

        # 질의 임베딩 생성
        query_array = encode_query(query)

        # 유사도 검색
        distances, indices = index.search(query_array, top_k)

        # 결과 구성
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(chunks):
                chunk = chunks[idx]
                results.append({
                    'rank': i + 1,
                    'distance': float(distance),
                    'content': chunk['content'],
                    'source': chunk['source'],
                    'filename': chunk.get('filename', ''),
                    'chunk_index': chunk['chunk_index'],
                    'total_chunks': chunk['total_chunks'],
                    'match_type': 'vector'
                })
        
        # 임시 파일 삭제
        os.unlink(tmp_index_path)
        os.unlink(tmp_meta_path)
        
        return results
        
    except Exception as e:
        print(f"검색 중 에러: {e}")
        return []