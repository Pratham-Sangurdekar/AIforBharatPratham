"""
Pydantic schemas for analysis request/response.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class PredictedMetrics(BaseModel):
    likes: int
    shares: int
    comments: int


class ContentDNA(BaseModel):
    hook: str
    emotion: str
    structure: str
    psychological_triggers: List[str]


class TrendAlignment(BaseModel):
    matched_topics: List[str]
    relevance_score: float


class PlatformOptimization(BaseModel):
    platform: str
    optimized_text: str
    tips: List[str]


class AnalysisResponse(BaseModel):
    id: int
    content_id: int
    virality_score: float
    explanation: str
    predicted_metrics: PredictedMetrics
    content_dna: ContentDNA
    trend_alignment: TrendAlignment
    suggestions: List[str]
    optimized_variants: List[str]
    platform_optimizations: Optional[List[PlatformOptimization]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    text: Optional[str] = None
    platform: Optional[str] = "general"


class ContentHistoryItem(BaseModel):
    id: int
    content_id: int
    content_type: str
    text_preview: Optional[str]
    media_url: Optional[str]
    virality_score: float
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: List[ContentHistoryItem]
    total: int
