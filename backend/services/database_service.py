"""
Database Service — Abstraction layer for data persistence.
Supports: Amazon DynamoDB | Local SQLite (via SQLAlchemy).

The service is portable: swap the backend by changing ENGAUGE_ENV.
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from decimal import Decimal

from config import (
    is_aws, AWS_REGION,
    DYNAMODB_ANALYSIS_TABLE, DYNAMODB_CONTENT_TABLE,
    DYNAMODB_TRENDS_TABLE, DYNAMODB_USERS_TABLE,
)

logger = logging.getLogger(__name__)

# Lazy-loaded DynamoDB resource
_dynamodb = None


def _get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        import boto3
        _dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return _dynamodb


# ══════════════════════════════════════════════
# CONTENT operations
# ══════════════════════════════════════════════

def save_content(content_type: str, text_content: Optional[str], media_path: Optional[str]) -> Dict[str, Any]:
    """Save a content record. Returns the record with generated id."""
    if is_aws():
        return _dynamo_save_content(content_type, text_content, media_path)
    return _sqlite_save_content(content_type, text_content, media_path)


def get_content(content_id: Any) -> Optional[Dict[str, Any]]:
    """Retrieve a content record by ID."""
    if is_aws():
        return _dynamo_get_content(str(content_id))
    return _sqlite_get_content(int(content_id))


# ══════════════════════════════════════════════
# ANALYSIS operations
# ══════════════════════════════════════════════

def save_analysis(content_id: Any, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store analysis results. Returns the record with generated id."""
    if is_aws():
        return _dynamo_save_analysis(str(content_id), analysis_data)
    return _sqlite_save_analysis(int(content_id), analysis_data)


def get_analysis(analysis_id: Any) -> Optional[Dict[str, Any]]:
    """Retrieve a single analysis by ID."""
    if is_aws():
        return _dynamo_get_analysis(str(analysis_id))
    return _sqlite_get_analysis(int(analysis_id))


def get_analysis_detail(analysis_id: Any) -> Optional[Dict[str, Any]]:
    """Retrieve full analysis + content detail by analysis ID."""
    if is_aws():
        return _dynamo_get_analysis_detail(str(analysis_id))
    return _sqlite_get_analysis_detail(int(analysis_id))


