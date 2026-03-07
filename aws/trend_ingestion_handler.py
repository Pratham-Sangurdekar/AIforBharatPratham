"""
Real Trend Data Engine — Fetches live trending data from free public sources.

Sources:
  1. Reddit public JSON endpoints (no API key)
  2. Google Trends via pytrends (no API key)
  3. NewsAPI (free tier, optional) / GDELT (free, no key)
  4. Fallback to simulated data

Runs both as AWS Lambda handler (EventBridge) and as local background task.
"""

import os
import json
import logging
import hashlib
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Optional API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

MAX_STORED_TRENDS = int(os.getenv("MAX_STORED_TRENDS", "300"))
TRENDS_PER_CATEGORY = 10

# Categories we track
CATEGORIES = [
    "technology", "memes", "politics",
    "entertainment", "marketing", "lifestyle",
]

# Category keyword mappings for relevance detection
CATEGORY_KEYWORDS = {
    "technology": [
        "AI", "artificial intelligence", "machine learning", "GPT", "LLM",
        "automation", "robotics", "quantum", "blockchain", "Web3", "SaaS",
        "startup", "tech", "coding", "software", "app", "cloud", "data", "cyber",
    ],
    "memes": [
        "meme", "viral", "funny", "relatable", "trend", "humor", "comedy",
        "lol", "brainrot", "tiktok",
    ],
    "politics": [
        "election", "policy", "government", "democracy", "vote", "president",
        "congress", "legislation", "geopolitics", "sanctions", "law", "political",
    ],
    "entertainment": [
        "movie", "music", "celebrity", "album", "concert", "netflix",
        "streaming", "award", "box office", "trailer", "show", "film", "song",
    ],
    "marketing": [
        "brand", "campaign", "marketing", "growth", "engagement", "conversion",
        "SEO", "content strategy", "influencer", "ROI", "social media", "ads",
    ],
    "lifestyle": [
        "health", "fitness", "diet", "wellness", "travel", "fashion",
        "productivity", "routine", "minimalism", "self-care", "food",
    ],
}

# Reddit subreddits per category
REDDIT_SUBS = {
    "technology": ["technology", "MachineLearning", "startups"],
    "entertainment": ["movies", "music", "entertainment"],
    "memes": ["memes", "dankmemes"],
    "marketing": ["marketing", "socialmedia", "Entrepreneur"],
    "politics": ["worldnews", "politics"],
    "lifestyle": ["LifeProTips", "fitness", "productivity"],
}


# ===========================================================================
# UNIFIED TREND SCHEMA
# ===========================================================================

