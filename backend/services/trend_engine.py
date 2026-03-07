"""
Trend Engine — Provides trending topics for the ENGAUGE analysis pipeline.

In local mode:
  - Runs a background thread that fetches real trends every N minutes
    from Reddit, Google Trends, and News (via trend_ingestion_handler).
  - Caches results in-memory so API responses are instant.
  - Falls back to simulated data if all sources fail.

In AWS mode:
  - Trends are fetched by Lambda (EventBridge) and stored in DynamoDB.
  - This module still provides analyze_trend_alignment() for heuristic scoring.
"""

import logging
import threading
import time
import os
import random
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# In-memory trend cache (refreshed by background thread)
_cached_trends: Dict[str, Any] = {}
_cached_platform_trends: Dict[str, List[Dict[str, Any]]] = {}
_lock = threading.Lock()
_bg_thread_started = False

REFRESH_INTERVAL = int(os.getenv("TREND_REFRESH_INTERVAL", "600"))  # 10 min default

# Simulated trending topics (used as fallback)
TRENDING_TOPICS = {
    "technology": {
        "keywords": [
            "AI", "artificial intelligence", "machine learning", "GPT", "LLM",
            "automation", "robotics", "quantum computing", "blockchain", "Web3",
            "SaaS", "startup",
        ],
        "topics": [
            "AI tools revolution", "OpenAI updates", "Apple product launch",
            "Coding with AI", "Tech layoffs recovery",
        ],
    },
    "memes": {
        "keywords": [
            "meme", "viral", "funny", "relatable", "trend", "slay", "no cap",
            "based", "sus", "brainrot", "skibidi",
        ],
        "topics": [
            "New meme format trending", "Relatable work memes",
            "Gen Z humor wave", "AI-generated memes", "Corporate cringe",
        ],
    },
    "politics": {
        "keywords": [
            "election", "policy", "government", "democracy", "vote",
            "president", "congress", "legislation", "geopolitics", "sanctions",
        ],
        "topics": [
            "2026 midterms", "Climate policy debate", "Tech regulation",
            "Global trade tensions", "AI governance",
        ],
    },
    "entertainment": {
        "keywords": [
            "movie", "music", "celebrity", "album", "concert", "netflix",
            "streaming", "award", "box office", "trailer",
        ],
        "topics": [
            "New album drop", "Award show highlights",
            "Streaming wars update", "Celebrity controversy",
            "Viral TikTok sound",
        ],
    },
    "marketing": {
        "keywords": [
            "brand", "campaign", "marketing", "growth", "engagement",
            "conversion", "SEO", "content strategy", "influencer", "ROI",
        ],
        "topics": [
            "Creator economy growth", "Short-form video dominance",
            "AI-powered marketing tools", "Brand authenticity trend",
            "Community-led growth",
        ],
    },
    "lifestyle": {
        "keywords": [
            "health", "fitness", "diet", "wellness", "travel", "fashion",
            "productivity", "morning routine", "minimalism",
        ],
        "topics": [
            "Productivity hacks trending", "Fitness challenge viral",
            "Digital detox movement", "Slow living trend",
            "Wellness tech boom",
        ],
    },
}


# ---------------------------------------------------------------------------
# Background refresh thread
# ---------------------------------------------------------------------------

def _refresh_loop():
    """Periodically fetch real trends in the background."""
    global _cached_trends, _cached_platform_trends
    while True:
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "aws"))
            from trend_ingestion_handler import ingest_trends
            result = ingest_trends()
            with _lock:
                _cached_trends = result
            logger.info("Background trend refresh complete: %d categories", len(result))
        except Exception as e:
            logger.warning("Background trend refresh failed: %s", e)
        time.sleep(REFRESH_INTERVAL)