def get_history(limit: int = 20, offset: int = 0, content_type: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve analysis history list."""
    if is_aws():
        return _dynamo_get_history(limit, offset, content_type)
    return _sqlite_get_history(limit, offset, content_type)


def get_gallery(content_type: Optional[str] = None, limit: int = 30, offset: int = 0) -> Dict[str, Any]:
    """Retrieve gallery items (content + analysis summaries)."""
    if is_aws():
        return _dynamo_get_gallery(content_type, limit, offset)
    return _sqlite_get_gallery(content_type, limit, offset)


def get_metrics() -> Dict[str, Any]:
    """Retrieve aggregated metrics data."""
    if is_aws():
        return _dynamo_get_metrics()
    return _sqlite_get_metrics()


# ══════════════════════════════════════════════
# USER / PROFILE operations
# ══════════════════════════════════════════════

DEFAULT_PROFILE = {
    "name": "Creator",
    "niche": "General",
    "primary_platforms": ["Instagram", "Twitter", "YouTube"],
    "audience_demographic": "18-35, Global",
    "content_categories": ["Technology", "Entertainment", "Marketing"],
    "bio": "Content creator exploring the digital landscape.",
}


def get_profile() -> Dict[str, Any]:
    """Get the creator profile (single-user system)."""
    if is_aws():
        return _dynamo_get_profile()
    return _sqlite_get_profile()


def update_profile(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update the creator profile."""
    if is_aws():
        return _dynamo_update_profile(update_data)
    return _sqlite_update_profile(update_data)


# ══════════════════════════════════════════════
# TRENDS operations
# ══════════════════════════════════════════════

def save_trends(trends_data: Dict[str, Any]) -> None:
    """Save trending topics data."""
    if is_aws():
        _dynamo_save_trends(trends_data)
    else:
        # Local mode: store in TrendEngine's in-memory cache
        from services.trend_engine import _lock, _cached_trends
        import services.trend_engine as _te
        with _te._lock:
            _te._cached_trends = trends_data


def get_trends() -> Dict[str, Any]:
    """Get trending topics."""
    if is_aws():
        return _dynamo_get_trends()
    from services.trend_engine import TrendEngine
    return TrendEngine.get_trending_topics()


def get_platform_trends() -> Dict[str, Any]:
    """Get platform-specific trends."""
    if is_aws():
        return _dynamo_get_platform_trends()
    from services.trend_engine import TrendEngine
    return TrendEngine.get_trending_by_platform()


# ══════════════════════════════════════════════
# CACHE operations (Section 5 — avoid repeated LLM calls)
# ══════════════════════════════════════════════

# In-memory cache for local mode (survives across requests within same process)
_analysis_cache: Dict[str, Any] = {}


def get_cached_analysis(content_hash: str) -> Optional[Dict[str, Any]]:
    """Look up a previously cached analysis result by content hash."""
    if is_aws():
        return _dynamo_get_cached_analysis(content_hash)
    return _analysis_cache.get(content_hash)


def cache_analysis(content_hash: str, result: Dict[str, Any]) -> None:
    """Store an analysis result in cache keyed by content hash."""
    if is_aws():
        _dynamo_cache_analysis(content_hash, result)
    else:
        _analysis_cache[content_hash] = result


def _dynamo_get_cached_analysis(content_hash: str) -> Optional[Dict[str, Any]]:
    """Check DynamoDB analysis table for a cached hash."""
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    try:
        from boto3.dynamodb.conditions import Attr
        resp = table.scan(
            FilterExpression=Attr("content_hash").eq(content_hash),
            Limit=1,
        )
        items = resp.get("Items", [])
        if items:
            item = _decimal_to_native(items[0])
            # Reconstruct the response payload from the stored analysis
            return {
                "id": item.get("id"),
                "content_id": item.get("content_id"),
                "virality_score": item.get("virality_score", 0),
                "explanation": item.get("explanation", ""),
                "predicted_metrics": item.get("predicted_metrics", {}),
                "content_dna": item.get("content_dna", {}),
                "trend_alignment": item.get("trend_alignment", {}),
                "suggestions": item.get("suggestions", []),
                "optimized_variants": item.get("optimized_variants", []),
                "platform_optimizations": item.get("platform_optimizations", []),
                "score_breakdown": item.get("score_breakdown", {}),
                "content_type": item.get("content_type_cached", "text"),
                "media_url": item.get("media_url_cached"),
                "created_at": item.get("created_at", ""),
                "cached": True,
            }
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
    return None


def _dynamo_cache_analysis(content_hash: str, result: Dict[str, Any]) -> None:
    """Store cache hash in the analysis record for future lookups."""
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    try:
        analysis_id = result.get("id")
        if analysis_id:
            table.update_item(
                Key={"id": str(analysis_id)},
                UpdateExpression="SET content_hash = :h, content_type_cached = :ct, media_url_cached = :mu, score_breakdown = :sb",
                ExpressionAttributeValues=_native_to_decimal({
                    ":h": content_hash,
                    ":ct": result.get("content_type", "text"),
                    ":mu": result.get("media_url"),
                    ":sb": result.get("score_breakdown", {}),
                }),
            )
    except Exception as e:
        logger.warning(f"Cache store failed: {e}")


# ══════════════════════════════════════════════
# DynamoDB Implementation
# ══════════════════════════════════════════════

def _decimal_to_native(obj):
    """Recursively convert Decimal to int/float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_native(i) for i in obj]
    return obj


def _native_to_decimal(obj):
    """Recursively convert float to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _native_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_native_to_decimal(i) for i in obj]
    return obj


def _dynamo_save_content(content_type: str, text_content: Optional[str], media_path: Optional[str]) -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_CONTENT_TABLE)
    content_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": content_id,
        "content_type": content_type,
        "created_at": now,
    }
    if text_content:
        item["text_content"] = text_content
    if media_path:
        item["media_path"] = media_path

    table.put_item(Item=item)
    return {"id": content_id, "content_type": content_type, "text_content": text_content,
            "media_path": media_path, "created_at": now}


def _dynamo_get_content(content_id: str) -> Optional[Dict[str, Any]]:
    table = _get_dynamodb().Table(DYNAMODB_CONTENT_TABLE)
    resp = table.get_item(Key={"id": content_id})
    item = resp.get("Item")
    return _decimal_to_native(item) if item else None


