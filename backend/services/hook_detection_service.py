"""
Hook Detection Service — ENGAUGE Section 5

Evaluates the first ~3 seconds of a video through its transcript and
visual tags / frame captions to produce a **hook_strength** score (0–100)
and classify the hook type.

Evaluated factors:
  • Visual hook  (person, text overlay, motion)
  • Speech hook  (curiosity, shock, question)
  • Curiosity trigger
  • Emotion trigger

The score heavily impacts the final virality prediction.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword dictionaries
# ---------------------------------------------------------------------------

_CURIOSITY = [
    "secret", "reason", "why", "how to", "truth", "never", "stop",
    "don't", "nobody", "hidden", "revealed", "actually", "you won't believe",
]

_SHOCK = [
    "crazy", "insane", "hate", "worst", "best", "warning", "shocking",
    "unbelievable", "mind-blowing", "danger",
]

_QUESTION = ["have you", "did you", "what if", "are you", "?", "who", "when"]

_URGENCY = ["right now", "before it's too late", "don't miss", "hurry", "limited"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_hook(
    transcript: str,
    visual_tags: Optional[List[str]] = None,
    captions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Analyse the opening segment and return hook metrics.

    Parameters
    ----------
    transcript : str
        Full transcript — only the first ~25 words are used.
    visual_tags : list[str], optional
        High-level tags from vision API (e.g. "person speaking").
    captions : list[str], optional
        Per-frame captions — only the first caption (≈ first frame) is used.

    Returns
    -------
    dict  ``{"hook_strength": 0-100, "hook_type": str, "hook_description": str, "hook_improvement": str}``
    """
    visual_tags = visual_tags or []
    captions = captions or []

    # Approximate "first 3 seconds" of speech ≈ first 25 words
    words = transcript.lower().split() if transcript else []
    first_segment = " ".join(words[:25])

    score: float = 0.0
    hook_type = "storytelling"
    description = ""
    improvement = "Add a bold claim or question in the first 3 seconds to boost retention."

    # --- Speech analysis ---
    if any(t in first_segment for t in _QUESTION):
        score += 30
        hook_type = "question"
        description = "Opens with an engaging question that sparks curiosity."

    if any(t in first_segment for t in _CURIOSITY):
        score += 35
        hook_type = "curiosity"
        description = "Leverages a strong curiosity gap to force retention."

    if any(t in first_segment for t in _SHOCK):
        score += 40
        hook_type = "shock"
        description = "Opens with a pattern-interrupting shock phrase."

    if any(t in first_segment for t in _URGENCY):
        score += 20
        if hook_type == "storytelling":
            hook_type = "urgency"
            description = "Creates urgency that compels the viewer to keep watching."

    # --- Visual analysis ---
    if "person speaking" in visual_tags:
        score += 15

    if "text overlay" in visual_tags:
        score += 15

    # First-frame visual energy from caption
    if captions:
        first_caption = captions[0].lower()
        if any(w in first_caption for w in ["person", "face", "looking at camera"]):
            score += 10

    # --- Normalise ---
    score = min(score, 100.0)

    if score == 0:
        score = 20.0
        description = "Standard chronological opening with no distinct hook."
        improvement = (
            "Start with the conclusion, a provocative question, or an "
            "impossible-to-ignore claim rather than a slow introduction."
        )
    elif not description:
        # Visual signals fired but no speech triggers — describe what was detected
        parts = []
        if "person speaking" in visual_tags:
            parts.append("a person on camera")
        if "text overlay" in visual_tags:
            parts.append("text overlay to capture attention")
        if captions and any(w in captions[0].lower() for w in ["person", "face", "looking at camera"]):
            parts.append("direct-to-camera framing")
        if parts:
            description = "Opens with " + " and ".join(parts) + "."
        else:
            description = "Visual elements provide moderate hook potential."

    return {
        "hook_strength": round(score, 1),
        "hook_type": hook_type,
        "hook_description": description,
        "hook_improvement": improvement,
    }
