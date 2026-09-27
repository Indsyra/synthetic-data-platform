import boto3
import os

def upload_file(local_path: str, bucket: str, key: str) -> None:
    s3_client = boto3.client("s3")
    s3_client.upload_file(local_path, bucket, key)

if __name__ == "__main__":
    for file_path in os.listdir("data/anonymized_data"):
        upload_file(f"data/anonymized_data/{file_path}", "indira-synthetic-social-data-2026", f"raw/{file_path}")