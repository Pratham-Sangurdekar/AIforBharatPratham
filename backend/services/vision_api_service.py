"""
Vision API Service — Remote Image Analysis

Primary:  Groq Llama 3.2 Vision (fast, reliable, already-configured API key)
Fallback: Replicate LLaVA / BLIP-2 (if Groq vision unavailable)

Sends extracted video frames as base64 images and returns per-frame captions
plus aggregated visual tags.

No local ML models are loaded.
"""

import os
import asyncio
import base64
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq Vision configuration
# ---------------------------------------------------------------------------
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ---------------------------------------------------------------------------
# Tag keywords to detect in captions
# ---------------------------------------------------------------------------
_TAG_KEYWORDS = {
    "person speaking": ["speak", "talk", "person", "man", "woman", "face", "looking at camera", "someone"],
    "text overlay": ["text", "word", "caption", "title", "subtitle", "writing", "overlay", "letter"],
    "product demo": ["product", "hold", "show", "unbox", "review", "device", "item", "brand"],
    "tutorial": ["how to", "step", "tutorial", "instruction", "guide", "demonstrat", "explain"],
    "reaction": ["react", "surprise", "shock", "laugh", "scream", "emotion", "excited"],
    "meme": ["meme", "funny", "joke", "humor", "comic"],
}


def _encode_image_b64(image_path: str) -> str:
    """Read image file → raw base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---------------------------------------------------------------------------
# Groq Vision (PRIMARY)
# ---------------------------------------------------------------------------

async def _analyze_frame_groq(image_path: str) -> str:
    """Send a single frame to Groq Llama 3.2 Vision and return a caption."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return ""  # will trigger fallback

    try:
        from groq import Groq
    except ImportError:
        return ""

    b64 = _encode_image_b64(image_path)
    data_uri = f"data:image/jpeg;base64,{b64}"

    client = Groq(api_key=api_key)

    def _call():
        resp = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Describe what is happening in this frame of a social media video. "
                                "Mention any people, objects, text overlays, emotions, and actions. "
                                "Keep it under 2 sentences."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri},
                        },
                    ],
                }
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:
        logger.warning("Groq Vision failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Replicate fallback
# ---------------------------------------------------------------------------

async def _analyze_frame_replicate(image_path: str) -> str:
    """Fallback: send frame to Replicate LLaVA or BLIP-2."""
    try:
        import replicate
    except ImportError:
        return "A frame from a social media video."

    if not os.getenv("REPLICATE_API_TOKEN"):
        return "A frame from a social media video."

    b64 = _encode_image_b64(image_path)
    data_uri = f"data:image/jpeg;base64,{b64}"

    # Try LLaVA first (use official model name without pinned version)
    try:
        output = await asyncio.to_thread(
            replicate.run,
            "yorickvp/llava-v1.6-mistral-7b",
            input={
                "image": data_uri,
                "prompt": "Describe what is happening in this frame of a social media video in 1-2 sentences.",
                "max_tokens": 200,
            },
        )
        return "".join(output).strip()
    except Exception as e:
        logger.warning("Replicate LLaVA failed: %s", e)

    # Try BLIP-2
    try:
        output = await asyncio.to_thread(
            replicate.run,
            "andreasjansson/blip-2",
            input={
                "image": data_uri,
                "question": "Describe what is happening in this social media video frame.",
            },
        )
        if isinstance(output, list):
            return "".join(output).strip()
        return str(output).strip()
    except Exception as e:
        logger.warning("Replicate BLIP-2 also failed: %s", e)

    return "A frame from a social media video."


# ---------------------------------------------------------------------------
# Per-frame dispatcher (Groq → Replicate → generic fallback)
# ---------------------------------------------------------------------------

async def _analyze_single_frame(image_path: str) -> str:
    """Analyse one frame. Tries Groq, then Replicate, then returns generic."""
    # Primary: Groq Vision
    caption = await _analyze_frame_groq(image_path)
    if caption:
        return caption

    # Fallback: Replicate
    caption = await _analyze_frame_replicate(image_path)
    return caption


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------

def _extract_tags(captions: List[str]) -> List[str]:
    """Heuristic tag extraction from aggregated captions."""
    combined = " ".join(captions).lower()
    found: List[str] = []
    for tag, keywords in _TAG_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            found.append(tag)
    return found


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_frames_batch(frame_paths: List[str]) -> Dict[str, Any]:
    """Analyse a batch of frames concurrently via remote vision APIs.

    Returns ``{"captions": [...], "visual_tags": [...]}``
    """
    if not frame_paths:
        return {"captions": [], "visual_tags": []}

    # Process frames with concurrency limit to avoid rate-limit floods
    semaphore = asyncio.Semaphore(3)  # max 3 concurrent API calls

    async def _limited(path: str) -> str:
        async with semaphore:
            return await _analyze_single_frame(path)

    tasks = [_limited(p) for p in frame_paths]
    captions: List[str] = list(await asyncio.gather(*tasks))

    visual_tags = _extract_tags(captions)

    logger.info(
        "Vision analysis complete: %d frames, %d tags (%s)",
        len(captions), len(visual_tags), ", ".join(visual_tags) or "none",
    )
    return {"captions": captions, "visual_tags": visual_tags}
