"""
Optimization Engine — Generate improvement suggestions and optimized variants.

Enhanced with:
- Trend-aware suggestions (references actual trending topics)
- Media-aware suggestions (references image/video/audio analysis)
- Actionable, specific improvement recommendations
- Platform-specific variant generation
"""

from typing import Dict, Any, List, Optional


class OptimizationEngine:
    """Generates content improvement suggestions and optimized variants."""

    @staticmethod
    def generate_suggestions(
        text: Optional[str],
        content_dna: Dict[str, Any],
        trend_alignment: Dict[str, Any],
        virality_score: float,
        media_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        suggestions: List[str] = []

        hook = content_dna.get("hook", "direct statement")
        emotion = content_dna.get("emotion", "neutral")
        structure = content_dna.get("structure", "single statement")
        triggers = content_dna.get("psychological_triggers", [])
        relevance = trend_alignment.get("relevance_score", 0)
        matched = trend_alignment.get("matched_topics", [])
        hook_strength = content_dna.get("hook_strength", 0)
        clarity = content_dna.get("clarity_score", 0)

        # --- Hook suggestions ---
        if hook in ("direct statement", "direct_statement") or hook_strength < 0.4:
            suggestions.append(
                "Rewrite the opening with a curiosity gap — e.g. "
                "'Nobody talks about this…' or 'The secret behind…' to stop the scroll."
            )
        elif hook == "question hook":
            suggestions.append(
                "Follow the question with a surprising answer in the next line to create tension."
            )
        elif hook in ("story", "story_hook"):
            suggestions.append(
                "Add a specific data point or number to ground the story and boost credibility."
            )

        # --- Emotion suggestions ---
        if emotion == "neutral":
            suggestions.append(
                "Inject stronger emotion — surprise and curiosity drive 2-3× more shares than neutral tone."
            )
        elif emotion in ("anger", "fear"):
            suggestions.append(
                "Balance the negative emotion with a constructive takeaway or hopeful resolution to avoid audience fatigue."
            )

        # --- Structure suggestions ---
        if structure in ("single statement", "single_statement"):
            suggestions.append(
                "Expand into a hook → build → payoff structure (3+ sentences). "
                "This pattern increases average watch time by 40%."
            )
        elif structure in ("hook payoff", "hook_payoff"):
            suggestions.append(
                "Add a middle section that builds anticipation — tell a micro-story or present counter-arguments."
            )

        # --- Trigger suggestions ---
        trigger_set = set(triggers)
        if len(trigger_set) < 2:
            missing = {"social_proof", "scarcity", "curiosity_gap", "fomo"} - trigger_set
            if missing:
                suggestions.append(
                    f"Add a psychological trigger: try {', '.join(list(missing)[:2])} "
                    "to boost engagement."
                )

        # --- Trend suggestions (with real data) ---
        if relevance < 0.4:
            if matched:
                suggestions.append(
                    f"Directly reference trending topics ({', '.join(matched[:3])}) "
                    "in your content to ride the wave."
                )
            else:
                suggestions.append(
                    "Reference a current trending topic to boost discoverability — "
                    "check the Trends tab for what's hot right now."
                )
        elif relevance >= 0.7:
            suggestions.append(
                f"Great trend alignment with {', '.join(matched[:2])}! "
                "Add your unique angle to stand out from the crowd."
            )

        # --- Clarity suggestions ---
        if clarity < 0.4:
            suggestions.append(
                "Simplify the message — use shorter sentences and one clear idea per paragraph. "
                "High clarity correlates with 60% better engagement."
            )

        # --- Media-specific suggestions ---
        if media_context:
            if media_context.get("emotional_tone") == "neutral":
                suggestions.append(
                    "The visual/audio tone is flat — add dramatic music, bold text overlays, "
                    "or emotion-evoking imagery."
                )
            if media_context.get("pacing_score", 1) < 0.4:
                suggestions.append(
                    "The pacing is slow — add cuts every 2-3 seconds and vary visual angles to keep attention."
                )
            if media_context.get("hook_strength", 1) < 0.4:
                suggestions.append(
                    "The opening frame is weak — start with a face close-up, bold text, or unexpected visual."
                )
            if media_context.get("transcript") and len(media_context["transcript"]) < 20:
                suggestions.append(
                    "Very little spoken content detected — add narration or text overlays to convey your message."
                )
            if media_context.get("meme_probability", 0) > 0.6:
                suggestions.append(
                    "Meme format detected — add a relatable caption and consider posting during peak hours (12-1pm, 7-9pm)."
                )

        # --- Score-based ---
        if virality_score < 50:
            suggestions.append(
                "Add a clear call-to-action: ask a question, request saves, or prompt comments."
            )
        if virality_score < 30:
            suggestions.append(
                "Consider a complete restructure — lead with your strongest hook and a clear value proposition."
            )

        # --- Text-specific ---
        if text:
            if len(text) > 1000:
                suggestions.append(
                    "Shorten to under 500 characters — concise posts get 2× more engagement on most platforms."
                )
            elif len(text) < 50:
                suggestions.append(
                    "Add more context or detail to give the audience enough to engage with."
                )

        return suggestions[:8]  # Cap at 8 suggestions

    @staticmethod
    def generate_optimized_variants(
        text: Optional[str],
        content_dna: Dict[str, Any],
        suggestions: List[str],
    ) -> List[str]:
        """
        Generate 3 optimized variants using heuristic templates.
        Overridden by LLM when available.
        """
        if not text:
            return [
                "Add a bold caption that opens with a hook and references a trending topic.",
                "Pair this media with a short, punchy text overlay that creates curiosity.",
                "Create a carousel or thread format to boost dwell time and shares.",
            ]

        hook = content_dna.get("hook", "direct statement")
        emotion = content_dna.get("emotion", "neutral")
        first_sentence = text.split(".")[0].strip() if "." in text else text.strip()

        variants = [
            f"Nobody talks about this — {first_sentence.lower()}. Here is what you need to know.",
            f"You will not believe what I discovered: {first_sentence.lower()}. This changes everything.",
            f"Stop scrolling. {first_sentence}. And here is the part that will surprise you.",
        ]
        return variants
