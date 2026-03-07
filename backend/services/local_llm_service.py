"""
Local LLM Service — Inference via Ollama (100 % free, runs locally).

Connects to the Ollama REST API at http://localhost:11434/api/generate.
Supports: llama3 · mistral · phi3

Falls back to heuristic scoring when Ollama is unreachable.

Configuration:
  USE_LOCAL_LLM=true   (env var or .env)
  LOCAL_LLM_MODEL=mistral  (default model)
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_GENERATE = f"{OLLAMA_BASE}/api/generate"

import os

LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "mistral")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))  # seconds

# Singleton flag — set to True once we've verified connectivity
_ollama_available: Optional[bool] = None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def is_ollama_available() -> bool:
    """Ping Ollama; cache result so we don't spam the health endpoint."""
    global _ollama_available
    if _ollama_available is not None:
        return _ollama_available
    try:
        req = Request(OLLAMA_BASE, method="GET")
        with urlopen(req, timeout=3) as resp:
            _ollama_available = resp.status == 200
    except Exception:
        _ollama_available = False
    logger.info("Ollama available: %s", _ollama_available)
    return _ollama_available


def reset_availability_cache() -> None:
    """Force re-check on next call (useful after Ollama restarts)."""
    global _ollama_available
    _ollama_available = None


# ---------------------------------------------------------------------------
# Low-level generation
# ---------------------------------------------------------------------------

