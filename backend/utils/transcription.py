"""
Transcription utilities.

TODO: Integrate Whisper or similar ASR model for audio/video transcription.
"""

from typing import Optional


def transcribe_audio(file_path: str) -> Optional[str]:
    """
    Transcribe audio from a file.
    Currently returns a placeholder — replace with Whisper API integration.
    """
    # TODO: Integrate OpenAI Whisper or similar model
    return "[Audio transcription placeholder — integrate Whisper for production]"


def transcribe_video(file_path: str) -> Optional[str]:
    """
    Extract and transcribe audio from a video file.
    Currently returns a placeholder.
    """
    # TODO: Extract audio track, then run through Whisper
    return "[Video transcription placeholder — integrate Whisper for production]"
