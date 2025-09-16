# 비즈니스 로직 서비스 레이어
from file_reader import s3_read
from faiss_index import create_and_save_faiss_index, search_faiss_index
from s3_client import check_faiss_file
from config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, DEFAULT_TOP_K

# S3 파일 읽기와 인덱싱을 한번에 처리하는 메인 함수
def s3_read_and_index(file_path: str, index_name: str, chunk_size: int = DEFAULT_CHUNK_SIZE, 
                     overlap: int = DEFAULT_OVERLAP, force_update: bool = False):
    """S3에서 파일을 읽어서 청크로 나누고 FAISS 인덱스 생성/업데이트 후 저장"""
    
    # 이미 인덱스가 존재하는지 확인
    index_key = f"{file_path.lstrip('/')}/{index_name}.index"
    if check_faiss_file(index_key) and not force_update:
        print(f"인덱스가 이미 존재합니다: {index_name}")
        print("기존 인덱스를 덮어씁니다...")
    else:
        print(f"새로운 인덱스 생성 시작: {index_name}")
    
    # 파일들을 읽어서 청크 생성
    chunks = s3_read(file_path, index_name, chunk_size, overlap)

    if not chunks:
        print("처리할 청크가 없습니다.")
        return False

    # FAISS 인덱스 생성 및 저장
    return create_and_save_faiss_index(file_path, chunks, index_name)

# 저장된 인덱스에서 질의 검색을 수행하는 엔드포인트 함수
def query_index(file_path: str, query: str, index_name: str, top_k: int = DEFAULT_TOP_K):
    """기존 FAISS 인덱스에서 질의 검색"""
    
    index_key = f"{file_path.lstrip('/')}/{index_name}.index"
    if not check_faiss_file(index_key):
        print(f"인덱스가 존재하지 않습니다: {index_name}")
        return []
    
    print(f"질의 검색 중: '{query}'")
    return search_faiss_index(file_path, query, index_name, top_k)