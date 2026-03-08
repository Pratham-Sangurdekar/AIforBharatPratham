"""
Transcription Service — Remote Audio Transcription

Extracts the audio track from a video via ffmpeg, then sends it to
AssemblyAI (primary) or Groq Whisper (fallback) for transcription.

No local ML models are loaded.
"""

import os
import tempfile
import asyncio
import logging
from typing import Dict, Any

try:
    import assemblyai as aai
except ImportError:
    aai = None

try:
    from groq import Groq as _GroqClient
except ImportError:
    _GroqClient = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Audio extraction (ffmpeg subprocess)
# ---------------------------------------------------------------------------

async def _extract_audio(video_path: str) -> str:
    """Extract audio from a video file using ffmpeg.  Returns the path to
    a temporary MP3 file, or ``""`` if extraction fails.
    """
    audio_path = os.path.join(
        tempfile.gettempdir(),
        f"engauge_audio_{os.path.basename(video_path)}.mp3",
    )

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", video_path,
        "-q:a", "0", "-map", "a", "-t", "30",   # limit to first 30s
        audio_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        return audio_path

    logger.warning("ffmpeg audio extraction produced no output for %s", video_path)
    return ""


# ---------------------------------------------------------------------------
# AssemblyAI transcription (primary)
# ---------------------------------------------------------------------------

async def _transcribe_assemblyai(audio_path: str) -> Dict[str, Any]:
    """Send audio to AssemblyAI and return transcript + keywords."""
    api_key = os.getenv("ASSEMBLYAI_API_KEY", "")
    if not aai or not api_key:
        raise RuntimeError("AssemblyAI SDK or API key not available")

    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(auto_highlights=True)
    transcriber = aai.Transcriber()

    transcript = await asyncio.to_thread(transcriber.transcribe, audio_path, config)

    text = transcript.text or ""

    keywords: list[str] = []
    if transcript.auto_highlights and hasattr(transcript.auto_highlights, "results"):
        for res in transcript.auto_highlights.results:
            keywords.append(res.text)

    return {"transcript": text, "keywords": keywords[:8]}


# ---------------------------------------------------------------------------
# Groq Whisper transcription (fallback)
# ---------------------------------------------------------------------------

async def _transcribe_groq_whisper(audio_path: str) -> Dict[str, Any]:
    """Send audio to Groq's hosted Whisper endpoint."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not _GroqClient or not api_key:
        raise RuntimeError("Groq SDK or API key not available")

    client = _GroqClient(api_key=api_key)

    def _call():
        with open(audio_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=("audio.mp3", f),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        return resp

    resp = await asyncio.to_thread(_call)
    text = resp.text if hasattr(resp, "text") else str(resp)

    # Extract simple keywords (first unique nouns ≥ 4 chars)
    words = text.split()
    seen: set[str] = set()
    keywords: list[str] = []
    for w in words:
        clean = w.strip(".,!?\"'").lower()
        if len(clean) >= 4 and clean not in seen:
            seen.add(clean)
            keywords.append(clean)
        if len(keywords) >= 8:
            break

    return {"transcript": text, "keywords": keywords}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def transcribe_video(video_path: str) -> Dict[str, Any]:
    """Extract audio from *video_path* and transcribe it remotely.

    Tries AssemblyAI first; falls back to Groq Whisper.
    Returns ``{"transcript": "...", "keywords": [...]}``
    """
    audio_path = await _extract_audio(video_path)
    if not audio_path:
        return {"transcript": "", "keywords": []}

    try:
        result = await _transcribe_assemblyai(audio_path)
        logger.info("Transcription via AssemblyAI succeeded (%d chars)", len(result["transcript"]))
        return result
    except Exception as e:
        logger.warning("AssemblyAI failed (%s), trying Groq Whisper …", e)

    try:
        result = await _transcribe_groq_whisper(audio_path)
        logger.info("Transcription via Groq Whisper succeeded (%d chars)", len(result["transcript"]))
        return result
    except Exception as e:
        logger.error("All transcription backends failed: %s", e)

    finally:
        # Cleanup temp audio
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass

    return {"transcript": "", "keywords": []}