def _generate_sync(prompt: str, system: Optional[str] = None, temperature: float = 0.4) -> str:
    """
    Blocking call to Ollama /api/generate.
    Returns the raw text response.
    """
    body: Dict[str, Any] = {
        "model": LOCAL_LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        body["system"] = system

    data = json.dumps(body).encode("utf-8")
    req = Request(
        OLLAMA_GENERATE,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("response", "")


async def generate(prompt: str, system: Optional[str] = None, temperature: float = 0.4) -> str:
    """Async wrapper around the blocking Ollama call (runs in thread pool)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _generate_sync, prompt, system, temperature)


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Any:
    """Best-effort JSON extraction from potentially noisy LLM output."""
    import re

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Markdown fence
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Brute-force outermost braces / brackets
    for sc, ec in [("{", "}"), ("[", "]")]:
        s = text.find(sc)
        e = text.rfind(ec)
        if s != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                pass

    logger.warning("JSON extraction failed from local LLM output (first 300 chars): %s", text[:300])
    return {}


# ---------------------------------------------------------------------------
# System prompts (reuse from llm_service)
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM_PROMPT = (
    "You are ENGAUGE — an expert social-media growth strategist, content "
    "performance analyst, and virality researcher. Analyse the content and "
    "return ONLY a valid JSON object with these exact keys:\n"
    "{\n"
    '  "virality_score": <float 0-100>,\n'
    '  "explanation": "<2-3 sentences explaining the score>",\n'
    '  "content_dna": {\n'
    '    "hook": "<hook type — one of: curiosity_gap | contrarian | story | data | urgency | question | shock | statistic | visual>",\n'
    '    "emotion": "<primary emotion — one of: curiosity | surprise | anger | joy | fear | inspiration | humor | nostalgia | awe>",\n'
    '    "structure": "<structure pattern — one of: hook_build_payoff | problem_solution | story_arc | listicle | single_statement | comparison | thread | tutorial>",\n'
    '    "psychological_triggers": ["<trigger from: curiosity_gap | social_proof | scarcity | authority | relatability | fomo | controversy | identity | reciprocity>", ...],\n'
    '    "hook_strength": <float 0.0-1.0>,\n'
    '    "emotional_intensity": <float 0.0-1.0>,\n'
    '    "clarity_score": <float 0.0-1.0 — how clear the message is>\n'
    "  },\n"
    '  "trend_alignment": {\n'
    '    "matched_topics": [...],\n'
    '    "relevance_score": <0.0-1.0>\n'
    "  },\n"
    '  "predicted_metrics": {"likes": <int>, "shares": <int>, "comments": <int>},\n'
    '  "suggestions": ["<actionable improvement suggestion>", ...],\n'
    '  "optimized_variants": ["<improved version 1>", "<improved version 2>", "<improved version 3>"]\n'
    "}\n"
    "Hook types: curiosity_gap (hints at hidden info), contrarian (unpopular opinion), story (personal narrative), "
    "data (stats/research), urgency (time pressure), question (provocative question), shock (surprising claim), "
    "statistic (specific number), visual (striking image/video).\n"
    "Psychological triggers: curiosity_gap, social_proof, scarcity, authority, relatability, fomo, controversy, identity, reciprocity.\n"
    "Do NOT wrap the JSON in markdown fences. Return ONLY the JSON."
)

_VARIANT_SYSTEM_PROMPT = (
    "You are ENGAUGE — an expert content optimiser. Given original content, "
    "its Content DNA analysis, and a set of improvement suggestions, generate "
    "3 meaningfully different improved versions. Return ONLY a JSON array of "
    "exactly 3 strings. No markdown fences."
)


# ---------------------------------------------------------------------------
# Public high-level API (mirrors llm_service signatures)
# ---------------------------------------------------------------------------

async def analyze_content_with_local_llm(
    text: Optional[str],
    content_type: str,
    trending_topics: Optional[Dict[str, Any]] = None,
    platform: str = "general",
    media_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyse content using the local Ollama model.
    Falls back to heuristics if Ollama is not available.
    """
    if not is_ollama_available():
        logger.info("Ollama not available, falling back to heuristics")
        return _heuristic_fallback(text, content_type, platform)

    user_prompt = _build_user_prompt(text, content_type, platform, trending_topics, media_context)

    try:
        raw = await generate(user_prompt, system=_ANALYSIS_SYSTEM_PROMPT, temperature=0.4)
        result = _extract_json(raw)
        return _validate(result)
    except Exception as e:
        logger.warning("Local LLM analysis failed: %s — falling back to heuristics", e)
        return _heuristic_fallback(text, content_type, platform)


async def generate_optimized_content_local(
    text: str,
    content_dna: Dict[str, Any],
    suggestions: List[str],
    platform: str = "general",
) -> List[str]:
    """Generate optimised content variants using Ollama."""
    if not is_ollama_available():
        from services.optimization_engine import OptimizationEngine
        return OptimizationEngine.generate_optimized_variants(text, content_dna, suggestions)

    user_prompt = (
        f'Original Content:\n"""{text}"""\n\n'
        f"Content DNA: {json.dumps(content_dna)}\n"
        f"Suggestions: {json.dumps(suggestions)}\n"
        f"Target Platform: {platform}\n\n"
        "Return ONLY a JSON array with exactly 3 strings."
    )

    try:
        raw = await generate(user_prompt, system=_VARIANT_SYSTEM_PROMPT, temperature=0.7)
        parsed = _extract_json(raw)
        if isinstance(parsed, list) and len(parsed) >= 1:
            return [str(v) for v in parsed[:3]]
    except Exception as e:
        logger.warning("Local LLM variant generation failed: %s", e)

    from services.optimization_engine import OptimizationEngine
    return OptimizationEngine.generate_optimized_variants(text, content_dna, suggestions)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_user_prompt(
    text: Optional[str],
    content_type: str,
    platform: str,
    trending_topics: Optional[Dict[str, Any]],
    media_context: Optional[Dict[str, Any]] = None,
) -> str:
    """Build the user-turn prompt with content + trend context + media analysis."""
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
            parts.append(f"Image caption: {media_context['caption']}")
        if media_context.get("transcript"):
            parts.append(f"Audio transcript: {media_context['transcript'][:500]}")
        if media_context.get("visual_theme"):
            parts.append(f"Visual theme: {media_context['visual_theme']}")
        if media_context.get("emotional_tone"):
            parts.append(f"Emotional tone: {media_context['emotional_tone']}")
        if media_context.get("detected_objects"):
            parts.append(f"Detected objects: {', '.join(media_context['detected_objects'][:10])}")
        if parts:
            media_block = "Media Analysis:\n" + "\n".join(parts)

    return (
        "Analyse the following creator content.\n\n"
        f"Content Type: {content_type}\n"
        f"Target Platform: {platform}\n\n"
        "--- CONTENT START ---\n"
        f"{text or '[Media-only content — no text provided]'}\n"
        "--- CONTENT END ---\n\n"
        f"{trends_block}\n\n"
        f"{media_block}\n\n"
        "Return ONLY the JSON object as described."
    )


# ---------------------------------------------------------------------------
# Validation + heuristic fallback
# ---------------------------------------------------------------------------

def _validate(result: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required keys with sensible defaults."""
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


def _heuristic_fallback(text: Optional[str], content_type: str, platform: str) -> Dict[str, Any]:
    """Use existing rule-based engines as fallback."""
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
