"""
Groq LLM Service — Free online AI inference via Groq Cloud SDK.

Uses the official `groq` Python SDK for:
  - Content analysis (text + media context → structured JSON)
  - Content variant generation

Models: llama-3.3-70b-versatile (default)
Free tier: ~30 RPM — no credit card needed.
"""

import json
import logging
import asyncio
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy client (avoids stale module-level config reads)
# ---------------------------------------------------------------------------

_groq_client = None


def _get_client():
    """Lazy-init and return a groq.Groq client."""
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        key = os.getenv("GROQ_API_KEY", "")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        _groq_client = Groq(api_key=key)
    return _groq_client


def _get_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def is_groq_available() -> bool:
    return bool(os.getenv("GROQ_API_KEY", ""))


# ---------------------------------------------------------------------------
# Low-level SDK call
# ---------------------------------------------------------------------------

def _call_groq_sync(
    messages: List[Dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 2048,
) -> str:
    """Blocking call via groq SDK. Returns raw assistant text."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=_get_model(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


async def _call_groq(
    messages: List[Dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 2048,
) -> str:
    """Async wrapper (runs blocking SDK call in thread pool)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _call_groq_sync, messages, temperature, max_tokens
    )


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Any:
    import re
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for sc, ec in [("{", "}"), ("[", "]")]:
        s = text.find(sc)
        e = text.rfind(ec)
        if s != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                pass
    logger.warning("JSON extraction failed (first 300 chars): %s", text[:300])
    return {}


# ---------------------------------------------------------------------------
# System prompts — content-type-aware
# ---------------------------------------------------------------------------

_TEXT_ANALYSIS_PROMPT = """You are ENGAUGE — an expert social-media growth strategist. Analyse the content deeply and return ONLY a valid JSON object.

CRITICAL RULES:
1. Every suggestion MUST quote specific words/phrases from the content
2. Every optimized variant MUST be a complete rewrite, not a small tweak
3. The explanation MUST reference specific elements of the content
4. Do NOT give generic advice like "add hashtags" or "post at optimal times"

Return this exact JSON structure:
{
  "virality_score": <float 0-100>,
  "explanation": "<2-3 sentences explaining WHY this specific content scores this way, referencing exact phrases>",
  "content_dna": {
    "hook": "<hook type>",
    "emotion": "<primary emotion>",
    "structure": "<structure pattern>",
    "psychological_triggers": ["<trigger>", ...],
    "hook_strength": <0.0-1.0>,
    "emotional_intensity": <0.0-1.0>,
    "clarity_score": <0.0-1.0>
  },
  "trend_alignment": {
    "matched_topics": ["<matched trending topics>"],
    "relevance_score": <0.0-1.0>
  },
  "predicted_metrics": {"likes": <int>, "shares": <int>, "comments": <int>},
  "suggestions": ["<specific suggestion quoting the content>", ...],
  "optimized_variants": ["<complete rewrite 1>", "<complete rewrite 2>", "<complete rewrite 3>"]
}
Do NOT wrap in markdown. Return ONLY the JSON."""

_IMAGE_ANALYSIS_PROMPT = """You are ENGAUGE — an expert visual content strategist. You are analysing an IMAGE post for social media.

You have been given an AI-generated description of the image. Based on this description:
1. Evaluate the image's viral potential
2. Describe what the image shows and why it works or doesn't
3. Suggest specific visual improvements (composition, color, text overlay, etc.)
4. Create 3 alternative caption/description suggestions that would go viral with this image

Return ONLY this JSON:
{
  "virality_score": <float 0-100>,
  "explanation": "<2-3 sentences about the image's strengths and weaknesses, referencing what's IN the image>",
  "content_dna": {
    "hook": "<visual hook type: striking_visual | contrast | unexpected | emotional_scene | text_overlay | meme_format | aesthetic | raw_authentic>",
    "emotion": "<emotion the image evokes>",
    "structure": "<visual_narrative | meme | infographic | behind_the_scenes | tutorial | before_after>",
    "psychological_triggers": ["<trigger>", ...],
    "hook_strength": <0.0-1.0>,
    "emotional_intensity": <0.0-1.0>,
    "clarity_score": <0.0-1.0>
  },
  "trend_alignment": {"matched_topics": [...], "relevance_score": <0.0-1.0>},
  "predicted_metrics": {"likes": <int>, "shares": <int>, "comments": <int>},
  "suggestions": [
    "<specific visual improvement suggestion>",
    "<composition/framing suggestion>",
    "<caption/text overlay suggestion>",
    "<posting strategy suggestion>"
  ],
  "optimized_variants": [
    "<complete caption for this image, variant 1>",
    "<complete caption for this image, variant 2>",
    "<complete caption for this image, variant 3>"
  ],
  "image_analysis": {
    "description": "<detailed description of what the image shows>",
    "visual_strengths": ["<strength 1>", ...],
    "visual_weaknesses": ["<weakness 1>", ...],
    "improvement_actions": ["<specific action to improve the image>", ...]
  }
}
Do NOT wrap in markdown. Return ONLY the JSON."""

