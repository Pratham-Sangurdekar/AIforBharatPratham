"""
Image Analysis Service — Real image understanding using open-source models.

Uses BLIP (Bootstrapping Language-Image Pre-training) for captioning
and CLIP for visual-text similarity scoring.

Models are loaded ONCE at startup via singleton pattern (Section 12).
All processing is local and free.

Returns:
  {
    caption: str,
    detected_objects: List[str],
    visual_theme: str,
    emotional_tone: str,
    meme_probability: float,
  }
"""

import logging
import io
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton model holders (loaded once, reused)
# ---------------------------------------------------------------------------

_blip_processor = None
_blip_model = None
_clip_model = None
_clip_processor = None
_models_loaded = False
_models_available = False


def _load_models():
    """Load BLIP and CLIP models once. Thread-safe via GIL for first call."""
    global _blip_processor, _blip_model, _clip_model, _clip_processor
    global _models_loaded, _models_available

    if _models_loaded:
        return _models_available

    _models_loaded = True

    # Suppress ALL noisy output during model loading.
    # The transformers library prints progress bars, warnings, and load reports
    # directly to stdout/stderr (bypassing logging), which causes SIGTTOU when
    # the server runs as a background process.
    import os, sys, contextlib

    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    try:
        import transformers
        transformers.logging.set_verbosity_error()
    except Exception:
        pass

    devnull = open(os.devnull, "w")
    old_stdout, old_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout, sys.stderr = devnull, devnull

        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            _blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            _blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
        except Exception as e:
            pass  # logged below after restoring stderr

        try:
            from transformers import CLIPProcessor, CLIPModel
            _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        except Exception as e:
            pass  # logged below after restoring stderr
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        devnull.close()

    if _blip_model is not None:
        logger.info("BLIP model loaded successfully")
    else:
        logger.warning("BLIP model not available")

    if _clip_model is not None:
        logger.info("CLIP model loaded successfully")
    else:
        logger.warning("CLIP model not available")

    _models_available = _blip_model is not None or _clip_model is not None
    return _models_available


def models_available() -> bool:
    """Check if image analysis models are loaded."""
    return _load_models()


# ---------------------------------------------------------------------------
# BLIP Captioning
# ---------------------------------------------------------------------------

def _generate_caption(image) -> str:
    """Generate a natural language caption from a PIL Image."""
    if _blip_processor is None or _blip_model is None:
        return ""
    try:
        inputs = _blip_processor(image, return_tensors="pt")
        output = _blip_model.generate(**inputs, max_new_tokens=50)
        caption = _blip_processor.decode(output[0], skip_special_tokens=True)
        return caption.strip()
    except Exception as e:
        logger.warning("BLIP captioning failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# CLIP classification
# ---------------------------------------------------------------------------

# Labels used for zero-shot classification
THEME_LABELS = [
    "nature landscape", "urban city", "food photography", "portrait face",
    "technology gadget", "animal pet", "meme humor", "fashion style",
    "sports fitness", "art illustration", "text screenshot", "product photo",
    "travel adventure", "selfie", "infographic chart",
]

EMOTION_LABELS = [
    "happy joyful", "sad melancholy", "angry intense", "calm peaceful",
    "exciting energetic", "funny humorous", "inspiring motivational",
    "shocking surprising", "neutral boring",
]

MEME_LABELS = ["meme", "not a meme"]


def _classify_image(image, labels: List[str]) -> List[Dict[str, float]]:
    """CLIP zero-shot classification — returns list of {label, score}."""
    if _clip_processor is None or _clip_model is None:
        return []
    try:
        import torch
        inputs = _clip_processor(text=labels, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = _clip_model(**inputs)
        logits = outputs.logits_per_image[0]
        probs = logits.softmax(dim=0).tolist()
        results = [{"label": l, "score": round(s, 4)} for l, s in zip(labels, probs)]
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    except Exception as e:
        logger.warning("CLIP classification failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

async def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Full image analysis pipeline (async-safe).
    Runs heavy inference in a thread pool to avoid blocking the event loop.
    Returns dict with caption, detected_objects, visual_theme,
    emotional_tone, meme_probability.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_image_blocking, image_bytes)


def analyze_image_sync(image_bytes: bytes) -> Dict[str, Any]:
    """Synchronous version for use in video frame analysis (called from thread pool)."""
    return _analyze_image_blocking(image_bytes)


def _analyze_image_blocking(image_bytes: bytes) -> Dict[str, Any]:
    """Pure synchronous implementation."""
    if not _load_models():
        return _fallback_result()

    try:
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return _fallback_result()

    caption = _generate_caption(image)
    theme_results = _classify_image(image, THEME_LABELS)
    visual_theme = theme_results[0]["label"] if theme_results else "unknown"
    detected_objects = [r["label"] for r in theme_results[:5]]
    emotion_results = _classify_image(image, EMOTION_LABELS)
    emotional_tone = emotion_results[0]["label"] if emotion_results else "neutral"
    meme_results = _classify_image(image, MEME_LABELS)
    meme_prob = 0.0
    for r in meme_results:
        if r["label"] == "meme":
            meme_prob = r["score"]
            break

    return {
        "caption": caption or "Image content",
        "detected_objects": detected_objects,
        "visual_theme": visual_theme,
        "emotional_tone": emotional_tone,
        "meme_probability": round(meme_prob, 3),
    }


def _fallback_result() -> Dict[str, Any]:
    """Return placeholder when models are not available."""
    return {
        "caption": "Image content (models not loaded)",
        "detected_objects": [],
        "visual_theme": "unknown",
        "emotional_tone": "neutral",
        "meme_probability": 0.0,
    }
