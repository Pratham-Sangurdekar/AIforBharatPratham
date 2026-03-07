"""
Viral Score Engine — Hybrid AI + heuristic virality scoring.

Provides:
  - Content DNA analysis (hook, emotion, structure, psychological triggers)
  - Heuristic-only virality score (used standalone AND as a component)
  - Hybrid score blending: 0.50*AI + 0.20*trend + 0.15*hook + 0.15*emotion
  - Deterministic engagement predictions (no random jitter)
  - Score breakdown dict for frontend visualisation (Section 8)
"""

import hashlib
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Hook & emotion keyword dictionaries
# ---------------------------------------------------------------------------

HOOK_PATTERNS = {
    "curiosity hook": [
        "secret", "you won't believe", "nobody talks about", "hidden",
        "revealed", "actually",
    ],
    "contrarian hook": [
        "unpopular opinion", "hot take", "contrary", "wrong about",
        "overrated",
    ],
    "story hook": [
        "i was", "last year", "when i", "my journey", "true story",
    ],
    "data hook": [
        "study shows", "research", "statistics", "data", "percent", "%",
    ],
    "urgency hook": [
        "right now", "before it's too late", "don't miss", "hurry",
        "limited",
    ],
    "question hook": [
        "?", "have you ever", "what if", "why do", "how does",
    ],
}

EMOTION_KEYWORDS = {
    "surprise": [
        "shocking", "unbelievable", "mind-blowing", "wow", "insane", "crazy",
    ],
    "curiosity": [
        "secret", "hidden", "discover", "learn", "find out", "revealed",
    ],
    "anger": [
        "outrage", "unacceptable", "furious", "terrible", "worst",
    ],
    "joy": [
        "amazing", "incredible", "love", "beautiful", "wonderful", "awesome",
    ],
    "fear": [
        "warning", "danger", "risk", "threat", "scary", "alarming",
    ],
    "inspiration": [
        "transform", "achieve", "success", "breakthrough", "overcome", "dream",
    ],
}

PSYCHOLOGICAL_TRIGGERS = {
    "curiosity gap": ["secret", "hidden", "revealed", "you didn't know"],
    "social proof": ["everyone", "millions", "viral", "trending", "popular"],
    "scarcity": ["limited", "exclusive", "only", "rare", "last chance"],
    "authority": ["expert", "study", "research", "proven", "science"],
    "relatability": ["we all", "you know", "relatable", "same", "honestly"],
    "fomo": ["missing out", "don't miss", "before it's gone", "while you can"],
}


# ---------------------------------------------------------------------------
# Hook & emotion strength maps (used in hybrid formula — Section 2)
# ---------------------------------------------------------------------------

HOOK_STRENGTH_MAP: Dict[str, float] = {
    "curiosity hook": 0.90,
    "contrarian hook": 0.85,
    "story hook": 0.80,
    "data hook": 0.70,
    "urgency hook": 0.75,
    "question hook": 0.65,
    "visual hook": 0.70,
    "direct statement": 0.30,
}

