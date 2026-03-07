"""
SQLAlchemy models for content storage.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(20), nullable=False)  # text, image, video, audio
    text_content = Column(Text, nullable=True)
    media_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, nullable=False, index=True)
    virality_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    predicted_metrics = Column(JSON, nullable=False)
    content_dna = Column(JSON, nullable=False)
    trend_alignment = Column(JSON, nullable=False)
    suggestions = Column(JSON, nullable=False)
    optimized_variants = Column(JSON, nullable=False)
    platform_optimizations = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