_VIDEO_ANALYSIS_PROMPT = """You are ENGAUGE — an expert video content strategist. You are analysing a VIDEO post.

You have been given AI analysis of the video (visual elements, transcript, pacing, etc.). Based on this:
1. Evaluate the video's viral potential
2. Describe the video content and pacing
3. Suggest specific improvements for hook, pacing, editing, and audio
4. If there's a transcript, suggest script improvements

Return ONLY this JSON:
{
  "virality_score": <float 0-100>,
  "explanation": "<2-3 sentences about the video's viral potential, referencing specific moments/content>",
  "content_dna": {
    "hook": "<video hook type: cold_open | question | shock | preview | storytelling | challenge>",
    "emotion": "<primary emotion>",
    "structure": "<hook_build_payoff | tutorial | vlog | reaction | montage | interview | story_arc>",
    "psychological_triggers": ["<trigger>", ...],
    "hook_strength": <0.0-1.0>,
    "emotional_intensity": <0.0-1.0>,
    "clarity_score": <0.0-1.0>
  },
  "trend_alignment": {"matched_topics": [...], "relevance_score": <0.0-1.0>},
  "predicted_metrics": {"likes": <int>, "shares": <int>, "comments": <int>},
  "suggestions": [
    "<specific hook improvement>",
    "<pacing/editing suggestion>",
    "<audio/music suggestion>",
    "<thumbnail/title suggestion>"
  ],
  "optimized_variants": [
    "<improved video title/caption variant 1>",
    "<improved video title/caption variant 2>",
    "<improved video title/caption variant 3>"
  ],
  "video_analysis": {
    "content_summary": "<what the video is about>",
    "pacing_notes": "<how the pacing works or doesn't>",
    "hook_assessment": "<assessment of the first 3 seconds>",
    "audio_notes": "<assessment of audio/music/voiceover>",
    "improvement_actions": ["<specific action>", ...]
  }
}
Do NOT wrap in markdown. Return ONLY the JSON."""