def _make_trend(keyword: str, category: str, source: str,
                popularity: float = 0.5, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """Build a normalised trend object."""
    return {
        "trend_keyword": keyword.strip(),
        "trend_category": category,
        "source": source,
        "popularity_score": round(max(0.0, min(1.0, popularity)), 3),
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }


# ===========================================================================
# SOURCE 1: REDDIT  (no API key required)
# ===========================================================================

def fetch_reddit_trends() -> List[Dict[str, Any]]:
    """Fetch from Reddit public JSON endpoints."""
    import urllib.request

    trends: List[Dict[str, Any]] = []

    for category, subs in REDDIT_SUBS.items():
        for sub in subs:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=8"
                req = urllib.request.Request(url, headers={"User-Agent": "ENGAUGE/2.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode())

                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    pd = post.get("data", {})
                    title = pd.get("title", "").strip()
                    ups = pd.get("ups", 0)
                    if not title:
                        continue
                    pop = min(1.0, ups / 50000) if ups > 0 else 0.1
                    trends.append(_make_trend(title, category, f"reddit/r/{sub}", pop))
            except Exception as e:
                logger.debug("Reddit r/%s failed: %s", sub, e)
                continue

    logger.info("Reddit: fetched %d trends", len(trends))
    return trends


# ===========================================================================
# SOURCE 2: GOOGLE TRENDS  (pytrends — no API key)
# ===========================================================================

def fetch_google_trends() -> List[Dict[str, Any]]:
    """Fetch real-time trending searches via pytrends."""
    trends: List[Dict[str, Any]] = []
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360, timeout=(5, 15))

        # Trending searches (US)
        try:
            df = pytrends.trending_searches(pn="united_states")
            for keyword in df[0].tolist()[:20]:
                cat = _categorise_keyword(keyword)
                trends.append(_make_trend(keyword, cat, "google_trends", 0.7))
        except Exception as e:
            logger.debug("Google trending_searches failed: %s", e)

        # Real-time trends
        try:
            rt = pytrends.realtime_trending_searches(pn="US")
            if rt is not None and not rt.empty:
                for _, row in rt.head(15).iterrows():
                    title = str(row.get("title", row.get("entityNames", "")))
                    if title:
                        cat = _categorise_keyword(title)
                        trends.append(_make_trend(title, cat, "google_trends_realtime", 0.8))
        except Exception:
            pass

    except ImportError:
        logger.info("pytrends not installed — skipping Google Trends")
    except Exception as e:
        logger.warning("Google Trends fetch failed: %s", e)

    logger.info("Google Trends: fetched %d trends", len(trends))
    return trends


# ===========================================================================
# SOURCE 3: NEWS HEADLINES (NewsAPI free tier or GDELT)
# ===========================================================================

def fetch_news_trends() -> List[Dict[str, Any]]:
    """Fetch from NewsAPI (if key provided) or GDELT (free, no key)."""
    trends: List[Dict[str, Any]] = []

    if NEWS_API_KEY:
        trends.extend(_fetch_newsapi())
    else:
        trends.extend(_fetch_gdelt())

    logger.info("News: fetched %d trends", len(trends))
    return trends


def _fetch_newsapi() -> List[Dict[str, Any]]:
    import urllib.request
    results: List[Dict[str, Any]] = []

    for news_cat in ["technology", "entertainment", "business", "science", "health"]:
        try:
            url = (
                f"https://newsapi.org/v2/top-headlines"
                f"?category={news_cat}&language=en&pageSize=5"
                f"&apiKey={NEWS_API_KEY}"
            )
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            for article in data.get("articles", []):
                title = article.get("title", "").strip()
                if title and title != "[Removed]":
                    cat = _map_news_category(news_cat)
                    results.append(_make_trend(title, cat, "newsapi", 0.6))
        except Exception:
            continue

    return results


def _fetch_gdelt() -> List[Dict[str, Any]]:
    """Fetch from GDELT (free, no API key needed)."""
    import urllib.request
    results: List[Dict[str, Any]] = []

    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc?query=&mode=ArtList&maxrecords=20&format=json&sort=DateDesc"
        req = urllib.request.Request(url, headers={"User-Agent": "ENGAUGE/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        for article in data.get("articles", [])[:20]:
            title = article.get("title", "").strip()
            if title:
                cat = _categorise_keyword(title)
                results.append(_make_trend(title, cat, "gdelt", 0.5))
    except Exception as e:
        logger.debug("GDELT fetch failed: %s", e)

    return results


# ===========================================================================
# HELPERS
# ===========================================================================

def _map_news_category(news_cat: str) -> str:
    mapping = {
        "technology": "technology", "entertainment": "entertainment",
        "business": "marketing", "science": "technology",
        "health": "lifestyle", "sports": "entertainment", "general": "lifestyle",
    }
    return mapping.get(news_cat, "lifestyle")


def _categorise_keyword(text: str) -> str:
    """Auto-categorise a keyword based on keyword matches."""
    tl = text.lower()
    best_cat = "lifestyle"
    best_hits = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw.lower() in tl)
        if hits > best_hits:
            best_hits = hits
            best_cat = cat
    return best_cat


def _dedup_trends(trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate trends by normalised keyword hash."""
    seen = set()
    unique = []
    for t in trends:
        h = hashlib.md5(t["trend_keyword"].strip().lower().encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(t)
    return unique


# ===========================================================================
# AGGREGATION
# ===========================================================================

def aggregate_trends(all_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate flat list into category-based structure for DB."""
    by_category: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in CATEGORIES}
    for t in all_trends:
        cat = t.get("trend_category", "lifestyle")
        if cat in by_category:
            by_category[cat].append(t)

    result = {}
    for cat in CATEGORIES:
        entries = sorted(by_category[cat], key=lambda x: x["popularity_score"], reverse=True)
        entries = entries[:TRENDS_PER_CATEGORY]
        if not entries:
            entries = [_make_trend(f"Trending in {cat}", cat, "default", 0.3)]

        topics = [{"text": e["trend_keyword"], "source": e["source"]} for e in entries]
        hot_keywords = _extract_keywords([e["trend_keyword"] for e in entries], cat)
        avg_pop = sum(e["popularity_score"] for e in entries) / len(entries)

        result[cat] = {
            "topics": topics,
            "hot_keywords": hot_keywords[:5],
            "trend_strength": round(avg_pop, 2),
        }
    return result


def _extract_keywords(topics: List[str], category: str) -> List[str]:
    cat_keywords = CATEGORY_KEYWORDS.get(category, [])
    found = set()
    for topic in topics:
        tl = topic.lower()
        for kw in cat_keywords:
            if kw.lower() in tl:
                found.add(kw)
    if len(found) < 3:
        remaining = [k for k in cat_keywords if k not in found]
        found.update(random.sample(remaining, min(3, len(remaining))))
    return list(found)


# ===========================================================================
# SIMULATED FALLBACK
# ===========================================================================

def get_simulated_trends() -> List[Dict[str, Any]]:
    raw = {
        "technology": [
            "AI tools are transforming content creation",
            "New LLM benchmarks shake up the industry",
            "Cloud computing costs drop significantly",
            "Wearable tech reaches mainstream adoption",
            "Cybersecurity threats evolve with AI",
        ],
        "memes": [
            "New meme format takes over Twitter",
            "Relatable work-from-home memes trend",
            "Gen Z humor goes mainstream",
            "AI-generated memes spark debate",
            "Nostalgia memes make a comeback",
        ],
        "politics": [
            "Global tech regulation debates intensify",
            "AI governance frameworks proposed",
            "Climate policy enters new phase",
            "Election season content strategies",
            "Digital privacy laws expand",
        ],
        "entertainment": [
            "Streaming platform wars heat up",
            "Independent creators rival studios",
            "Short-form video dominates attention",
            "Music industry embraces AI tools",
            "Podcast growth continues to surge",
        ],
        "marketing": [
            "Creator economy hits new milestone",
            "AI-powered marketing tools surge",
            "Community-led growth strategies work",
            "Brand authenticity beats perfection",
            "Short-form video ROI proven",
        ],
        "lifestyle": [
            "Digital wellness movement grows",
            "Productivity hack videos go viral",
            "Slow living trend gains momentum",
            "Fitness challenges drive engagement",
            "Minimalist lifestyle content thrives",
        ],
    }
    trends = []
    for cat, items in raw.items():
        for item in items:
            trends.append(_make_trend(item, cat, "simulated", round(random.uniform(0.3, 0.8), 2)))
    return trends


# ===========================================================================
# MAIN INGESTION FUNCTION (used by both Lambda and local)
# ===========================================================================

def ingest_trends() -> Dict[str, Any]:
    """Fetch from all sources, deduplicate, aggregate, and store."""
    all_trends: List[Dict[str, Any]] = []

    # Source 1: Reddit
    try:
        all_trends.extend(fetch_reddit_trends())
    except Exception as e:
        logger.warning("Reddit ingestion failed: %s", e)

    # Source 2: Google Trends
    try:
        all_trends.extend(fetch_google_trends())
    except Exception as e:
        logger.warning("Google Trends ingestion failed: %s", e)

    # Source 3: News
    try:
        all_trends.extend(fetch_news_trends())
    except Exception as e:
        logger.warning("News ingestion failed: %s", e)

    # Fallback
    if not all_trends:
        logger.info("No real trends fetched, using simulated data")
        all_trends = get_simulated_trends()

    # Dedup & cap
    all_trends = _dedup_trends(all_trends)
    if len(all_trends) > MAX_STORED_TRENDS:
        all_trends = sorted(all_trends, key=lambda x: x["popularity_score"], reverse=True)[:MAX_STORED_TRENDS]

    # Aggregate
    formatted = aggregate_trends(all_trends)

    # Store
    try:
        from services import database_service
        database_service.save_trends(formatted)
        logger.info("Trends saved (%d items across %d categories)", len(all_trends), len(formatted))
    except Exception as e:
        logger.error("Failed to save trends: %s", e)

    return formatted


# ===========================================================================
# AWS LAMBDA HANDLER
# ===========================================================================

def handler(event, context):
    """Lambda entry point (EventBridge schedule)."""
    os.environ.setdefault("ENGAUGE_ENV", "aws")
    logger.info("Trend ingestion started at %s", datetime.now(timezone.utc).isoformat())

    formatted = ingest_trends()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Trend ingestion complete",
            "categories": list(formatted.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }),
    }
