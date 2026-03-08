import pytest
from unittest.mock import patch, AsyncMock
import os
from services.video_analysis_service import analyze_video
from services.remote_llm_service import evaluate_video

@pytest.mark.asyncio
@patch("services.video_analysis_service.extract_frames")
@patch("services.vision_api_service.analyze_frames_batch")
@patch("services.transcription_service.transcribe_video")
async def test_video_orchestrator(mock_transcribe, mock_vision, mock_extract):
    # Mock local OpenCV
    mock_extract.return_value = ["/tmp/frame1.jpg", "/tmp/frame2.jpg"]
    
    # Mock remote Replicate
    mock_vision.return_value = {
        "captions": ["a person speaking", "a product demo"],
        "visual_tags": ["person speaking", "product demo"]
    }
    
    # Mock remote AssemblyAI
    mock_transcribe.return_value = {
        "transcript": "Secret exposed! Do you know how to build a viral app?",
        "keywords": ["secret", "app"]
    }
    
    result = await analyze_video("/mock/path/video.mp4")
    
    # Validate context aggregation
    assert len(result["frame_descriptions"]) == 2
    assert "person speaking" in result["visual_tags"]
    assert "Secret exposed!" in result["transcript"]
    
    # Validate hook engine detection
    assert result["hook_analysis"]["hook_strength"] > 0.3
    assert result["hook_analysis"]["hook_type"] in ["curiosity", "question"]
    assert "video_duration_analyzed" in result

@patch("services.remote_llm_service.Groq")
def test_remote_llm_evaluation(MockGroq):
    mock_client = MockGroq.return_value
    class MockMessage:
        content = '{"virality_score": 85, "suggestions": ["test"]}'
    class MockChoice:
        message = MockMessage()
        
    mock_client.chat.completions.create.return_value.choices = [MockChoice()]
    
    res = evaluate_video({"transcript": "test context"}, {"trend": "ai"})
    assert res.get("virality_score") == 85
    assert len(res.get("suggestions", [])) > 0