def start_background_refresh():
    """Start the background trend refresh thread (once)."""
    global _bg_thread_started
    if _bg_thread_started:
        return
    _bg_thread_started = True
    t = threading.Thread(target=_refresh_loop, daemon=True)
    t.start()
    logger.info("Trend refresh background thread started (interval=%ds)", REFRESH_INTERVAL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class TrendEngine:
    """Analyses content for alignment with current trending topics."""

    @staticmethod
    def get_trending_topics() -> Dict[str, Any]:
        """
        Return trending data — real if available, simulated otherwise.
        Also starts the background refresh thread on first call.
        """
        start_background_refresh()

        with _lock:
            if _cached_trends:
                return _cached_trends

        # Return simulated data as initial fallback
        result = {}
        for category, data in TRENDING_TOPICS.items():
            result[category] = {
                "topics": data["topics"],
                "hot_keywords": random.sample(
                    data["keywords"], min(5, len(data["keywords"]))
                ),
                "trend_strength": round(random.uniform(0.5, 1.0), 2),
            }
        return result

    @staticmethod
    def get_trending_by_platform() -> Dict[str, List[Dict[str, Any]]]:
        """Return platform-specific trends."""
        return {
            "twitter": [
                {"topic": "AI tools taking over", "volume": "125K tweets", "category": "technology"},
                {"topic": "Election debate reactions", "volume": "89K tweets", "category": "politics"},
                {"topic": "New meme format", "volume": "67K tweets", "category": "memes"},
                {"topic": "Productivity morning routines", "volume": "45K tweets", "category": "lifestyle"},
                {"topic": "Creator economy tips", "volume": "34K tweets", "category": "marketing"},
            ],
            "instagram": [
                {"topic": "Aesthetic reels trending", "volume": "2.1M posts", "category": "entertainment"},
                {"topic": "AI art showcase", "volume": "890K posts", "category": "technology"},
                {"topic": "Fitness transformations", "volume": "1.5M posts", "category": "lifestyle"},
                {"topic": "Brand collaboration trends", "volume": "450K posts", "category": "marketing"},
                {"topic": "Relatable content creators", "volume": "780K posts", "category": "memes"},
            ],
            "youtube": [
                {"topic": "AI tutorial videos", "volume": "High", "category": "technology"},
                {"topic": "Documentary style content", "volume": "High", "category": "entertainment"},
                {"topic": "Short-form vs long-form debate", "volume": "Medium", "category": "marketing"},
                {"topic": "Political commentary", "volume": "Medium", "category": "politics"},
                {"topic": "Challenge videos", "volume": "High", "category": "memes"},
            ],
            "linkedin": [
                {"topic": "AI in the workplace", "volume": "Trending", "category": "technology"},
                {"topic": "Leadership insights", "volume": "Trending", "category": "marketing"},
                {"topic": "Career transition stories", "volume": "Popular", "category": "lifestyle"},
                {"topic": "Startup funding news", "volume": "Rising", "category": "technology"},
                {"topic": "Remote work culture", "volume": "Steady", "category": "lifestyle"},
            ],
        }

    @staticmethod
    def analyze_trend_alignment(
        text: Optional[str], content_type: str
    ) -> Dict[str, Any]:
        """Check how well content aligns with current trends."""
        if not text:
            return {"matched_topics": [], "relevance_score": 0.1}

        text_lower = text.lower()
        matched_topics: List[str] = []
        total_keyword_hits = 0

        # Use real trends if available
        trends = TrendEngine.get_trending_topics()

        for category, data in trends.items():
            if isinstance(data, dict):
                # Check keywords from hot_keywords
                keywords = data.get("hot_keywords", [])
                topics = data.get("topics", [])
                hits = sum(1 for kw in keywords if isinstance(kw, str) and kw.lower() in text_lower)

                # Also check topic text
                for t in topics:
                    topic_text = t if isinstance(t, str) else t.get("text", "") if isinstance(t, dict) else str(t)
                    topic_words = topic_text.lower().split()
                    if any(w in text_lower for w in topic_words if len(w) > 3):
                        hits += 1

                if hits > 0:
                    total_keyword_hits += hits
                    # Pick top topic from category
                    if topics:
                        first = topics[0]
                        label = first if isinstance(first, str) else first.get("text", str(first))
                        matched_topics.append(label)

        # Also check against static keyword bank for broader coverage
        for category, data in TRENDING_TOPICS.items():
            hits = sum(1 for kw in data["keywords"] if kw.lower() in text_lower)
            if hits > 0:
                total_keyword_hits += hits
                if data["topics"][0] not in matched_topics:
                    matched_topics.append(data["topics"][0])

        relevance_score = min(1.0, total_keyword_hits * 0.08)

        return {
            "matched_topics": matched_topics[:5],
            "relevance_score": round(relevance_score, 2),
        }
