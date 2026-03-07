"""
Content Analyzer — Step 1 & 2: Detect content type and extract metadata.
"""

import os
from typing import Dict, Any, Optional


class ContentAnalyzer:
    """Detects content type and extracts metadata from uploaded content."""

    SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm"}
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}

    @staticmethod
    def detect_content_type(
        text: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ContentAnalyzer.SUPPORTED_IMAGE_EXTENSIONS:
                return "image"
            if ext in ContentAnalyzer.SUPPORTED_VIDEO_EXTENSIONS:
                return "video"
            if ext in ContentAnalyzer.SUPPORTED_AUDIO_EXTENSIONS:
                return "audio"
        if text:
            return "text"
        return "unknown"

    @staticmethod
    def extract_metadata(
        text: Optional[str] = None,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        content_type = ContentAnalyzer.detect_content_type(text, filename)
        metadata: Dict[str, Any] = {
            "content_type": content_type,
            "has_text": text is not None and len(text.strip()) > 0,
            "text_length": len(text) if text else 0,
        }
        if filename:
            metadata["filename"] = filename
            metadata["extension"] = os.path.splitext(filename)[1].lower()
        if file_size:
            metadata["file_size_bytes"] = file_size
        return metadata