_VARIANT_SYSTEM_PROMPT = (
    "You are ENGAUGE — an expert content optimiser. Given original content, "
    "its Content DNA analysis, and improvement suggestions, generate "
    "3 meaningfully different improved versions. Each must be a COMPLETE rewrite "
    "that applies different subsets of the suggestions. "
    "Return ONLY a JSON array of exactly 3 strings. No markdown fences."
)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_user_prompt(
    text: Optional[str],
    content_type: str,
    platform: str,
    trending_topics: Optional[Dict[str, Any]],
    media_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Build user prompt with content + trends + media context."""
    # Trending block
    trends_block = ""
    if trending_topics:
        lines: List[str] = []
        count = 0
        for category, data in trending_topics.items():
            topics = data.get("topics", []) if isinstance(data, dict) else []
            for t in topics:
                label = t if isinstance(t, str) else t.get("text", str(t))
                lines.append(f"- [{category}] {label}")
                count += 1
                if count >= 20:
                    break
            if count >= 20:
                break
        if lines:
            trends_block = "Current Trending Topics:\n" + "\n".join(lines)

    # Media context block
    media_block = ""
    if media_context:
        parts = []
        if media_context.get("caption"):
            parts.append(f"AI Image/Video Description: {media_context['caption']}")
        if media_context.get("transcript"):
            parts.append(f"Audio Transcript: {media_context['transcript'][:1000]}")
        if media_context.get("visual_theme"):
            parts.append(f"Visual Theme: {media_context['visual_theme']}")
        if media_context.get("emotional_tone"):
            parts.append(f"Emotional Tone: {media_context['emotional_tone']}")
        if media_context.get("detected_objects"):
            parts.append(f"Detected Elements: {', '.join(media_context['detected_objects'][:10])}")
        if media_context.get("composition_notes"):
            parts.append(f"Composition: {media_context['composition_notes']}")
        if media_context.get("improvement_suggestions"):
            parts.append(f"Initial Improvement Notes: {', '.join(media_context['improvement_suggestions'][:5])}")
        if media_context.get("visual_quality"):
            parts.append(f"Visual Quality: {media_context['visual_quality']}")
        if media_context.get("hook_strength") is not None:
            parts.append(f"Visual Hook Strength: {media_context['hook_strength']:.2f}")
        if media_context.get("pacing_score") is not None:
            parts.append(f"Pacing Score: {media_context['pacing_score']:.2f}")
        if parts:
            media_block = "--- MEDIA ANALYSIS ---\n" + "\n".join(parts) + "\n--- END MEDIA ANALYSIS ---"

    content_text = text or "[No text/caption provided. Analyse based on the media analysis above.]"

    return (
        f"Analyse this {content_type} content for {platform}.\n\n"
        f"--- CONTENT START ---\n{content_text}\n--- CONTENT END ---\n\n"
        f"{media_block}\n\n"
        f"{trends_block}\n\n"
        "Return ONLY the JSON. Make all suggestions SPECIFIC to this content."
    )


def _get_system_prompt(content_type: str) -> str:
    """Return the appropriate system prompt based on content type."""
    if content_type == "image":
        return _IMAGE_ANALYSIS_PROMPT
    elif content_type == "video":
        return _VIDEO_ANALYSIS_PROMPT
    return _TEXT_ANALYSIS_PROMPT


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_content_with_groq(
    text: Optional[str],
    content_type: str,
    trending_topics: Optional[Dict[str, Any]] = None,
    platform: str = "general",
    media_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Analyse content using Groq Cloud SDK."""
    if not is_groq_available():
        raise RuntimeError("GROQ_API_KEY not configured")

    system_prompt = _get_system_prompt(content_type)
    user_prompt = _build_user_prompt(text, content_type, platform, trending_topics, media_context)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw = await _call_groq(messages, temperature=0.4, max_tokens=2048)
    logger.info("Groq API returned %d chars for %s analysis", len(raw), content_type)

    result = _extract_json(raw)
    if not result:
        logger.warning("Groq returned empty/unparseable JSON")
        raise ValueError("Empty JSON from Groq")
    return _validate(result)


async def generate_optimized_content_groq(
    text: str,
    content_dna: Dict[str, Any],
    suggestions: List[str],
    platform: str = "general",
) -> List[str]:
    """Generate optimised content variants using Groq."""
    if not is_groq_available():
        raise RuntimeError("GROQ_API_KEY not configured")

    messages = [
        {"role": "system", "content": _VARIANT_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f'Original Content:\n"""{text}"""\n\n'
            f"Content DNA: {json.dumps(content_dna)}\n"
            f"Suggestions: {json.dumps(suggestions)}\n"
            f"Target Platform: {platform}\n\n"
            "Return ONLY a JSON array with exactly 3 strings."
        )},
    ]

    raw = await _call_groq(messages, temperature=0.7, max_tokens=2048)
    parsed = _extract_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return [str(v) for v in parsed[:3]]
    raise RuntimeError("Groq variant generation failed")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(result: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {
        "content_dna": {
            "hook": "direct statement",
            "emotion": "neutral",
            "structure": "single statement",
            "psychological_triggers": ["direct appeal"],
        },
        "virality_score": 50.0,
        "explanation": "Analysis completed.",
        "suggestions": [],
        "optimized_variants": [],
        "trend_alignment": {"matched_topics": [], "relevance_score": 0.0},
        "predicted_metrics": {"likes": 100, "shares": 20, "comments": 15},
    }
    for key, default in defaults.items():
        if key not in result:
            result[key] = default
    result["virality_score"] = max(0.0, min(100.0, float(result["virality_score"])))
    return result