def _dynamo_save_analysis(content_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    analysis_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = _native_to_decimal({
        "id": analysis_id,
        "content_id": content_id,
        "virality_score": data.get("virality_score", 0),
        "explanation": data.get("explanation", ""),
        "predicted_metrics": data.get("predicted_metrics", {}),
        "content_dna": data.get("content_dna", {}),
        "trend_alignment": data.get("trend_alignment", {}),
        "suggestions": data.get("suggestions", []),
        "optimized_variants": data.get("optimized_variants", []),
        "platform_optimizations": data.get("platform_optimizations", []),
        "created_at": now,
    })

    table.put_item(Item=item)

    result = _decimal_to_native(item)
    result["id"] = analysis_id
    return result


def _dynamo_get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    resp = table.get_item(Key={"id": analysis_id})
    item = resp.get("Item")
    return _decimal_to_native(item) if item else None


def _dynamo_get_analysis_detail(analysis_id: str) -> Optional[Dict[str, Any]]:
    analysis = _dynamo_get_analysis(analysis_id)
    if not analysis:
        return None
    content = _dynamo_get_content(analysis["content_id"])
    if not content:
        return None
    return {
        "id": analysis["id"],
        "content_id": content["id"],
        "content_type": content.get("content_type", "text"),
        "text_content": content.get("text_content"),
        "media_url": content.get("media_path"),
        "virality_score": analysis.get("virality_score", 0),
        "explanation": analysis.get("explanation", ""),
        "predicted_metrics": analysis.get("predicted_metrics", {}),
        "content_dna": analysis.get("content_dna", {}),
        "trend_alignment": analysis.get("trend_alignment", {}),
        "suggestions": analysis.get("suggestions", []),
        "optimized_variants": analysis.get("optimized_variants", []),
        "platform_optimizations": analysis.get("platform_optimizations"),
        "created_at": analysis.get("created_at", ""),
    }


def _dynamo_get_history(limit: int, offset: int, content_type: Optional[str]) -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    # Scan all analyses (for hackathon scale this is fine; production would use GSI)
    scan_params = {}
    if content_type:
        from boto3.dynamodb.conditions import Attr
        scan_params["FilterExpression"] = Attr("content_type_cached").eq(content_type)

    resp = table.scan(**scan_params)
    all_items = _decimal_to_native(resp.get("Items", []))

    # Sort by created_at descending
    all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    total = len(all_items)
    paged = all_items[offset:offset + limit]

    items = []
    for a in paged:
        content = _dynamo_get_content(a["content_id"]) or {}
        if content_type and content.get("content_type") != content_type:
            continue
        text = content.get("text_content", "")
        items.append({
            "id": a["id"],
            "content_id": a["content_id"],
            "content_type": content.get("content_type", "text"),
            "text_preview": (text[:120] + "...") if text and len(text) > 120 else text,
            "media_url": content.get("media_path"),
            "virality_score": a.get("virality_score", 0),
            "created_at": a.get("created_at", ""),
        })

    return {"items": items, "total": total}


def _dynamo_get_gallery(content_type: Optional[str], limit: int, offset: int) -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_CONTENT_TABLE)
    resp = table.scan()
    all_contents = _decimal_to_native(resp.get("Items", []))
    all_contents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    if content_type:
        all_contents = [c for c in all_contents if c.get("content_type") == content_type]

    total = len(all_contents)
    paged = all_contents[offset:offset + limit]

    # Fetch analyses for these contents
    analysis_table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    items = []
    for c in paged:
        # Find analysis for this content
        from boto3.dynamodb.conditions import Attr
        resp = analysis_table.scan(FilterExpression=Attr("content_id").eq(c["id"]), Limit=1)
        analysis_items = resp.get("Items", [])
        a = _decimal_to_native(analysis_items[0]) if analysis_items else None

        text = c.get("text_content", "")
        items.append({
            "id": c["id"],
            "content_type": c.get("content_type", "text"),
            "text_preview": (text[:100] + "...") if text and len(text) > 100 else text,
            "media_url": c.get("media_path"),
            "virality_score": a.get("virality_score") if a else None,
            "analysis_id": a.get("id") if a else None,
            "created_at": c.get("created_at", ""),
        })

    return {"items": items, "total": total}


