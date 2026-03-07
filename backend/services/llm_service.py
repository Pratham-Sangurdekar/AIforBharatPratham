"""
LLM Service — Abstraction layer for AI analysis.
Supports: Amazon Bedrock (Claude 3 Haiku) | Local heuristic fallback.

The service is portable: swap the backend by changing ENGAUGE_ENV.
Uses a structured expert social-media growth strategist prompt for deep
content analysis, returning strict JSON with virality_score, content_dna,
trend_alignment, predicted_metrics, suggestions, and optimized_variants.
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, List

from config import is_aws, BEDROCK_MODEL_ID, BEDROCK_MAX_TOKENS, AWS_REGION, USE_LLM, USE_LOCAL_LLM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded Bedrock client
# ---------------------------------------------------------------------------
_bedrock_client = None


def _get_bedrock_client():
    """Lazy-initialize and return the Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
        )
    return _bedrock_client


# ---------------------------------------------------------------------------
# Content hash for caching (Section 5)
# ---------------------------------------------------------------------------

def compute_content_hash(text: Optional[str], platform: str) -> str:
    """
    Produce a deterministic hash of (content + platform).
    Used as a cache key to avoid repeated Bedrock invocations.
    """
    payload = f"{(text or '').strip().lower()}||{platform.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_content_with_llm(
    text: Optional[str],
    content_type: str,
    trending_topics: Optional[Dict[str, Any]] = None,
    platform: str = "general",
    media_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run full content analysis via LLM.
    Priority: Local Ollama → Bedrock → Heuristic fallback.
    """
    # --- Try local LLM first (free, no API key needed) ---
    if USE_LOCAL_LLM:
        try:
            from services.local_llm_service import analyze_content_with_local_llm
            return await analyze_content_with_local_llm(
                text, content_type, trending_topics, platform, media_context
            )
        except Exception as e:
            logger.warning("Local LLM unavailable, trying Bedrock: %s", e)

    # --- Try Bedrock (AWS, paid) ---
    if USE_LLM and (is_aws() or _can_use_bedrock()):
        try:
            return await _analyze_with_bedrock(
                text, content_type, trending_topics, platform
            )
        except Exception as e:
            logger.warning(
                "Bedrock analysis failed, falling back to heuristics: %s", e
            )

    # --- Heuristic fallback ---
    return _analyze_with_heuristics(text, content_type, platform)


async def generate_optimized_content(
    text: str,
    content_dna: Dict[str, Any],
    suggestions: List[str],
    platform: str = "general",
) -> List[str]:
    """Generate optimised content variants using LLM or heuristics."""
    # --- Try local LLM first ---
    if USE_LOCAL_LLM:
        try:
            from services.local_llm_service import generate_optimized_content_local
            return await generate_optimized_content_local(
                text, content_dna, suggestions, platform
            )
        except Exception as e:
            logger.warning("Local LLM variant generation unavailable: %s", e)

    if USE_LLM and (is_aws() or _can_use_bedrock()):
        try:
            return await _generate_variants_with_bedrock(
                text, content_dna, suggestions, platform
            )
        except Exception as e:
            logger.warning(
                "Bedrock variant generation failed, falling back: %s", e
            )
    from services.optimization_engine import OptimizationEngine
    return OptimizationEngine.generate_optimized_variants(
        text, content_dna, suggestions
    )


# ---------------------------------------------------------------------------
# Bedrock helpers
# ---------------------------------------------------------------------------

def _can_use_bedrock() -> bool:
    """Check if Bedrock credentials are available."""
    try:
        import boto3
        sts = boto3.client("sts", region_name=AWS_REGION)
        sts.get_caller_identity()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM_PROMPT = (
    "You are ENGAUGE — an expert social-media growth strategist and content "
    "performance analyst. Your job is to deeply analyse a piece of creator "
    "content and produce an actionable intelligence report.\n\n"
    "Evaluation dimensions (weight each independently):\n"
    "1. Hook strength — Does the first line create an immediate curiosity "
    "gap, pattern interrupt, or emotional jolt?\n"
    "2. Emotional triggers — Which primary emotion does the content leverage? "
    "How intense is it?\n"
    "3. Content structure — Is there a clear hook-build-payoff arc or a "
    "single punchline?\n"
    "4. Psychological persuasion — Identify Cialdini-style triggers "
    "(curiosity gap, social proof, scarcity, authority, relatability, FOMO).\n"
    "5. Trend alignment — Given the current trending topics, how well does "
    "this content ride an existing wave?\n"
    "6. Platform suitability — Is the content optimised for the target "
    "platform conventions?\n\n"
    "Scoring rubric:\n"
    "- 0-20: Virtually no viral potential; generic or off-topic.\n"
    "- 21-40: Below average; missing a strong hook or emotional core.\n"
    "- 41-60: Average; one or two strong elements but lacks synergy.\n"
    "- 61-80: Above average; multiple viral elements working together.\n"
    "- 81-100: Exceptional; strong hook + emotion + trend + structure "
    "alignment.\n\n"
    "STRICT OUTPUT FORMAT — return ONLY a valid JSON object, no markdown "
    "fences, no prose before or after."
)

_VARIANT_SYSTEM_PROMPT = (
    "You are ENGAUGE — an expert content optimiser. Given original content, "
    "its Content DNA analysis, and a set of improvement suggestions, generate "
    "3 meaningfully different improved versions. Each variant should apply "
    "different subsets of the suggestions and be platform-optimised. "
    "Return ONLY a JSON array of exactly 3 strings."
)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_analysis_user_prompt(
    text: Optional[str],
    content_type: str,
    platform: str,
    trending_topics: Optional[Dict[str, Any]],
) -> str:
    """Build the user-turn prompt injected with content and trending context."""
    # Inject up to 20 trending topics
    trends_block = ""
    if trending_topics:
        trend_lines: List[str] = []
        count = 0
        for category, data in trending_topics.items():
            topics = data.get("topics", []) if isinstance(data, dict) else []
            for t in topics:
                label = t if isinstance(t, str) else t.get("text", str(t))
                trend_lines.append(f"- [{category}] {label}")
                count += 1
                if count >= 20:
                    break
            if count >= 20:
                break
        if trend_lines:
            trends_block = "Current Trending Topics:\n" + "\n".join(trend_lines)

    return (
        "Analyse the following creator content.\n\n"
        f"Content Type: {content_type}\n"
        f"Target Platform: {platform}\n\n"
        "--- CONTENT START ---\n"
        f"{text or '[Media-only content — no text provided]'}\n"
        "--- CONTENT END ---\n\n"
        f"{trends_block}\n\n"
        "Return ONLY a valid JSON object with these exact keys:\n"
        "{\n"
        '  "virality_score": <float 0-100>,\n'
        '  "explanation": "<2-3 sentence explanation of the score>",\n'
        '  "content_dna": {\n'
        '    "hook": "<hook type: curiosity hook | contrarian hook | story hook | data hook | urgency hook | question hook | visual hook | direct statement>",\n'
        '    "emotion": "<primary emotion: surprise | curiosity | anger | joy | fear | inspiration | neutral>",\n'
        '    "structure": "<structure: hook build payoff | hook payoff | single statement | visual narrative>",\n'
        '    "psychological_triggers": ["<trigger>", "..."]\n'
        "  },\n"
        '  "trend_alignment": {\n'
        '    "matched_topics": ["<matched trending topic strings>"],\n'
        '    "relevance_score": <float 0.0-1.0>\n'
        "  },\n"
        '  "predicted_metrics": {\n'
        '    "likes": <int>,\n'
        '    "shares": <int>,\n'
        '    "comments": <int>\n'
        "  },\n"
        '  "suggestions": ["<3-6 specific, actionable improvement suggestions>"],\n'
        '  "optimized_variants": ["<3 meaningfully different rewritten versions>"]\n'
        "}"
    )


# ---------------------------------------------------------------------------
# Bedrock calls
# ---------------------------------------------------------------------------

async def _analyze_with_bedrock(
    text: Optional[str],
    content_type: str,
    trending_topics: Optional[Dict[str, Any]],
    platform: str,
) -> Dict[str, Any]:
    """Call Bedrock Claude 3 Haiku for full content analysis."""
    client = _get_bedrock_client()
    user_prompt = _build_analysis_user_prompt(
        text, content_type, platform, trending_topics
    )

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": BEDROCK_MAX_TOKENS,
        "temperature": 0.4,
        "system": _ANALYSIS_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    })

    try:
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
    except Exception as exc:
        logger.error("Bedrock invoke_model error: %s", exc)
        raise

    response_body = json.loads(response["body"].read())
    assistant_text = response_body["content"][0]["text"]
    result = _extract_json(assistant_text)
    return _validate_analysis_result(result)


async def _generate_variants_with_bedrock(
    text: str,
    content_dna: Dict[str, Any],
    suggestions: List[str],
    platform: str,
) -> List[str]:
    """Use Bedrock to generate optimised content variants."""
    client = _get_bedrock_client()

    user_prompt = (
        f'Original Content:\n"""{text}"""\n\n'
        f"Content DNA: {json.dumps(content_dna)}\n"
        f"Suggestions to apply: {json.dumps(suggestions)}\n"
        f"Target Platform: {platform}\n\n"
        "Return ONLY a JSON array with exactly 3 strings."
    )

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": BEDROCK_MAX_TOKENS,
        "temperature": 0.7,
        "system": _VARIANT_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_prompt}],
    })

    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    assistant_text = response_body["content"][0]["text"]
    variants = _extract_json(assistant_text)
    if isinstance(variants, list) and len(variants) >= 1:
        return variants[:3]

    # Fallback to heuristic variants
    from services.optimization_engine import OptimizationEngine
    return OptimizationEngine.generate_optimized_variants(
        text, content_dna, suggestions
    )


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

def _analyze_with_heuristics(
    text: Optional[str],
    content_type: str,
    platform: str,
) -> Dict[str, Any]:
    """Use existing rule-based engines as fallback when Bedrock is unavailable."""
    from services.viral_score_engine import ViralScoreEngine
    from services.optimization_engine import OptimizationEngine
    from services.trend_engine import TrendEngine

    content_dna = ViralScoreEngine.analyze_content_dna(text, content_type)
    trend_alignment = TrendEngine.analyze_trend_alignment(text, content_type)
    virality_score = ViralScoreEngine.calculate_virality_score(
        text, content_type, content_dna, trend_alignment["relevance_score"]
    )
    predicted_metrics = ViralScoreEngine.predict_engagement(virality_score)
    suggestions = OptimizationEngine.generate_suggestions(
        text, content_dna, trend_alignment, virality_score
    )
    optimized_variants = OptimizationEngine.generate_optimized_variants(
        text, content_dna, suggestions
    )

    # Build a human-readable explanation
    hook = content_dna.get("hook", "direct statement")
    emotion = content_dna.get("emotion", "neutral")
    topics = trend_alignment.get("matched_topics", [])

    parts: List[str] = []
    if virality_score >= 70:
        parts.append("Strong viral potential detected.")
    elif virality_score >= 40:
        parts.append("Moderate engagement potential.")
    else:
        parts.append("Content needs optimization for better reach.")
    parts.append(f"Uses a {hook} with {emotion} tone.")
    if topics:
        parts.append(f"Aligns with trends: {', '.join(topics[:3])}.")

    return {
        "content_dna": content_dna,
        "virality_score": virality_score,
        "explanation": " ".join(parts),
        "suggestions": suggestions,
        "optimized_variants": optimized_variants,
        "trend_alignment": trend_alignment,
        "predicted_metrics": predicted_metrics,
    }


# ---------------------------------------------------------------------------
# JSON extraction & validation helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Any:
    """Extract JSON from LLM response text (handles markdown fences)."""
    import re

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code-fence extraction
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Brute-force: find outermost { } or [ ]
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        idx_start = text.find(start_char)
        idx_end = text.rfind(end_char)
        if idx_start != -1 and idx_end > idx_start:
            try:
                return json.loads(text[idx_start : idx_end + 1])
            except json.JSONDecodeError:
                pass

    logger.error("Failed to extract JSON from LLM response: %s", text[:200])
    return {}


def _validate_analysis_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required fields exist with sensible defaults."""
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
    # Clamp score to 0-100
    result["virality_score"] = max(
        0.0, min(100.0, float(result["virality_score"]))
    )
    return result
