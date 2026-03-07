"""
Audio Analysis Service — Transcribes and analyses audio content.

Uses OpenAI Whisper (free, local, open-source) for speech-to-text
and derives engagement/topic/emotion metrics from the transcript.

Output (full analysis):
  {
    transcript: str,
    emotional_tone: str,
    topic_keywords: List[str],
    engagement_potential: float,
    language: str,
    word_count: int,
    speech_pace: str,          // slow | moderate | fast
    key_phrases: List[str],
  }
"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton Whisper model
# ---------------------------------------------------------------------------
_whisper_model = None
_WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny | base | small


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info("Loading Whisper model '%s' …", _WHISPER_MODEL_SIZE)
            _whisper_model = whisper.load_model(_WHISPER_MODEL_SIZE)
            logger.info("Whisper model loaded.")
        except ImportError:
            logger.warning("openai-whisper not installed — audio analysis unavailable")
        except Exception as e:
            logger.warning("Failed to load Whisper model: %s", e)
    return _whisper_model


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe_audio_file(audio_path: str) -> str:
    """Transcribe an audio file using Whisper. Returns plain-text transcript."""
    model = _load_whisper()
    if model is None:
        return ""
    try:
        result = model.transcribe(audio_path, fp16=False)
        return result.get("text", "").strip()
    except Exception as e:
        logger.warning("Whisper transcription failed: %s", e)
        return ""


def transcribe_audio_bytes(audio_bytes: bytes, ext: str = ".wav") -> str:
    """Transcribe raw audio bytes. Writes to temp file then delegates."""
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.close()
        return transcribe_audio_file(tmp.name)
    finally:
        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# Full Analysis
# ---------------------------------------------------------------------------

async def analyze_audio(audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
    """
    Transcribe audio and derive engagement/topic/emotion metrics.
    Runs the heavy Whisper inference in a thread pool.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_audio_sync, audio_bytes, filename)


def _analyze_audio_sync(audio_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
    """Synchronous audio analysis — called from thread pool."""
    result: Dict[str, Any] = {
        "transcript": "",
        "emotional_tone": "neutral",
        "topic_keywords": [],
        "engagement_potential": 0.5,
        "language": "en",
        "word_count": 0,
        "speech_pace": "moderate",
        "key_phrases": [],
    }

    ext = os.path.splitext(filename)[-1] or ".wav"
    transcript = transcribe_audio_bytes(audio_bytes, ext)
    if not transcript:
        return result

    result["transcript"] = transcript
    words = transcript.split()
    result["word_count"] = len(words)

    # --- Detect language (via Whisper) ---
    model = _load_whisper()
    if model is not None:
        try:
            import whisper
            tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            tmp.write(audio_bytes)
            tmp.close()
            audio_arr = whisper.load_audio(tmp.name)
            audio_arr = whisper.pad_or_trim(audio_arr)
            mel = whisper.log_mel_spectrogram(audio_arr).to(model.device)
            _, probs = model.detect_language(mel)
            result["language"] = max(probs, key=probs.get)
            os.unlink(tmp.name)
        except Exception:
            pass

    # --- Topic keywords ---
    result["topic_keywords"] = _extract_keywords(transcript)

    # --- Key phrases ---
    result["key_phrases"] = _extract_key_phrases(transcript)

    # --- Emotional tone ---
    result["emotional_tone"] = _detect_emotion(transcript)

    # --- Speech pace ---
    result["speech_pace"] = _estimate_pace(len(words))

    # --- Engagement potential ---
    result["engagement_potential"] = _estimate_engagement(
        transcript, result["emotional_tone"], result["speech_pace"]
    )

    return result


# ---------------------------------------------------------------------------
# NLP helpers (lightweight, no extra deps)
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "i me my myself we our ours ourselves you your yours yourself yourselves "
    "he him his himself she her hers herself it its itself they them their "
    "theirs themselves what which who whom this that these those am is are was "
    "were be been being have has had having do does did doing a an the and but "
    "if or because as until while of at by for with about against between "
    "through during before after above below to from up down in out on off "
    "over under again further then once here there when where why how all "
    "both each few more most other some such no nor not only own same so "
    "than too very s t can will just don should now d ll m o re ve y ain "
    "aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan "
    "shouldn wasn weren won wouldn".split()
)


def _extract_keywords(text: str, top_n: int = 8) -> List[str]:
    """Extract most frequent meaningful words as topic keywords."""
    from collections import Counter
    words = [
        w.lower().strip(".,!?\"'()[]{}:;—-") for w in text.split()
        if len(w) > 3
    ]
    filtered = [w for w in words if w and w not in _STOP_WORDS]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def _extract_key_phrases(text: str, max_phrases: int = 5) -> List[str]:
    """Extract simple key phrases using bigrams."""
    from collections import Counter
    words = [
        w.lower().strip(".,!?\"'()[]{}:;—-") for w in text.split()
    ]
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)
               if words[i] not in _STOP_WORDS and words[i+1] not in _STOP_WORDS
               and len(words[i]) > 2 and len(words[i+1]) > 2]
    return [b for b, _ in Counter(bigrams).most_common(max_phrases)]


_EMOTION_WORDS: Dict[str, List[str]] = {
    "excitement": ["amazing", "incredible", "awesome", "exciting", "wow", "insane", "unbelievable"],
    "humor": ["funny", "joke", "hilarious", "lol", "haha", "laugh", "comedy"],
    "anger": ["angry", "furious", "outrage", "rage", "aggravating", "annoying"],
    "sadness": ["sad", "depressing", "heartbreaking", "tragic", "unfortunate"],
    "inspiration": ["inspire", "motivate", "believe", "dream", "achieve", "success"],
    "fear": ["scary", "terrifying", "afraid", "dangerous", "warning", "threat"],
    "curiosity": ["why", "how", "secret", "mystery", "hidden", "discover", "truth"],
}


def _detect_emotion(text: str) -> str:
    tl = text.lower()
    scores: Dict[str, int] = {}
    for emotion, keywords in _EMOTION_WORDS.items():
        scores[emotion] = sum(1 for kw in keywords if kw in tl)
    best = max(scores, key=scores.get) if scores else "neutral"
    return best if scores.get(best, 0) > 0 else "neutral"


def _estimate_pace(word_count: int, duration_sec: float = 30.0) -> str:
    """Estimate speech pace based on word count within first 30 seconds."""
    wpm = word_count * (60 / duration_sec)
    if wpm < 100:
        return "slow"
    elif wpm > 170:
        return "fast"
    return "moderate"


def _estimate_engagement(transcript: str, emotion: str, pace: str) -> float:
    """Heuristic engagement potential 0-1."""
    score = 0.4
    # Emotion bonus
    high_engagement_emotions = {"excitement", "humor", "curiosity", "inspiration"}
    if emotion in high_engagement_emotions:
        score += 0.2
    # Pace bonus
    if pace == "moderate":
        score += 0.1
    elif pace == "fast":
        score += 0.05  # fast can overwhelm
    # Question marks indicate engagement hooks
    questions = transcript.count("?")
    score += min(0.15, questions * 0.05)
    # Exclamation marks indicate energy
    excl = transcript.count("!")
    score += min(0.1, excl * 0.03)
    return round(min(1.0, score), 2)
