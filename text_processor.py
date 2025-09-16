# 텍스트 처리 및 청킹
from config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP

# 긴 텍스트를 지정된 크기의 청크로 분할
def chunk_text(text: str, source_file: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
    """텍스트를 청크로 나누고 소스 파일 정보 포함"""
    chunks = []
    # 파일명만 추출 (경로에서 마지막 부분)
    filename = source_file.split('/')[-1]

    if len(text) <= chunk_size:
        chunks.append({
            'content': text,
            'source': source_file,
            'filename': filename,
            'chunk_index': 0,
            'total_chunks': 1
        })
        return chunks
    
    start = 0
    chunk_index = 0
    total_chunks = (len(text) - overlap) // (chunk_size - overlap) + 1
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_content = text[start:end]
        
        chunks.append({
            'content': chunk_content,
            'source': source_file,
            'filename': filename,
            'chunk_index': chunk_index,
            'total_chunks': total_chunks
        })
        
        chunk_index += 1
        start = end - overlap
        
        if end >= len(text):
            break
    
    return chunks