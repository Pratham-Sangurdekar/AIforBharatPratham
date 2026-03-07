"""
Gallery API — Media gallery via service abstraction.
"""

from fastapi import APIRouter
from typing import Optional

from services import database_service

router = APIRouter()


@router.get("/gallery")
def get_gallery(
    content_type: Optional[str] = None,
    limit: int = 30,
    offset: int = 0,
):
    """Get all uploaded media with their analysis summaries."""
    return database_service.get_gallery(content_type, limit, offset)
