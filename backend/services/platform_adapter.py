"""
Platform Adapter — Generates platform-specific optimizations.

TODO: Use LLM to generate true platform-adapted content for production.
"""

from typing import Dict, Any, List, Optional


PLATFORM_CONFIGS = {
    "twitter": {
        "max_length": 280,
        "style": "concise, punchy, conversational",
        "tips": [
            "Keep under 280 characters",
            "Use a strong opening line",
            "Add 1-2 relevant hashtags",
            "End with a question to boost replies",
        ],
    },
    "instagram": {
        "max_length": 2200,
        "style": "visual-first, storytelling, lifestyle",
        "tips": [
            "Lead with a scroll-stopping first line",
            "Use line breaks for readability",
            "Include 5-10 targeted hashtags",
            "End with a clear call-to-action",
        ],
    },
    "linkedin": {
        "max_length": 3000,
        "style": "professional, insightful, thought leadership",
        "tips": [
            "Open with a bold or contrarian statement",
            "Share personal experience or data",
            "Use short paragraphs with line breaks",
            "End with a discussion question",
        ],
    },
    "youtube": {
        "max_length": 5000,
        "style": "detailed, educational, entertaining",
        "tips": [
            "Hook viewers in the first 5 seconds",
            "Use pattern interrupts every 30 seconds",
            "Include clear chapter markers",
            "End with a strong call-to-action and subscribe prompt",
        ],
    },
}


class PlatformAdapter:
    """Adapts content for different social media platforms."""

    @staticmethod
    def get_platform_optimization(
        text: Optional[str],
        platform: str,
    ) -> Dict[str, Any]:
        config = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["twitter"])

        if not text:
            return {
                "platform": platform,
                "optimized_text": f"[Add {config['style']} caption for your media]",
                "tips": config["tips"],
            }

        # Simple length-based adaptation
        optimized = text
        max_len = config["max_length"]
        if len(text) > max_len:
            optimized = text[:max_len - 3] + "..."

        return {
            "platform": platform,
            "optimized_text": optimized,
            "tips": config["tips"],
        }

    @staticmethod
    def get_all_platform_optimizations(text: Optional[str]) -> List[Dict[str, Any]]:
        return [
            PlatformAdapter.get_platform_optimization(text, platform)
            for platform in PLATFORM_CONFIGS
        ]