def _dynamo_get_metrics() -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    resp = table.scan()
    analyses = _decimal_to_native(resp.get("Items", []))
    analyses.sort(key=lambda x: x.get("created_at", ""))

    total_analyses = len(analyses)
    scores = [a.get("virality_score", 0) for a in analyses]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    score_over_time = [
        {"date": a.get("created_at", ""), "score": a.get("virality_score", 0)}
        for a in analyses
    ]

    engagement_data = []
    for a in analyses:
        pm = a.get("predicted_metrics", {})
        if isinstance(pm, dict):
            engagement_data.append({
                "date": a.get("created_at", ""),
                "likes": pm.get("likes", 0),
                "shares": pm.get("shares", 0),
                "comments": pm.get("comments", 0),
            })

    # Content type distribution (need to check content table)
    content_table = _get_dynamodb().Table(DYNAMODB_CONTENT_TABLE)
    content_resp = content_table.scan()
    contents = content_resp.get("Items", [])
    from collections import defaultdict
    type_counts = defaultdict(int)
    for c in contents:
        type_counts[c.get("content_type", "text")] += 1
    content_distribution = [{"type": t, "count": c} for t, c in type_counts.items()]

    # Score brackets
    brackets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in scores:
        if s <= 20:
            brackets["0-20"] += 1
        elif s <= 40:
            brackets["21-40"] += 1
        elif s <= 60:
            brackets["41-60"] += 1
        elif s <= 80:
            brackets["61-80"] += 1
        else:
            brackets["81-100"] += 1

    return {
        "total_analyses": total_analyses,
        "avg_virality_score": avg_score,
        "score_over_time": score_over_time,
        "engagement_data": engagement_data,
        "content_distribution": content_distribution,
        "score_distribution": [{"range": k, "count": v} for k, v in brackets.items()],
    }


def _dynamo_get_profile() -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_USERS_TABLE)
    resp = table.get_item(Key={"id": "default_user"})
    item = resp.get("Item")
    if not item:
        # Create default profile
        item = {
            "id": "default_user",
            **DEFAULT_PROFILE,
            "avatar_url": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        table.put_item(Item=item)

    profile = _decimal_to_native(item)

    # Get avg score
    analysis_table = _get_dynamodb().Table(DYNAMODB_ANALYSIS_TABLE)
    analysis_resp = analysis_table.scan(ProjectionExpression="virality_score")
    scores = [_decimal_to_native(a.get("virality_score", 0)) for a in analysis_resp.get("Items", [])]
    avg = round(sum(scores) / len(scores), 1) if scores else 0

    profile["avg_virality_score"] = avg
    return profile


def _dynamo_update_profile(update_data: Dict[str, Any]) -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_USERS_TABLE)
    # Get current profile first
    profile = _dynamo_get_profile()
    for key, value in update_data.items():
        profile[key] = value
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=_native_to_decimal(profile))
    return {"status": "updated", "profile": _decimal_to_native(profile)}


def _dynamo_save_trends(trends_data: Dict[str, Any]) -> None:
    table = _get_dynamodb().Table(DYNAMODB_TRENDS_TABLE)
    now = datetime.now(timezone.utc).isoformat()
    for category, data in trends_data.items():
        item = _native_to_decimal({
            "category": category,
            "data": data,
            "updated_at": now,
        })
        table.put_item(Item=item)


def _dynamo_get_trends() -> Dict[str, Any]:
    table = _get_dynamodb().Table(DYNAMODB_TRENDS_TABLE)
    resp = table.scan()
    items = resp.get("Items", [])
    if not items:
        # Fallback to static trends
        from services.trend_engine import TrendEngine
        return TrendEngine.get_trending_topics()
    result = {}
    for item in items:
        item = _decimal_to_native(item)
        result[item["category"]] = item.get("data", {})
    return result


def _dynamo_get_platform_trends() -> Dict[str, Any]:
    # For now, platform trends are derived from the same trend engine
    # A more sophisticated version would store per-platform data
    from services.trend_engine import TrendEngine
    return TrendEngine.get_trending_by_platform()


# ══════════════════════════════════════════════
# SQLite Implementation (via existing SQLAlchemy models)
# ══════════════════════════════════════════════

def _get_db_session():
    """Get a SQLAlchemy session for local mode."""
    from database import SessionLocal
    return SessionLocal()


