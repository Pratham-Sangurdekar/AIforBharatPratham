"""
User model for creator profile.
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel
from typing import List, Optional


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), default="Creator")
    niche = Column(String(200), default="General")
    primary_platforms = Column(JSON, default=list)
    audience_demographic = Column(String(200), default="18-35, Global")
    content_categories = Column(JSON, default=list)
    bio = Column(Text, default="")
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic schemas
class UserProfile(BaseModel):
    id: int
    name: str
    niche: str
    primary_platforms: List[str]
    audience_demographic: str
    content_categories: List[str]
    bio: str
    avatar_url: Optional[str] = None
    avg_virality_score: Optional[float] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    niche: Optional[str] = None
    primary_platforms: Optional[List[str]] = None
    audience_demographic: Optional[str] = None
    content_categories: Optional[List[str]] = None
    bio: Optional[str] = None
