# S3 클라이언트 및 기본 작업
import boto3
from botocore.exceptions import ClientError
from config import BUCKET_NAME, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# S3 클라이언트 초기화
s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# S3에 파일이 존재하는지 확인
def check_faiss_file(object_key):
    """S3에 파일이 존재하는지 확인"""
    try:
        print(BUCKET_NAME, object_key)
        s3.head_object(Bucket=BUCKET_NAME, Key=object_key)
        print(f"파일 발견: s3://{BUCKET_NAME}/{object_key}")
        return True
    except Exception as e:
        if e.response['Error']['Code'] == '404':
            print(f"파일 없음: s3://{BUCKET_NAME}/{object_key}")
            return False
        else:
            # 다른 종류의 에러 (예: 접근 권한 없음)
            print("에러 발생:", e)
            raise

def get_s3_client():
    """S3 클라이언트 반환"""
    return s3

def get_bucket_name():
    """버킷 이름 반환"""
    return BUCKET_NAME