def _sqlite_save_content(content_type: str, text_content: Optional[str], media_path: Optional[str]) -> Dict[str, Any]:
    from models.content_model import Content
    db = _get_db_session()
    try:
        record = Content(content_type=content_type, text_content=text_content, media_path=media_path)
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "id": record.id,
            "content_type": record.content_type,
            "text_content": record.text_content,
            "media_path": record.media_path,
            "created_at": str(record.created_at),
        }
    finally:
        db.close()


def _sqlite_get_content(content_id: int) -> Optional[Dict[str, Any]]:
    from models.content_model import Content
    db = _get_db_session()
    try:
        record = db.query(Content).filter(Content.id == content_id).first()
        if not record:
            return None
        return {
            "id": record.id,
            "content_type": record.content_type,
            "text_content": record.text_content,
            "media_path": record.media_path,
            "created_at": str(record.created_at),
        }
    finally:
        db.close()


def _sqlite_save_analysis(content_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    from models.content_model import Analysis
    db = _get_db_session()
    try:
        record = Analysis(
            content_id=content_id,
            virality_score=data.get("virality_score", 0),
            explanation=data.get("explanation", ""),
            predicted_metrics=data.get("predicted_metrics", {}),
            content_dna=data.get("content_dna", {}),
            trend_alignment=data.get("trend_alignment", {}),
            suggestions=data.get("suggestions", []),
            optimized_variants=data.get("optimized_variants", []),
            platform_optimizations=data.get("platform_optimizations", []),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "id": record.id,
            "content_id": record.content_id,
            "virality_score": record.virality_score,
            "explanation": record.explanation,
            "predicted_metrics": record.predicted_metrics,
            "content_dna": record.content_dna,
            "trend_alignment": record.trend_alignment,
            "suggestions": record.suggestions,
            "optimized_variants": record.optimized_variants,
            "platform_optimizations": record.platform_optimizations,
            "created_at": str(record.created_at),
        }
    finally:
        db.close()


def _sqlite_get_analysis(analysis_id: int) -> Optional[Dict[str, Any]]:
    from models.content_model import Analysis
    db = _get_db_session()
    try:
        record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not record:
            return None
        return {
            "id": record.id,
            "content_id": record.content_id,
            "virality_score": record.virality_score,
            "explanation": record.explanation,
            "predicted_metrics": record.predicted_metrics,
            "content_dna": record.content_dna,
            "trend_alignment": record.trend_alignment,
            "suggestions": record.suggestions,
            "optimized_variants": record.optimized_variants,
            "platform_optimizations": record.platform_optimizations,
            "created_at": str(record.created_at),
        }
    finally:
        db.close()


def _sqlite_get_analysis_detail(analysis_id: int) -> Optional[Dict[str, Any]]:
    from models.content_model import Analysis, Content
    db = _get_db_session()
    try:
        row = (
            db.query(Analysis, Content)
            .join(Content, Analysis.content_id == Content.id)
            .filter(Analysis.id == analysis_id)
            .first()
        )
        if not row:
            return None
        analysis, content = row
        return {
            "id": analysis.id,
            "content_id": content.id,
            "content_type": content.content_type,
            "text_content": content.text_content,
            "media_url": content.media_path,
            "virality_score": analysis.virality_score,
            "explanation": analysis.explanation,
            "predicted_metrics": analysis.predicted_metrics,
            "content_dna": analysis.content_dna,
            "trend_alignment": analysis.trend_alignment,
            "suggestions": analysis.suggestions,
            "optimized_variants": analysis.optimized_variants,
            "platform_optimizations": analysis.platform_optimizations,
            "created_at": str(analysis.created_at),
        }
    finally:
        db.close()


def _sqlite_get_history(limit: int, offset: int, content_type: Optional[str]) -> Dict[str, Any]:
    from models.content_model import Analysis, Content
    from sqlalchemy import desc
    db = _get_db_session()
    try:
        query = (
            db.query(Analysis, Content)
            .join(Content, Analysis.content_id == Content.id)
            .order_by(desc(Analysis.created_at))
        )
        if content_type:
            query = query.filter(Content.content_type == content_type)
        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        items = []
        for analysis, content in rows:
            items.append({
                "id": analysis.id,
                "content_id": content.id,
                "content_type": content.content_type,
                "text_preview": (content.text_content[:120] + "...") if content.text_content and len(content.text_content) > 120 else content.text_content,
                "media_url": content.media_path,
                "virality_score": analysis.virality_score,
                "created_at": str(analysis.created_at),
            })
        return {"items": items, "total": total}
    finally:
        db.close()


def _sqlite_get_gallery(content_type: Optional[str], limit: int, offset: int) -> Dict[str, Any]:
    from models.content_model import Analysis, Content
    from sqlalchemy import desc
    db = _get_db_session()
    try:
        query = (
            db.query(Content, Analysis)
            .outerjoin(Analysis, Content.id == Analysis.content_id)
            .order_by(desc(Content.created_at))
        )
        if content_type:
            query = query.filter(Content.content_type == content_type)
        total = query.count()
        rows = query.offset(offset).limit(limit).all()
        items = []
        for content, analysis in rows:
            items.append({
                "id": content.id,
                "content_type": content.content_type,
                "text_preview": (content.text_content[:100] + "...") if content.text_content and len(content.text_content) > 100 else content.text_content,
                "media_url": content.media_path,
                "virality_score": analysis.virality_score if analysis else None,
                "analysis_id": analysis.id if analysis else None,
                "created_at": str(content.created_at),
            })
        return {"items": items, "total": total}
    finally:
        db.close()


def _sqlite_get_metrics() -> Dict[str, Any]:
    from models.content_model import Analysis, Content
    from sqlalchemy import func as sql_func
    from collections import defaultdict
    db = _get_db_session()
    try:
        total_analyses = db.query(Analysis).count()
        avg_score = db.query(sql_func.avg(Analysis.virality_score)).scalar()
        analyses = db.query(Analysis).order_by(Analysis.created_at).all()

        score_over_time = [{"date": str(a.created_at), "score": a.virality_score} for a in analyses]
        engagement_data = []
        for a in analyses:
            if a.predicted_metrics:
                metrics = a.predicted_metrics if isinstance(a.predicted_metrics, dict) else {}
                engagement_data.append({
                    "date": str(a.created_at),
                    "likes": metrics.get("likes", 0),
                    "shares": metrics.get("shares", 0),
                    "comments": metrics.get("comments", 0),
                })

        type_counts = db.query(Content.content_type, sql_func.count(Content.id)).group_by(Content.content_type).all()
        content_distribution = [{"type": t, "count": c} for t, c in type_counts]

        brackets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for a in analyses:
            s = a.virality_score
            if s <= 20: brackets["0-20"] += 1
            elif s <= 40: brackets["21-40"] += 1
            elif s <= 60: brackets["41-60"] += 1
            elif s <= 80: brackets["61-80"] += 1
            else: brackets["81-100"] += 1

        return {
            "total_analyses": total_analyses,
            "avg_virality_score": round(avg_score, 1) if avg_score else 0,
            "score_over_time": score_over_time,
            "engagement_data": engagement_data,
            "content_distribution": content_distribution,
            "score_distribution": [{"range": k, "count": v} for k, v in brackets.items()],
        }
    finally:
        db.close()


def _sqlite_get_profile() -> Dict[str, Any]:
    from models.user_model import User
    from models.content_model import Analysis
    from sqlalchemy import func as sql_func
    db = _get_db_session()
    try:
        user = db.query(User).first()
        if not user:
            user = User(**DEFAULT_PROFILE)
            db.add(user)
            db.commit()
            db.refresh(user)
        avg_score = db.query(sql_func.avg(Analysis.virality_score)).scalar()
        return {
            "id": user.id,
            "name": user.name,
            "niche": user.niche,
            "primary_platforms": user.primary_platforms or [],
            "audience_demographic": user.audience_demographic,
            "content_categories": user.content_categories or [],
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "avg_virality_score": round(avg_score, 1) if avg_score else 0,
        }
    finally:
        db.close()


def _sqlite_update_profile(update_data: Dict[str, Any]) -> Dict[str, Any]:
    from models.user_model import User
    db = _get_db_session()
    try:
        user = db.query(User).first()
        if not user:
            user = User(**DEFAULT_PROFILE)
            db.add(user)
            db.commit()
            db.refresh(user)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return {"status": "updated", "profile": {
            "id": user.id,
            "name": user.name,
            "niche": user.niche,
            "primary_platforms": user.primary_platforms or [],
            "audience_demographic": user.audience_demographic,
            "content_categories": user.content_categories or [],
            "bio": user.bio,
        }}
    finally:
        db.close()
