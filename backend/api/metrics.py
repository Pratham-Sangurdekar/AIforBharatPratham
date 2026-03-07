"""
Metrics API — Aggregated analytics via service abstraction.

Enhancements:
- chart-ready aggregated data: average_score, top_score, engagement_average
- score distribution histogram bucket counts
"""

from fastapi import APIRouter
from services import database_service

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    """
    Return aggregated metrics data for charts.

    On top of the raw data returned by database_service.get_metrics(),
    we compute additional roll-ups the frontend needs:
      - average_score, top_score
      - engagement_average  (avg of likes, shares, comments)
      - score_distribution  (histogram buckets 0-20, 21-40, …, 81-100)
    """
    raw = database_service.get_metrics()

    # Attempt to compute aggregated stats from recent_analyses
    recent: list = raw.get("recent_analyses", [])
    scores = [
        float(a.get("virality_score", 0))
        for a in recent
        if a.get("virality_score") is not None
    ]

    average_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    top_score = round(max(scores), 1) if scores else 0.0

    # Engagement averages
    likes_list = [
        a.get("predicted_metrics", {}).get("likes", 0) for a in recent
    ]
    shares_list = [
        a.get("predicted_metrics", {}).get("shares", 0) for a in recent
    ]
    comments_list = [
        a.get("predicted_metrics", {}).get("comments", 0) for a in recent
    ]

    def _avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else 0.0

    engagement_average = {
        "likes": _avg(likes_list),
        "shares": _avg(shares_list),
        "comments": _avg(comments_list),
    }

    # Score distribution histogram (5 buckets)
    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scores:
        if s <= 20:
            buckets["0-20"] += 1
        elif s <= 40:
            buckets["21-40"] += 1
        elif s <= 60:
            buckets["41-60"] += 1
        elif s <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1

    return {
        **raw,
        "average_score": average_score,
        "top_score": top_score,
        "engagement_average": engagement_average,
        "score_distribution": buckets,
    }
