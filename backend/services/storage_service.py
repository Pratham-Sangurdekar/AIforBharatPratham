"""
Storage Service — Abstraction layer for file storage.
Supports: Amazon S3 | Local filesystem.

The service is portable: swap the backend by changing ENGAUGE_ENV.
"""

import os
import uuid
import logging
from typing import Optional, Tuple

from config import is_aws, S3_MEDIA_BUCKET, AWS_REGION, LOCAL_MEDIA_DIR, CLOUDFRONT_DOMAIN

logger = logging.getLogger(__name__)

# Lazy-loaded S3 client
_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


# Content type subfolder mapping
_TYPE_FOLDERS = {
    ".jpg": "images", ".jpeg": "images", ".png": "images", ".gif": "images",
    ".webp": "images", ".svg": "images", ".bmp": "images",
    ".mp4": "videos", ".mov": "videos", ".avi": "videos", ".mkv": "videos",
    ".webm": "videos",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio",
    ".flac": "audio",
}


def _get_subfolder(filename: str) -> str:
    """Determine the upload subfolder based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    return _TYPE_FOLDERS.get(ext, "other")


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def save_file(file_bytes: bytes, original_filename: str) -> str:
    """
    Save a file and return the URL/path to access it.

    AWS mode:  uploads to S3 → returns CloudFront/S3 URL
    Local mode: saves to disk → returns /media/{filename}
    """
    if is_aws():
        return _save_to_s3(file_bytes, original_filename)
    return _save_to_local(file_bytes, original_filename)


def get_file_url(path_or_key: str) -> str:
    """
    Convert a stored path/key to a full URL.
    In AWS mode, generates a pre-signed S3 URL (valid for 1 hour)
    if CloudFront is not configured, ensuring no public bucket access is needed.
    """
    if is_aws():
        if path_or_key.startswith("http"):
            return path_or_key
        if CLOUDFRONT_DOMAIN:
            return f"https://{CLOUDFRONT_DOMAIN}/{path_or_key}"
        # Generate a pre-signed URL (valid 1 hour) — no public bucket needed
        try:
            s3 = _get_s3_client()
            key = _extract_s3_key(path_or_key)
            return s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_MEDIA_BUCKET, "Key": key},
                ExpiresIn=3600,
            )
        except Exception as e:
            logger.warning(f"Failed to generate signed URL, falling back to direct URL: {e}")
            return f"https://{S3_MEDIA_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{path_or_key}"
    return path_or_key  # Already a local /media/ path


def delete_file(path_or_key: str) -> bool:
    """Delete a stored file."""
    if is_aws():
        return _delete_from_s3(path_or_key)
    return _delete_from_local(path_or_key)


def file_exists(path_or_key: str) -> bool:
    """Check if a file exists in storage."""
    if is_aws():
        return _exists_in_s3(path_or_key)
    return _exists_locally(path_or_key)


# ──────────────────────────────────────────────
# S3 Implementation
# ──────────────────────────────────────────────

def _save_to_s3(file_bytes: bytes, original_filename: str) -> str:
    """Upload file to S3 bucket."""
    s3 = _get_s3_client()
    ext = os.path.splitext(original_filename)[1].lower()
    subfolder = _get_subfolder(original_filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    s3_key = f"uploads/{subfolder}/{unique_name}"

    content_type = _guess_content_type(ext)

    s3.put_object(
        Bucket=S3_MEDIA_BUCKET,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )

    logger.info(f"Uploaded to S3: s3://{S3_MEDIA_BUCKET}/{s3_key}")

    # Return the URL
    if CLOUDFRONT_DOMAIN:
        return f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
    return f"https://{S3_MEDIA_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"


def _delete_from_s3(s3_key: str) -> bool:
    """Delete a file from S3."""
    try:
        s3 = _get_s3_client()
        # Strip URL prefix to get key
        key = _extract_s3_key(s3_key)
        s3.delete_object(Bucket=S3_MEDIA_BUCKET, Key=key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete from S3: {e}")
        return False


def _exists_in_s3(s3_key: str) -> bool:
    """Check if a file exists in S3."""
    try:
        s3 = _get_s3_client()
        key = _extract_s3_key(s3_key)
        s3.head_object(Bucket=S3_MEDIA_BUCKET, Key=key)
        return True
    except Exception:
        return False


def _extract_s3_key(url_or_key: str) -> str:
    """Extract the S3 key from a URL or return as-is."""
    if url_or_key.startswith("https://"):
        # https://bucket.s3.region.amazonaws.com/key or https://cloudfront/key
        parts = url_or_key.split("/", 3)
        return parts[3] if len(parts) > 3 else url_or_key
    return url_or_key


# ──────────────────────────────────────────────
# Local Filesystem Implementation
# ──────────────────────────────────────────────

_local_media_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), LOCAL_MEDIA_DIR)
os.makedirs(_local_media_dir, exist_ok=True)


def _save_to_local(file_bytes: bytes, original_filename: str) -> str:
    """Save file to local media directory."""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(_local_media_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return f"/media/{unique_name}"


def _delete_from_local(path: str) -> bool:
    """Delete a file from local storage."""
    try:
        full_path = os.path.join(_local_media_dir, os.path.basename(path))
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete local file: {e}")
        return False


def _exists_locally(path: str) -> bool:
    """Check if a local file exists."""
    full_path = os.path.join(_local_media_dir, os.path.basename(path))
    return os.path.exists(full_path)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _guess_content_type(ext: str) -> str:
    """Map file extension to MIME type."""
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo",
        ".webm": "video/webm", ".mkv": "video/x-matroska",
        ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
        ".m4a": "audio/mp4", ".flac": "audio/flac",
    }
    return mime_map.get(ext, "application/octet-stream")
