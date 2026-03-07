"""
Media processing utilities.
"""

import os
import uuid
import shutil
from typing import Optional, Tuple

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")
os.makedirs(MEDIA_DIR, exist_ok=True)


def save_uploaded_file(file_bytes: bytes, original_filename: str) -> str:
    """Save an uploaded file and return the relative media path."""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(MEDIA_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return f"/media/{unique_name}"


def get_file_size(path: str) -> int:
    """Return file size in bytes."""
    if os.path.exists(path):
        return os.path.getsize(path)
    return 0
