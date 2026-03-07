"""
Video Analysis Service — Extracts intelligence from video content.

Pipeline:
  1. Extract key frames every 2 seconds (OpenCV)
  2. Analyse frames with image_analysis_service (BLIP/CLIP)
  3. Extract audio track (ffmpeg/moviepy)
  4. Transcribe audio with Whisper
  5. Combine results

Limits analysed portion to the first 30 seconds for performance.

Output:
  {
    transcript: str,
    detected_topics: List[str],
    visual_elements: List[str],
    emotional_tone: str,
    hook_strength: float,
    pacing_score: float,
  }
"""

import asyncio
import io
import os
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Shared thread pool for CPU-heavy work (model inference, frame extraction)
_video_pool = ThreadPoolExecutor(max_workers=2)

MAX_DURATION_SECONDS = 30
FRAME_INTERVAL_SECONDS = 2


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def _extract_frames(video_path: str) -> List[bytes]:
    """Extract key frames every FRAME_INTERVAL_SECONDS using OpenCV.

    Returns list of JPEG-encoded frame bytes.
    """
    frames: List[bytes] = []
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        max_frame = int(min(MAX_DURATION_SECONDS * fps, total_frames))
        frame_step = int(fps * FRAME_INTERVAL_SECONDS)

        frame_idx = 0
        while frame_idx < max_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            _, buf = cv2.imencode(".jpg", frame)
            frames.append(buf.tobytes())
            frame_idx += frame_step

        cap.release()
    except ImportError:
        logger.warning("OpenCV (cv2) not installed — cannot extract video frames")
    except Exception as e:
        logger.warning("Frame extraction failed: %s", e)

    return frames


# ---------------------------------------------------------------------------
# Audio extraction
# ---------------------------------------------------------------------------

def _extract_audio(video_path: str) -> Optional[str]:
    """Extract audio track from video to a temporary WAV file.

    Tries moviepy first, then ffmpeg subprocess.
    Returns path to the WAV file or None.
    """
    wav_path = video_path + ".audio.wav"

    # Try moviepy
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        if clip.audio is not None:
            # Limit to first 30 seconds
            duration = min(clip.duration, MAX_DURATION_SECONDS)
            clip.audio.subclipped(0, duration).write_audiofile(wav_path, logger=None)
            clip.close()
            return wav_path
        clip.close()
    except ImportError:
        pass
    except Exception as e:
        logger.debug("moviepy audio extraction failed: %s", e)

    # Try ffmpeg subprocess
    try:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-t", str(MAX_DURATION_SECONDS),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            wav_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
            return wav_path
    except Exception as e:
        logger.debug("ffmpeg audio extraction failed: %s", e)

    return None


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

async def analyze_video(video_bytes: bytes, filename: str = "video.mp4") -> Dict[str, Any]:
    """
    Full video analysis pipeline.
    Runs the heavy synchronous work (OpenCV, BLIP/CLIP, Whisper) in a thread
    pool so the async event loop is never blocked.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_video_pool, _analyze_video_sync, video_bytes, filename)


def _analyze_video_sync(video_bytes: bytes, filename: str = "video.mp4") -> Dict[str, Any]:
    """
    Synchronous video analysis — called from thread pool.
    """
    result: Dict[str, Any] = {
        "transcript": "",
        "detected_topics": [],
        "visual_elements": [],
        "emotional_tone": "neutral",
        "hook_strength": 0.5,
        "pacing_score": 0.5,
    }

    # Write to temp file for OpenCV/ffmpeg
    tmp_dir = tempfile.mkdtemp()
    video_path = os.path.join(tmp_dir, filename)
    with open(video_path, "wb") as f:
        f.write(video_bytes)

    try:
        # --- Step 1 & 2: Extract and analyse frames ---
        frames = _extract_frames(video_path)
        visual_themes: List[str] = []
        emotions: List[str] = []
        captions: List[str] = []
        objects: List[str] = []

        if frames:
            from services.image_analysis_service import analyze_image_sync
            for i, frame_bytes in enumerate(frames[:8]):  # Limit to 8 frames
                try:
                    frame_result = analyze_image_sync(frame_bytes)
                    if frame_result.get("caption"):
                        captions.append(frame_result["caption"])
                    if frame_result.get("visual_theme"):
                        visual_themes.append(frame_result["visual_theme"])
                    if frame_result.get("emotional_tone"):
                        emotions.append(frame_result["emotional_tone"])
                    objects.extend(frame_result.get("detected_objects", []))
                except Exception as e:
                    logger.debug("Frame %d analysis failed: %s", i, e)

        # Deduplicate
        visual_elements = list(dict.fromkeys(objects + visual_themes))[:10]
        result["visual_elements"] = visual_elements

        # Most common emotion across frames
        if emotions:
            from collections import Counter
            result["emotional_tone"] = Counter(emotions).most_common(1)[0][0]

        # --- Step 3 & 4: Extract audio and transcribe ---
        audio_path = _extract_audio(video_path)
        transcript = ""
        if audio_path:
            try:
                from services.audio_analysis_service import transcribe_audio_file
                transcript = transcribe_audio_file(audio_path)
                result["transcript"] = transcript
            except Exception as e:
                logger.debug("Audio transcription failed: %s", e)
            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        # --- Step 5: Combine and derive insights ---
        # Topics from captions + transcript
        all_text = " ".join(captions) + " " + transcript
        result["detected_topics"] = _extract_topics(all_text)

        # Hook strength = how interesting the first frame caption is
        result["hook_strength"] = _estimate_hook_strength(captions)

        # Pacing score = visual variety across frames
        result["pacing_score"] = _estimate_pacing(visual_themes)

    finally:
        # Cleanup temp files
        try:
            os.unlink(video_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Derived metrics
# ---------------------------------------------------------------------------

TOPIC_KEYWORDS = {
    "AI": ["ai", "artificial", "machine learning", "neural", "gpt"],
    "Technology": ["tech", "software", "app", "code", "digital"],
    "Marketing": ["brand", "marketing", "growth", "engagement"],
    "Entertainment": ["movie", "music", "celebrity", "show"],
    "Lifestyle": ["health", "fitness", "food", "travel"],
    "Education": ["learn", "tutorial", "explain", "teach"],
    "Humor": ["funny", "joke", "meme", "laugh", "comedy"],
}


def _extract_topics(text: str) -> List[str]:
    """Extract detected topics from combined text."""
    tl = text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            topics.append(topic)
    return topics[:5] if topics else ["General"]


def _estimate_hook_strength(captions: List[str]) -> float:
    """Estimate hook strength based on first frame's caption."""
    if not captions:
        return 0.3
    first = captions[0].lower()
    # Engaging visual hooks
    hook_signals = ["person", "face", "text", "shocking", "bright", "colorful"]
    score = 0.4
    for signal in hook_signals:
        if signal in first:
            score += 0.1
    return min(1.0, round(score, 2))


def _estimate_pacing(visual_themes: List[str]) -> float:
    """Estimate pacing from visual variety across frames."""
    if not visual_themes:
        return 0.3
    unique = len(set(visual_themes))
    total = len(visual_themes)
    variety = unique / total if total > 0 else 0
    # Some variety is good, too much is chaotic
    if variety > 0.8:
        return round(0.7 + (1.0 - variety) * 0.3, 2)
    return round(0.3 + variety * 0.7, 2)
