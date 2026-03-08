"""
Video Analysis Service — ENGAUGE Serverless Video Pipeline

Architecture:
  Video Upload
  → Frame Extraction (OpenCV, 1 frame every 2s, max 30s)
  → Visual Analysis via Replicate API (LLaVA / BLIP-2)
  → Audio Transcription via AssemblyAI or Groq Whisper
  → Hook Detection (first 3 seconds)
  → Multimodal Context Builder
  → Return structured context for LLM reasoning

No local ML models are loaded.  All heavy inference is remote.
"""

import os
import hashlib
import tempfile
import asyncio
import logging
from typing import Dict, Any, List

try:
    import cv2
except ImportError:
    cv2 = None

from services.vision_api_service import analyze_frames_batch
from services.transcription_service import transcribe_video
from services.hook_detection_service import detect_hook

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory result cache keyed by content hash
# ---------------------------------------------------------------------------
_result_cache: Dict[str, Dict[str, Any]] = {}


def _content_hash(video_path: str) -> str:
    """SHA-256 of the first 64 KB — fast dedup without reading the whole file."""
    h = hashlib.sha256()
    with open(video_path, "rb") as f:
        h.update(f.read(65_536))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Section 2 — Frame Extraction (OpenCV)
# ---------------------------------------------------------------------------

async def extract_frames(
    video_path: str,
    interval_seconds: int = 2,
    max_seconds: int = 30,
) -> List[str]:
    """Extract one frame every *interval_seconds*, limited to the first
    *max_seconds* of video.  Frames are saved as 640×360 JPEGs in the
    system temp directory and their paths are returned.
    """
    if cv2 is None:
        logger.error("OpenCV (cv2) is not installed — cannot extract frames.")
        return []

    def _extract() -> List[str]:
        paths: List[str] = []
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = int(fps * interval_seconds)
        max_frame_count = int(fps * max_seconds)
        tmp = tempfile.gettempdir()

        count = 0
        idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or count > max_frame_count:
                break
            if count % frame_interval == 0:
                frame = cv2.resize(frame, (640, 360))
                out = os.path.join(tmp, f"engauge_frame_{os.path.basename(video_path)}_{idx}.jpg")
                cv2.imwrite(out, frame)
                paths.append(out)
                idx += 1
            count += 1

        cap.release()
        return paths

    try:
        return await asyncio.to_thread(_extract)
    except Exception as e:
        logger.error("Frame extraction failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Section 6 — Multimodal Context Builder  (also the main entry-point)
# ---------------------------------------------------------------------------

async def analyze_video(video_path: str) -> Dict[str, Any]:
    """Full video analysis orchestrator.

    1. Check result cache (by content hash).
    2. Extract frames locally (OpenCV).
    3. Run vision + transcription concurrently via remote APIs.
    4. Run hook detection.
    5. Assemble multimodal context dict.

    Returns
    -------
    dict  with keys:
        frame_descriptions, visual_tags, transcript, keywords,
        detected_topics, hook_strength, hook_type, pacing_score,
        visual_engagement
    """
    # --- Cache check ---
    chash = _content_hash(video_path)
    if chash in _result_cache:
        logger.info("Video cache hit (%s)", chash[:12])
        return _result_cache[chash]

    # 1. Frame extraction (local, non-blocking)
    logger.info("Extracting frames from %s …", video_path)
    frame_paths = await extract_frames(video_path, interval_seconds=2, max_seconds=30)

    # 2. Vision + Audio in parallel (remote APIs)
    logger.info("Dispatching %d frames to vision API & audio to transcription …", len(frame_paths))
    vision_result, audio_result = await asyncio.gather(
        analyze_frames_batch(frame_paths),
        transcribe_video(video_path),
    )

    # Cleanup temp frames
    for p in frame_paths:
        try:
            os.remove(p)
        except OSError:
            pass

    # 3. Hook detection (first 3 seconds)
    hook_result = detect_hook(
        transcript=audio_result.get("transcript", ""),
        visual_tags=vision_result.get("visual_tags", []),
        captions=vision_result.get("captions", []),
    )

    # 4. Derive secondary signals
    visual_tags = vision_result.get("visual_tags", [])
    visual_engagement = 85 if "person speaking" in visual_tags else 50
    if "text overlay" in visual_tags:
        visual_engagement = min(100, visual_engagement + 10)

    num_frames = len(frame_paths)
    pacing_score = min(100, int(num_frames / 15.0 * 100)) if num_frames else 30

    # 5. Assemble multimodal context
    context: Dict[str, Any] = {
        "frame_descriptions": vision_result.get("captions", []),
        "visual_tags": visual_tags,
        "transcript": audio_result.get("transcript", ""),
        "keywords": audio_result.get("keywords", []),
        "detected_topics": audio_result.get("keywords", [])[:5],
        "hook_strength": hook_result["hook_strength"],
        "hook_type": hook_result["hook_type"],
        "hook_description": hook_result.get("hook_description", ""),
        "hook_improvement": hook_result.get("hook_improvement", ""),
        "pacing_score": pacing_score,
        "visual_engagement": visual_engagement,
        "video_duration_analyzed": min(30, num_frames * 2),
    }

    # Cache for dedup
    _result_cache[chash] = context
    logger.info("Video analysis complete — %d frames, hook=%.0f", num_frames, hook_result["hook_strength"])
    return context
