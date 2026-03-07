"""
Profile API — Creator profile management via service abstraction.
"""

from fastapi import APIRouter
from models.user_model import UserProfileUpdate
from services import database_service

router = APIRouter()


@router.get("/profile")
def get_profile():
    """Get creator profile."""
    return database_service.get_profile()


@router.put("/profile")
def update_profile(update: UserProfileUpdate):
    """Update creator profile."""
    update_data = update.model_dump(exclude_unset=True)
    return database_service.update_profile(update_data)
