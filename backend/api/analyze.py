"""
Analysis API — Main content analysis endpoint.
Orchestrates the full multimodal pipeline via service abstractions.

Capabilities:
- Text analysis via Groq LLM or local Ollama / Bedrock
- Image analysis via Gemini or local BLIP/CLIP
- Video analysis via serverless pipeline (Replicate + AssemblyAI + Groq Llama-3)
- Audio analysis via Groq Whisper or local Whisper
- Content hash caching to avoid repeated API calls
- Hybrid virality scoring (Section 8 formula)
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

    Priority: Gemini API (free, online) → Local models (BLIP/CLIP/Whisper).
    Returns a media_context dict that gets passed to the LLM.
    """
    media_context: Dict[str, Any] = {}

    if content_type == "image":
        # Try Gemini first
        try:
            from services.gemini_analysis_service import (
                analyze_image_with_gemini,
                is_gemini_available,
            )
            if is_gemini_available():
                result = await analyze_image_with_gemini(file_bytes)
                media_context = {
                    "caption": result.get("caption", ""),
                    "detected_objects": result.get("detected_objects", []),
                    "visual_theme": result.get("visual_theme", ""),
                    "emotional_tone": result.get("emotional_tone", ""),
                    "meme_probability": result.get("meme_probability", 0),
                    "visual_quality": result.get("visual_quality", ""),
                    "composition_notes": result.get("composition_notes", ""),
                    "improvement_suggestions": result.get("improvement_suggestions", []),
                }
                return media_context
        except Exception as e:
            logger.warning("Gemini image analysis failed, trying local: %s", e)

        # Fallback to local BLIP/CLIP
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
            logger.warning("Local image analysis also failed: %s", e)

    elif content_type == "video":
        # Video is handled by the dedicated serverless pipeline in the main
        # endpoint (see SERVERLESS VIDEO PIPELINE below).  This branch is a
        # no-op — kept for interface completeness.
        pass

    elif content_type == "audio":
        # Try Groq Whisper first
        try:
            from services.gemini_analysis_service import _transcribe_with_groq_whisper
            import tempfile, os
            tmp = tempfile.mktemp(suffix=".wav")
            with open(tmp, "wb") as f:
                f.write(file_bytes)
            transcript = _transcribe_with_groq_whisper(tmp)
            os.unlink(tmp)
            if transcript:
                media_context = {
                    "transcript": transcript,
                    "emotional_tone": "",
                    "detected_topics": [],
                    "key_phrases": [],
                    "speech_pace": "moderate",
                    "engagement_potential": 0.5,
                }
                return media_context
        except Exception as e:
            logger.warning("Groq Whisper audio failed, trying local: %s", e)

        # Fallback to local Whisper
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
            logger.warning("Local audio analysis also failed: %s", e)

    return media_context


