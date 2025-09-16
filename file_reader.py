# 다양한 파일 형식 읽기 및 처리
import io
import json
import csv
import olefile
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from s3_client import get_s3_client, get_bucket_name, check_faiss_file
from text_processor import chunk_text
from config import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP

# S3에서 파일들을 읽어 텍스트 추출 및 청크 생성
def s3_read(file_path: str, file_name: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
    """S3에서 파일들을 읽어 텍스트 추출 및 청크 생성"""
    print("파일들을 읽어서 청크 생성 중...")
    file_path = file_path.lstrip('/')

    s3 = get_s3_client()
    bucket_name = get_bucket_name()

    bucket = s3.list_objects_v2(Bucket=bucket_name, Prefix=file_path + "/")

    print(bucket)

    all_chunks = []
    for obj in bucket['Contents']:
        if obj['Key'].endswith('/'):  # 폴더는 건너뛰기
            continue

        try:
            # 파일 본문을 바이트 형태로 우선 읽어옵니다. (Client 방식)
            file_obj = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
            body_bytes = file_obj['Body'].read()

            # 파일 확장자 확인
            file_path_obj = Path(obj['Key'])
            file_suffix = file_path_obj.suffix.lower()

            if file_suffix == '.pdf':
                chunks = _process_pdf(body_bytes, obj['Key'], chunk_size, overlap)
                all_chunks.extend(chunks)
                print(f" - [PDF] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")

            elif file_suffix in ['.docx', '.doc']:
                chunks = _process_docx(body_bytes, obj['Key'], chunk_size, overlap)
                all_chunks.extend(chunks)
                print(f" - [DOCX] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")

            elif file_suffix in ['.txt', '.md']:
                chunks = _process_text(body_bytes, obj['Key'], chunk_size, overlap)
                all_chunks.extend(chunks)
                print(f" - [TXT/MD] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")

            elif file_suffix == '.hwp':
                chunks = _process_hwp(body_bytes, obj['Key'], chunk_size, overlap)
                if chunks:
                    all_chunks.extend(chunks)
                    print(f" - [HWP] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")

            elif file_suffix == '.csv':
                chunks = _process_csv(body_bytes, obj['Key'], chunk_size, overlap)
                all_chunks.extend(chunks)
                print(f" - [CSV] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")

            elif file_suffix == '.json':
                chunks = _process_json(body_bytes, obj['Key'], chunk_size, overlap)
                if chunks:
                    all_chunks.extend(chunks)
                    print(f" - [JSON] 로드 완료: {obj['Key']} ({len(chunks)}개 청크)")
                else:
                    print(f" - [JSON] content 키 없음: {obj['Key']}")

        except Exception as e:
            print(f" !! 파일 처리 중 에러 발생: {obj['Key']}, 에러: {e}")
            return None

    return all_chunks

def _process_pdf(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """PDF 파일 처리"""
    pdf_stream = io.BytesIO(body_bytes)
    pdf_reader = PdfReader(pdf_stream)
    full_text = ""
    
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n"
    
    return chunk_text(full_text, file_key, chunk_size, overlap)

def _process_docx(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """DOCX/DOC 파일 처리"""
    docx_file = io.BytesIO(body_bytes)
    document = Document(docx_file)
    full_text = ""
    
    for paragraph in document.paragraphs:
        full_text += paragraph.text + "\n"
    
    return chunk_text(full_text, file_key, chunk_size, overlap)

def _process_text(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """텍스트/마크다운 파일 처리"""
    text = body_bytes.decode('utf-8')
    return chunk_text(text, file_key, chunk_size, overlap)

def _process_hwp(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """HWP 파일 처리"""
    try:
        ole = olefile.OleFileIO(io.BytesIO(body_bytes))
        encoded_text = ole.openstream('PrvText').read()
        text_content = encoded_text.decode('utf-16')
        ole.close()
        
        return chunk_text(text_content, file_key, chunk_size, overlap)
    except Exception as hwp_error:
        print(f" !! HWP 파일 처리 중 에러 발생: {file_key}, 에러: {hwp_error}")
        return []

def _process_csv(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """CSV 파일 처리"""
    csv_file = io.StringIO(body_bytes.decode('utf-8'))
    reader = csv.reader(csv_file)
    next(reader, None)  # 헤더 행 건너뛰기
    csv_content = []
    
    for row in reader:
        if len(row) > 1:
            csv_content.append(row[1])  # 1번 인덱스(2번째) 열
    
    # CSV 내용을 하나의 텍스트로 합치고 청크로 나누기
    combined_text = '\n'.join(csv_content)
    return chunk_text(combined_text, file_key, chunk_size, overlap)

def _process_json(body_bytes: bytes, file_key: str, chunk_size: int, overlap: int):
    """JSON 파일 처리"""
    json_data = json.loads(body_bytes.decode('utf-8'))
    if 'content' in json_data:
        return chunk_text(json_data['content'], file_key, chunk_size, overlap)
    else:
        return []