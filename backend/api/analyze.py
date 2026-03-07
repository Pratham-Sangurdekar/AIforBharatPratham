"""
Analysis API — Main content analysis endpoint.
Orchestrates the full multimodal pipeline via service abstractions.

Capabilities:
- Text analysis via local LLM (Ollama) or Bedrock
- Image analysis via BLIP + CLIP
- Video analysis via OpenCV + Whisper + BLIP/CLIP
- Audio analysis via Whisper
- Content hash caching to avoid repeated analysis calls
- Hybrid virality scoring blending AI + heuristic sub-signals
- Score breakdown dict for frontend visualisation bars
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, Dict, Any

from services.content_analyzer import ContentAnalyzer
from services.platform_adapter import PlatformAdapter
from services.viral_score_engine import ViralScoreEngine
from services import llm_service, storage_service, database_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Media analysis dispatcher
# ---------------------------------------------------------------------------

async def _analyze_media(
    content_type: str, file_bytes: bytes, filename: str
) -> Dict[str, Any]:
    """Route media to the appropriate analysis service.

    Returns a media_context dict that gets passed to the LLM.
    """
    media_context: Dict[str, Any] = {}

    if content_type == "image":
        try:
            from services.image_analysis_service import analyze_image
            result = await analyze_image(file_bytes)
            media_context = {
                "caption": result.get("caption", ""),
                "detected_objects": result.get("detected_objects", []),
                "visual_theme": result.get("visual_theme", ""),
                "emotional_tone": result.get("emotional_tone", ""),
                "meme_probability": result.get("meme_probability", 0),
            }
        except Exception as e:
            logger.warning("Image analysis failed: %s", e)

    elif content_type == "video":
        try:
            from services.video_analysis_service import analyze_video
            result = await analyze_video(file_bytes, filename)
            media_context = {
                "transcript": result.get("transcript", ""),
                "detected_objects": result.get("visual_elements", []),
                "emotional_tone": result.get("emotional_tone", ""),
                "detected_topics": result.get("detected_topics", []),
                "hook_strength": result.get("hook_strength", 0.5),
                "pacing_score": result.get("pacing_score", 0.5),
            }
        except Exception as e:
            logger.warning("Video analysis failed: %s", e)

    elif content_type == "audio":
        try:
            from services.audio_analysis_service import analyze_audio
            result = await analyze_audio(file_bytes, filename)
            media_context = {
                "transcript": result.get("transcript", ""),
                "emotional_tone": result.get("emotional_tone", ""),
                "detected_topics": result.get("topic_keywords", []),
                "key_phrases": result.get("key_phrases", []),
                "speech_pace": result.get("speech_pace", "moderate"),
                "engagement_potential": result.get("engagement_potential", 0.5),
            }
        except Exception as e:
            logger.warning("Audio analysis failed: %s", e)

    return media_context


@router.post("/analyze")
async def analyze_content(
    text: Optional[str] = Form(None),
    platform: Optional[str] = Form("general"),
    file: Optional[UploadFile] = File(None),
):
    """
    Full multimodal analysis pipeline:
    1. Detect content type & extract metadata
    2. Check cache by content hash (skip AI if hit)
    3. Save media (S3 or local)
    4. Run media-specific analysis (image/video/audio)
    5. AI analysis with media context (Local LLM or Bedrock)
    6. Compute hybrid virality score + score breakdown
    7. Platform optimisations
    8. Cache & store results
    """
    import asyncio

    if not text and not file:
        raise HTTPException(
            status_code=400, detail="Provide text content or upload a file"
        )

    try:
        # --- Step 1: Detect type ---
        filename = file.filename if file else None
        content_type = ContentAnalyzer.detect_content_type(text, filename)

        # --- Step 2: Cache check via content hash ---
        content_hash = llm_service.compute_content_hash(text, platform or "general")
        cached = database_service.get_cached_analysis(content_hash)
        if cached:
            return cached

        # --- Step 3: Save media ---
        media_path = None
        file_bytes = None
        if file:
            file_bytes = await file.read()
            media_path = storage_service.save_file(file_bytes, file.filename)

        # --- Store content record ---
        content_record = database_service.save_content(content_type, text, media_path)

        # --- Step 4: Media-specific analysis ---
        media_context: Dict[str, Any] = {}
        if file_bytes and content_type in ("image", "video", "audio"):
            try:
                media_context = await asyncio.wait_for(
                    _analyze_media(content_type, file_bytes, filename or "file"),
                    timeout=120,  # 2 minute max for media analysis
                )
            except asyncio.TimeoutError:
                logger.warning("Media analysis timed out for %s", content_type)
            except Exception as e:
                logger.warning("Media analysis error for %s: %s", content_type, e)
            logger.info(
                "Media analysis complete for %s: %d context keys",
                content_type, len(media_context),
            )

        # --- Step 5: AI analysis (with media context) ---
        trending = database_service.get_trends()
        analysis_result = await llm_service.analyze_content_with_llm(
            text, content_type, trending, platform, media_context=media_context
        )

        # --- Step 6: Hybrid scoring ---
        ai_score = float(analysis_result.get("virality_score", 50))
        trend_relevance = float(
            analysis_result.get("trend_alignment", {}).get("relevance_score", 0)
        )
        content_dna = analysis_result.get("content_dna", {})

        hybrid_score = ViralScoreEngine.calculate_hybrid_score(
            ai_score, trend_relevance, content_dna, media_context
        )
        score_breakdown = ViralScoreEngine.get_score_breakdown(
            ai_score, trend_relevance, content_dna, media_context
        )

        # Override the raw AI score with the blended hybrid score
        analysis_result["virality_score"] = hybrid_score

        # --- Step 7: Platform optimisations ---
        platform_optimizations = PlatformAdapter.get_all_platform_optimizations(text)
        analysis_result["platform_optimizations"] = platform_optimizations

        # --- Step 8: Store analysis ---
        analysis_record = database_service.save_analysis(
            content_record["id"], analysis_result
        )

        # --- Cache the result for future identical content ---
        response_payload = {
            "id": analysis_record["id"],
            "content_id": content_record["id"],
            "virality_score": hybrid_score,
            "explanation": analysis_result.get("explanation", ""),
            "predicted_metrics": analysis_result.get("predicted_metrics", {}),
            "content_dna": content_dna,
            "trend_alignment": analysis_result.get("trend_alignment", {}),
            "suggestions": analysis_result.get("suggestions", []),
            "optimized_variants": analysis_result.get("optimized_variants", []),
            "platform_optimizations": platform_optimizations,
            "content_type": content_type,
            "media_url": media_path,
            "media_analysis": media_context,
            "score_breakdown": score_breakdown,
            "created_at": analysis_record.get("created_at", ""),
        }

        database_service.cache_analysis(content_hash, response_payload)

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in analyze_content")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
