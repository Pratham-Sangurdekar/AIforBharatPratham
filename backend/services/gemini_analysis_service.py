"""
Gemini Analysis Service — Free multimodal analysis via Google Gemini API.

Uses Google's genai SDK for:
  - Image analysis (visual description, objects, themes, improvements)
  - Video analysis (frame analysis + optional Groq Whisper transcription)

Free tier: 15 RPM, 1M tokens/day.
"""

import json
import logging
import asyncio
import os
import tempfile
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when an API returns 429."""
    pass

# ---------------------------------------------------------------------------
# Lazy client
# ---------------------------------------------------------------------------

_genai_client = None


def _get_genai():
    """Lazy-init google.generativeai."""
    global _genai_client
    if _genai_client is None:
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=key)
        _genai_client = genai
    return _genai_client


def is_gemini_available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", ""))


def _get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


# ---------------------------------------------------------------------------
# Image analysis
# ---------------------------------------------------------------------------

def _analyze_image_sync(file_bytes: bytes) -> Dict[str, Any]:
    """Synchronous image analysis via Gemini."""
    genai = _get_genai()
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(file_bytes))
    model = genai.GenerativeModel(_get_model_name())

    prompt = """Analyse this image for social media viral potential. Return ONLY a JSON object with:
{
  "caption": "<detailed description of what the image shows>",
  "detected_objects": ["<object/element 1>", ...],
  "visual_theme": "<overall theme/mood of the image>",
  "emotional_tone": "<emotion the image evokes>",
  "meme_probability": <0.0-1.0>,
  "visual_quality": "<assessment: excellent/good/average/poor>",
  "composition_notes": "<notes on framing, lighting, colors>",
  "improvement_suggestions": [
    "<specific visual improvement 1>",
    "<specific visual improvement 2>",
    "<specific visual improvement 3>"
  ],
  "viral_elements": ["<what makes this shareable>", ...],
  "text_in_image": "<any text detected in the image, or empty string>"
}
Return ONLY the JSON, no markdown fences."""

    response = model.generate_content([prompt, img])
    raw = response.text

    # Parse JSON
    result = _extract_json_from_text(raw)
    if result:
        return result

    # Fallback: return raw text as caption
    return {"caption": raw, "detected_objects": [], "visual_theme": "", "emotional_tone": ""}


async def analyze_image_with_gemini(file_bytes: bytes) -> Dict[str, Any]:
    """Async wrapper for image analysis."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_image_sync, file_bytes)


# ---------------------------------------------------------------------------
# Video analysis
# ---------------------------------------------------------------------------

def _analyze_video_sync(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Synchronous video analysis: Gemini for visuals + Groq Whisper for audio."""
    result: Dict[str, Any] = {}

    # 1. Extract frames and analyze visually with Gemini
    try:
        genai = _get_genai()
        frames = _extract_video_frames(file_bytes, filename, max_frames=4)
        if frames:
            from PIL import Image
            import io
            pil_frames = [Image.open(io.BytesIO(f)) for f in frames]

            model = genai.GenerativeModel(_get_model_name())
            prompt = """These are frames from a video. Analyse the video content. Return ONLY JSON:
{
  "caption": "<what the video is about>",
  "visual_elements": ["<element 1>", ...],
  "emotional_tone": "<emotion of the video>",
  "detected_topics": ["<topic 1>", ...],
  "hook_strength": <0.0-1.0 — how strong is the opening>,
  "pacing_score": <0.0-1.0 — how well-paced is the content>,
  "visual_quality": "<excellent/good/average/poor>",
  "improvement_suggestions": [
    "<specific improvement 1>",
    "<specific improvement 2>",
    "<specific improvement 3>"
  ],
  "content_summary": "<detailed summary of what happens in the video>"
}
Return ONLY JSON, no markdown."""

            content = [prompt] + pil_frames
            response = model.generate_content(content)
            parsed = _extract_json_from_text(response.text)
            if parsed:
                result.update(parsed)
            else:
                result["caption"] = response.text
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            raise RateLimitError(str(e))
        logger.warning("Gemini video frame analysis failed: %s", e)

    # 2. Transcribe audio with Groq Whisper
    try:
        transcript = _transcribe_audio(file_bytes, filename)
        if transcript:
            result["transcript"] = transcript
    except Exception as e:
        logger.warning("Audio transcription failed: %s", e)

    return result


async def analyze_video_with_gemini(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Async wrapper for video analysis."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_video_sync, file_bytes, filename)


# ---------------------------------------------------------------------------
# Audio transcription via Groq Whisper
# ---------------------------------------------------------------------------

def _transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """Transcribe audio using Groq Whisper."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise RuntimeError("GROQ_API_KEY not configured for transcription")

    # Extract audio from video using ffmpeg (if available)
    suffix = os.path.splitext(filename)[1] or ".mp4"
    tmp_video = tempfile.mktemp(suffix=suffix)
    tmp_audio = tempfile.mktemp(suffix=".wav")

    try:
        with open(tmp_video, "wb") as f:
            f.write(file_bytes)

        # Try ffmpeg extraction
        audio_extracted = False
        import subprocess
        try:
            proc = subprocess.run(
                ["ffmpeg", "-i", tmp_video, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", tmp_audio, "-y"],
                capture_output=True, timeout=30
            )
            if proc.returncode == 0 and os.path.exists(tmp_audio):
                audio_extracted = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Use extracted audio or fall back to sending original file
        audio_path = tmp_audio if audio_extracted else tmp_video

        from groq import Groq
        client = Groq(api_key=key)
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="text",
            )
        return str(transcription).strip()
    finally:
        for f in set([tmp_video, tmp_audio]):
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Video frame extraction
# ---------------------------------------------------------------------------

def _extract_video_frames(file_bytes: bytes, filename: str, max_frames: int = 4) -> list:
    """Extract key frames from a video file."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.warning("cv2 not available for frame extraction")
        return []

    suffix = os.path.splitext(filename)[1] or ".mp4"
    tmp = tempfile.mktemp(suffix=suffix)
    try:
        with open(tmp, "wb") as f:
            f.write(file_bytes)

        cap = cv2.VideoCapture(tmp)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return []

        # Sample evenly spaced frames
        indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame)
                frames.append(buf.tobytes())
        cap.release()
        return frames
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _extract_json_from_text(text: str) -> Optional[Dict]:
    """Best-effort JSON extraction."""
    import re
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e > s:
        try:
            return json.loads(text[s : e + 1])
        except json.JSONDecodeError:
            pass
    return None
