"""
History API — Retrieve past analyses via service abstraction.

Enhancements:
- Sort parameter:  newest (default) | oldest | score_desc
- Media URL resolution via storage_service (pre-signed S3 URLs)
- Thumbnail / preview metadata attached to each record
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from services import database_service, storage_service

router = APIRouter()


@router.get("/history")
def get_history(
    limit: int = 20,
    offset: int = 0,
    content_type: Optional[str] = None,
    sort: Optional[str] = "newest",
):
    """
    Retrieve analysis history.

    Query params:
      - limit / offset   : pagination
      - content_type      : optional filter
      - sort              : newest | oldest | score_desc
    """
    result = database_service.get_history(limit, offset, content_type)

    # get_history returns {"items": [...], "total": N}
    items = result.get("items", []) if isinstance(result, dict) else result
    total = result.get("total", 0) if isinstance(result, dict) else len(result)

    # Enrich each record with resolved media URL and sort
    enriched = []
    for rec in items:
        if not isinstance(rec, dict):
            continue
        media_path = rec.get("media_url") or rec.get("media_path")
        if media_path:
            rec["media_url"] = storage_service.get_file_url(media_path)
        # Attach a short text preview (first 120 chars)
        text = rec.get("text") or rec.get("content_text") or ""
        rec["text_preview"] = text[:120] + ("…" if len(text) > 120 else "")
        enriched.append(rec)

    # Client-side sort (DB may not support ORDER BY in DynamoDB scans)
    if sort == "oldest":
        enriched.sort(
            key=lambda r: r.get("created_at", ""), reverse=False
        )
    elif sort == "score_desc":
        enriched.sort(
            key=lambda r: float(r.get("virality_score", 0)), reverse=True
        )
    else:
        # newest first (default)
        enriched.sort(
            key=lambda r: r.get("created_at", ""), reverse=True
        )

    return {"items": enriched, "total": total}


@router.get("/history/{analysis_id}")
def get_analysis_detail(analysis_id: str):
    """Get full analysis detail by ID, with resolved media URL."""
    result = database_service.get_analysis_detail(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    media_path = result.get("media_url") or result.get("media_path")
    if media_path:
        result["media_url"] = storage_service.get_file_url(media_path)

    return result
