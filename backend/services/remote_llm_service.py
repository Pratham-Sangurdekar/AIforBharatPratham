"""
Remote LLM Service — Groq Llama-3 Reasoning for Video Analysis

Sends the assembled multimodal context (frame descriptions, visual tags,
transcript, hook analysis, trends) to Groq's ``llama3-70b-8192`` model
and returns a structured virality evaluation.

Endpoint:  https://api.groq.com/openai/v1/chat/completions
Model:     llama3-70b-8192

No local ML models are loaded.
"""

import os
import json
import logging
from typing import Dict, Any

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Suggestion generation (Section 9)
# ---------------------------------------------------------------------------

_DEFAULT_SUGGESTIONS = [
    "Strengthen the hook in the first 3 seconds with a bold claim or question.",
    "Add a text overlay to highlight the key message.",
    "Reference a currently trending topic to boost discoverability.",
    "Shorten the intro to improve early retention.",
    "Add a curiosity-based question to open a loop.",
    "Increase pacing — cut dead air and filler words.",
    "Use a direct call-to-action at the end.",
    "Include a visual pattern interrupt within the first 2 seconds.",
]


# ---------------------------------------------------------------------------
# Groq LLM evaluation
# ---------------------------------------------------------------------------

def evaluate_video(
    media_context: Dict[str, Any],
    trending_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Send multimodal video context + trends to Groq Llama-3 and return
    a virality evaluation dict.

    Falls back to heuristic defaults if the API is unavailable.
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not Groq or not groq_api_key:
        logger.error("Groq SDK or API key missing — returning fallback.")
        return _fallback(media_context)

    client = Groq(api_key=groq_api_key)

    # Build the prompt (Section 7)
    context_json = json.dumps(media_context, indent=2, default=str)
    trends_json = json.dumps(trending_data, indent=2, default=str)

    user_prompt = f"""You are an expert viral content strategist.

Analyze the following video.

=== VIDEO TRANSCRIPT ===
{media_context.get("transcript", "(no transcript)")}

=== FRAME DESCRIPTIONS ===
{json.dumps(media_context.get("frame_descriptions", []), indent=2)}

=== VISUAL TAGS ===
{json.dumps(media_context.get("visual_tags", []))}

=== HOOK ANALYSIS ===
Hook strength: {media_context.get("hook_strength", "N/A")}
Hook type:     {media_context.get("hook_type", "N/A")}

=== CURRENT TRENDS ===
{trends_json}

Evaluate:
1. Hook effectiveness (first 3 seconds)
2. Emotional impact
3. Visual storytelling quality
4. Trend alignment
5. Platform suitability (TikTok, Instagram Reels, YouTube Shorts)

Return ONLY a raw JSON object with this structure:
{{
    "virality_score": <float 0-100>,
    "predicted_metrics": {{
        "likes": <int>,
        "shares": <int>,
        "comments": <int>,
        "estimated_reach": <int>
    }},
    "content_dna": {{
        "hook": "<string>",
        "emotion": "<string>",
        "structure": "<string>",
        "psychological_triggers": ["<string>"],
        "hook_strength": <float 0-1.0>,
        "emotional_intensity": <float 0-1.0>,
        "clarity_score": <float 0-1.0>
    }},
    "trend_alignment": {{
        "relevance_score": <float 0-1.0>,
        "matched_trends": ["<string>"],
        "recommendation": "<string>"
    }},
    "suggestions": [
        "<string actionable improvement>"
    ],
    "optimized_variants": [
        "<string rewritten hook or script variant>"
    ]
}}

Limit suggestions to a maximum of 8.
"""

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior social media strategist. "
                        "Output ONLY raw JSON. No markdown fences."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            model=groq_model,
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        reply = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if reply.startswith("```"):
            reply = reply.split("\n", 1)[1] if "\n" in reply else reply[3:]
        if reply.endswith("```"):
            reply = reply[:-3]

        result = json.loads(reply.strip())

        # Enforce suggestion cap (Section 9)
        if "suggestions" in result:
            result["suggestions"] = result["suggestions"][:8]

        return result

    except Exception as e:
        logger.error("Groq API error: %s", e)
        return _fallback(media_context)


def _fallback(media_context: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback when Groq is unreachable."""
    hook = media_context.get("hook_strength", 50)
    if isinstance(hook, float) and hook <= 1.0:
        hook = hook * 100  # normalise to 0-100

    return {
        "virality_score": 50.0,
        "predicted_metrics": {"likes": 120, "shares": 30, "comments": 8, "estimated_reach": 2400},
        "content_dna": {
            "hook": media_context.get("hook_type", "unknown"),
            "emotion": "neutral",
            "structure": "chronological",
            "psychological_triggers": [],
            "hook_strength": min(hook / 100, 1.0),
            "emotional_intensity": 0.5,
            "clarity_score": 0.5,
        },
        "trend_alignment": {
            "relevance_score": 0.0,
            "matched_trends": [],
            "recommendation": "Unable to evaluate — AI service unavailable.",
        },
        "suggestions": _DEFAULT_SUGGESTIONS[:4],
        "optimized_variants": ["(AI evaluation unavailable — retry later)"],
    }
