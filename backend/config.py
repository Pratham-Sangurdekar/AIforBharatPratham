"""
ENGAUGE Configuration — Environment-based settings.
Supports local development (SQLite + filesystem) and AWS (DynamoDB + S3 + Bedrock).
"""

import os
from enum import Enum


class Environment(str, Enum):
    LOCAL = "local"
    AWS = "aws"


# Determine the runtime environment
ENV = Environment(os.getenv("ENGAUGE_ENV", "local").lower())

# ---------- AWS Settings ----------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# S3
S3_MEDIA_BUCKET = os.getenv("S3_MEDIA_BUCKET", "engauge-media")
S3_FRONTEND_BUCKET = os.getenv("S3_FRONTEND_BUCKET", "engauge-frontend")

# DynamoDB
DYNAMODB_ANALYSIS_TABLE = os.getenv("DYNAMODB_ANALYSIS_TABLE", "engauge_analysis_results")
DYNAMODB_CONTENT_TABLE = os.getenv("DYNAMODB_CONTENT_TABLE", "engauge_contents")
DYNAMODB_TRENDS_TABLE = os.getenv("DYNAMODB_TRENDS_TABLE", "engauge_trending_topics")
DYNAMODB_USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "engauge_users")

# Bedrock
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "2048"))
BEDROCK_TIMEOUT = int(os.getenv("BEDROCK_TIMEOUT", "15"))  # seconds

# CloudFront
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "")

# API Gateway
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "")

# ---------- Local Settings ----------
SQLITE_URL = os.getenv("SQLITE_URL", "sqlite:///./engauge.db")
LOCAL_MEDIA_DIR = os.getenv("LOCAL_MEDIA_DIR", "media")

# ---------- CORS ----------
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# ---------- Feature Flags ----------
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"  # Use Bedrock LLM vs heuristics
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"  # Use Ollama local LLM
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "mistral")


def is_aws() -> bool:
    return ENV == Environment.AWS


def is_local() -> bool:
    return ENV == Environment.LOCAL