EMOTION_INTENSITY_MAP: Dict[str, float] = {
    "surprise": 0.90,
    "curiosity": 0.85,
    "anger": 0.80,
    "joy": 0.75,
    "fear": 0.70,
    "inspiration": 0.80,
    "neutral": 0.20,
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class ViralScoreEngine:
    """Analyses content DNA and computes virality scores."""

    # ---- Detection helpers (unchanged logic) ----

    @staticmethod
    def _detect_hook(text: str) -> str:
        text_lower = text.lower()
        best_hook = "direct statement"
        best_count = 0
        for hook_type, keywords in HOOK_PATTERNS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > best_count:
                best_count = count
                best_hook = hook_type
        return best_hook

    @staticmethod
    def _detect_emotion(text: str) -> str:
        text_lower = text.lower()
        best_emotion = "neutral"
        best_count = 0
        for emotion, keywords in EMOTION_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > best_count:
                best_count = count
                best_emotion = emotion
        return best_emotion

    @staticmethod
    def _detect_structure(text: str) -> str:
        sentences = [
            s.strip()
            for s in text.replace("!", ".").replace("?", ".").split(".")
            if s.strip()
        ]
        if len(sentences) >= 3:
            return "hook build payoff"
        elif len(sentences) == 2:
            return "hook payoff"
        return "single statement"

    @staticmethod
    def _detect_psychological_triggers(text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for trigger, keywords in PSYCHOLOGICAL_TRIGGERS.items():
            if any(kw in text_lower for kw in keywords):
                found.append(trigger)
        return found if found else ["direct appeal"]

    # ---- Content DNA ----

    @staticmethod
    def analyze_content_dna(
        text: Optional[str], content_type: str
    ) -> Dict[str, Any]:
        """Return content DNA dict: hook, emotion, structure, triggers."""
        if not text or not text.strip():
            return {
                "hook": "visual hook",
                "emotion": "curiosity",
                "structure": "visual narrative",
                "psychological_triggers": ["visual appeal"],
            }
        return {
            "hook": ViralScoreEngine._detect_hook(text),
            "emotion": ViralScoreEngine._detect_emotion(text),
            "structure": ViralScoreEngine._detect_structure(text),
            "psychological_triggers": ViralScoreEngine._detect_psychological_triggers(text),
        }

    # ---- Heuristic-only score (legacy, still used as fallback) ----

    @staticmethod
    def calculate_virality_score(
        text: Optional[str],
        content_type: str,
        content_dna: Dict[str, Any],
        trend_relevance: float = 0.0,
    ) -> float:
        """Compute a virality score 0-100 from heuristic rules only."""
        score = 30.0

        hook = content_dna.get("hook", "direct statement")
        hook_scores = {
            "curiosity hook": 18, "contrarian hook": 16, "story hook": 15,
            "data hook": 14, "urgency hook": 13, "question hook": 12,
            "visual hook": 14, "direct statement": 5,
        }
        score += hook_scores.get(hook, 5)

        emotion = content_dna.get("emotion", "neutral")
        emotion_scores = {
            "surprise": 15, "curiosity": 14, "anger": 12, "joy": 11,
            "fear": 10, "inspiration": 13, "neutral": 3,
        }
        score += emotion_scores.get(emotion, 3)

        structure = content_dna.get("structure", "single statement")
        if structure == "hook build payoff":
            score += 10
        elif structure == "hook payoff":
            score += 6

        triggers = content_dna.get("psychological_triggers", [])
        score += min(len(triggers) * 4, 16)

        score += trend_relevance * 12

        type_bonus = {"video": 5, "image": 3, "audio": 2, "text": 0}
        score += type_bonus.get(content_type, 0)

        if text:
            length = len(text)
            if 100 <= length <= 500:
                score += 5
            elif 50 <= length < 100 or 500 < length <= 1000:
                score += 2

        # Deterministic jitter from content hash
        if text:
            h = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            jitter = (h % 7) - 3
            score += jitter

        return max(0.0, min(100.0, round(score, 1)))

    # ---- Hybrid score (Section 2 / enhanced Section 8) ----

    @staticmethod
    def calculate_hybrid_score(
        ai_score: float,
        trend_relevance: float,
        content_dna: Dict[str, Any],
        media_context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Blend AI score with heuristic sub-signals.

        Enhanced 6-factor formula:
          0.40 * ai_score
        + 0.20 * (trend_relevance * 100)
        + 0.15 * (hook_strength * 100)
        + 0.10 * (emotion_intensity * 100)
        + 0.10 * (visual_engagement * 100)
        + 0.05 * (clarity * 100)

        Returns a float 0-100.
        """
        hook = content_dna.get("hook", "direct statement")
        emotion = content_dna.get("emotion", "neutral")

        hook_strength = content_dna.get("hook_strength") or HOOK_STRENGTH_MAP.get(hook, 0.30)
        emotion_intensity = content_dna.get("emotional_intensity") or EMOTION_INTENSITY_MAP.get(emotion, 0.20)
        clarity = content_dna.get("clarity_score", 0.5)

        # Visual engagement from media analysis
        visual_engagement = 0.3  # default for text-only
        if media_context:
            ve = 0.4
            if media_context.get("caption"):
                ve += 0.15
            if media_context.get("visual_theme"):
                ve += 0.1
            if media_context.get("hook_strength"):
                ve = max(ve, media_context["hook_strength"])
            if media_context.get("meme_probability", 0) > 0.5:
                ve += 0.15  # memes tend to have high visual engagement
            visual_engagement = min(1.0, ve)

        blended = (
            0.40 * ai_score
            + 0.20 * (trend_relevance * 100)
            + 0.15 * (hook_strength * 100)
            + 0.10 * (emotion_intensity * 100)
            + 0.10 * (visual_engagement * 100)
            + 0.05 * (clarity * 100)
        )
        return max(0.0, min(100.0, round(blended, 1)))

    # ---- Score breakdown for frontend bars (Section 8 enhanced) ----

    @staticmethod
    def get_score_breakdown(
        ai_score: float,
        trend_relevance: float,
        content_dna: Dict[str, Any],
        media_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """Return sub-scores (0-100 each) for dashboard breakdown bars."""
        hook = content_dna.get("hook", "direct statement")
        emotion = content_dna.get("emotion", "neutral")

        hook_strength = (content_dna.get("hook_strength") or HOOK_STRENGTH_MAP.get(hook, 0.30)) * 100
        emotion_intensity = (content_dna.get("emotional_intensity") or EMOTION_INTENSITY_MAP.get(emotion, 0.20)) * 100
        trend_score = trend_relevance * 100
        clarity = content_dna.get("clarity_score", 0.5) * 100

        visual_engagement = 30.0
        if media_context:
            ve = 40.0
            if media_context.get("caption"):
                ve += 15
            if media_context.get("visual_theme"):
                ve += 10
            if media_context.get("hook_strength"):
                ve = max(ve, media_context["hook_strength"] * 100)
            visual_engagement = min(100.0, ve)

        return {
            "ai_score": round(ai_score, 1),
            "trend_score": round(trend_score, 1),
            "hook_strength": round(hook_strength, 1),
            "emotion_intensity": round(emotion_intensity, 1),
            "visual_engagement": round(visual_engagement, 1),
            "clarity": round(clarity, 1),
        }

    # ---- Deterministic engagement predictions ----

    @staticmethod
    def predict_engagement(virality_score: float) -> Dict[str, int]:
        """
        Estimate engagement metrics from virality score.
        Deterministic — same score always yields the same prediction.
        """
        base_reach = virality_score * 50
        # Use deterministic multipliers instead of random
        return {
            "likes": int(base_reach * 0.25),
            "shares": int(base_reach * 0.065),
            "comments": int(base_reach * 0.02),
        }
