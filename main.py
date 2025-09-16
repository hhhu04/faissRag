# FastAPI 엔드포인트 - HTTP 요청/응답 처리만 담당
from fastapi import FastAPI
from service import s3_read_and_index, query_index

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FAISS RAG API"}

@app.post("/index")
async def create_index(file_path: str, index_name: str):
    """파일을 읽어서 인덱스 생성"""
    result = s3_read_and_index(file_path, index_name)
    return {"success": result, "message": "인덱스 생성 완료" if result else "인덱스 생성 실패"}

@app.get("/search")
async def search(file_path: str, query: str, index_name: str, top_k: int = 5):
    """인덱스에서 검색"""
    results = query_index(file_path, query, index_name, top_k)
    return {"results": results}