@router.post("/analyze")
async def analyze_content(
    text: Optional[str] = Form(None),
    platform: Optional[str] = Form("general"),
    llm_provider: Optional[str] = Form("groq"),
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
        content_hash = llm_service.compute_content_hash(text, platform or "general", llm_provider)
        cached = await asyncio.to_thread(database_service.get_cached_analysis, content_hash)
        if cached:
             return cached

        # --- Step 3: Save media ---
        media_path = None
        file_bytes = None
        if file:
            file_bytes = await file.read()
            media_path = storage_service.save_file(file_bytes, file.filename)

        # --- Store content record ---
        content_record = await asyncio.to_thread(database_service.save_content, content_type, text, media_path)

        # --- SERVERLESS VIDEO PIPELINE (Section 10) ---
        if content_type == "video" and file_bytes:
            import tempfile, os
            from services.video_analysis_service import analyze_video
            from services.remote_llm_service import evaluate_video

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(file_bytes)

            try:
                # 1. Frame extraction + Replicate vision + AssemblyAI/Groq transcription + hook detection
                media_context = await asyncio.wait_for(
                    analyze_video(tmp_path),
                    timeout=180,      # 3-minute ceiling
                )

                # 2. LLM reasoning via Groq Llama-3
                trending = await asyncio.to_thread(database_service.get_trends)
                analysis_result = await asyncio.to_thread(evaluate_video, media_context, trending)

                # 3. Hybrid scoring (Section 8 formula)
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

                analysis_result["virality_score"] = hybrid_score
                platform_optimizations = PlatformAdapter.get_all_platform_optimizations(text or "")
                analysis_result["platform_optimizations"] = platform_optimizations

                # --- Build frontend-compatible video_analysis object ---
                frame_descs = media_context.get("frame_descriptions", [])
                non_empty = [d for d in frame_descs if d and "unable" not in d.lower()]
                content_summary = " ".join(non_empty[:5]) if non_empty else "Video frames were extracted but could not be described."

                hook_str = media_context.get("hook_strength", 0)
                hook_tp = media_context.get("hook_type", "unknown")
                hook_desc = media_context.get("hook_description", "")
                hook_assessment = f"{hook_tp.replace('_', ' ').title()} hook — strength {hook_str}/100"
                if hook_desc:
                    hook_assessment += f". {hook_desc}"

                pacing = media_context.get("pacing_score", 50)
                if pacing > 70:
                    pacing_text = f"Pacing score {pacing}/100 — fast-paced and engaging content with dynamic visual changes."
                elif pacing > 40:
                    pacing_text = f"Pacing score {pacing}/100 — moderate pacing. Consider adding more cuts or transitions to increase energy."
                else:
                    pacing_text = f"Pacing score {pacing}/100 — slow-paced. Try shorter clips, faster cuts, and more visual variety."

                improvement_actions = analysis_result.get("suggestions", [])[:5]
                hook_imp = media_context.get("hook_improvement")
                if hook_imp and hook_imp not in improvement_actions:
                    improvement_actions.insert(0, hook_imp)

                analysis_result["video_analysis"] = {
                    "content_summary": content_summary,
                    "hook_assessment": hook_assessment,
                    "pacing_notes": pacing_text,
                    "improvement_actions": improvement_actions,
                }

                # Enrich media_context with fields the frontend reads
                media_context["caption"] = content_summary
                media_context["detected_objects"] = media_context.get("visual_tags", [])

            except asyncio.TimeoutError:
                logger.error("Video pipeline timed out after 180 s")
                raise HTTPException(status_code=504, detail="Video analysis timed out. Try a shorter video.")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
            analysis_record = await asyncio.to_thread(database_service.save_analysis, content_record["id"], analysis_result)
            
        else:
            # --- STANDARD PIPELINE (Text, Images, Audio) ---
            media_context: Dict[str, Any] = {}
            if file_bytes and content_type in ("image", "audio"):
                try:
                    media_context = await asyncio.wait_for(
                        _analyze_media(content_type, file_bytes, filename or "file"),
                        timeout=120,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Media analysis timed out for %s", content_type)
                except Exception as e:
                    logger.warning("Media analysis error for %s: %s", content_type, e)
                logger.info(
                    "Media analysis complete for %s: %d context keys",
                    content_type, len(media_context),
                )
    
            trending = await asyncio.to_thread(database_service.get_trends)
            analysis_result = await llm_service.analyze_content_with_llm(
                text, content_type, trending, platform, media_context=media_context, llm_provider=llm_provider
            )
    
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
    
            analysis_result["virality_score"] = hybrid_score
            platform_optimizations = PlatformAdapter.get_all_platform_optimizations(text)
            analysis_result["platform_optimizations"] = platform_optimizations
    
            analysis_record = database_service.save_analysis(content_record["id"], analysis_result)

        # --- Cache the result for future identical content ---
        analysis_mode = analysis_result.get("analysis_mode", "ai")
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
            "image_analysis": analysis_result.get("image_analysis"),
            "video_analysis": analysis_result.get("video_analysis"),
            "score_breakdown": score_breakdown,
            "analysis_mode": analysis_mode,
            "created_at": analysis_record.get("created_at", ""),
        }

        await asyncio.to_thread(database_service.cache_analysis, content_hash, response_payload)

        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        # Check for rate-limit errors from Gemini/Groq
        from services.gemini_analysis_service import RateLimitError
        if isinstance(e, RateLimitError) or "429" in str(e) or "quota" in str(e).lower():
            raise HTTPException(status_code=429, detail="Too many requests, please try a few minutes later")
        logger.exception("Unhandled error in analyze_content")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
