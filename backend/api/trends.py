"""
Trends API — Exposes real-time trending topics.

Pulls from the TrendEngine's live cache (Reddit, Google Trends, GDELT)
with fallback to database_service.
"""

from fastapi import APIRouter
from services import database_service

router = APIRouter()


@router.get("/trends")
def get_trends():
    """Get all trending topics grouped by category (real-time)."""
    try:
        from services.trend_engine import TrendEngine
        live = TrendEngine.get_trending_topics()
        if live and any(
            isinstance(v, dict) and v.get("topics") for v in live.values()
        ):
            return live
    except Exception:
        pass
    return database_service.get_trends()


@router.get("/trends/platforms")
def get_platform_trends():
    """Get platform-specific trending topics."""
    return database_service.get_platform_trends()


@router.get("/trends/live")
def get_live_trends():
    """
    Lightweight endpoint for frontend polling.
    Returns categories with topics, popularity scores, and source tags.
    """
    try:
        from services.trend_engine import TrendEngine
        raw = TrendEngine.get_trending_topics()
        # Enrich with metadata
        enriched = {}
        for category, data in raw.items():
            if isinstance(data, dict):
                enriched[category] = {
                    "topics": data.get("topics", []),
                    "hot_keywords": data.get("hot_keywords", []),
                    "trend_strength": data.get("trend_strength", 0.5),
                    "source": data.get("source", "aggregated"),
                }
            else:
                enriched[category] = data
        return enriched
    except Exception:
        return database_service.get_trends()
