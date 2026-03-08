import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

region = os.getenv("AWS_REGION", "us-east-1")
ak = os.getenv("AWS_ACCESS_KEY_ID")
sk = os.getenv("AWS_SECRET_ACCESS_KEY")

dynamodb = boto3.client("dynamodb", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
s3 = boto3.client("s3", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)

tables_to_create = [
    ("engauge_analysis_results", "id"),
    ("engauge_contents", "id"),
    ("engauge_trending_topics", "category"),
    ("engauge_users", "id")
]

for table_name, pk in tables_to_create:
    try:
        dynamodb.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Creating table {table_name}...")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": pk, "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": pk, "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST"
            )
        else:
            print(f"Error checking {table_name}: {e}")

bucket_name = ("engauge-media-storage-" + (ak or "default").lower()[:6]).lower()
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"Bucket {bucket_name} already exists.")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print(f"Creating bucket {bucket_name}...")
        try:
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
        except Exception as bucket_err:
             print(f"Error creating bucket {bucket_name}: {bucket_err}")
    else:
        print(f"Error checking bucket {bucket_name}: {e}")

print(f"S3_BUCKET_NAME={bucket_name}")
