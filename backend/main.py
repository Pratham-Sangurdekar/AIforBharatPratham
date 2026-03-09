"""
ENGAUGE Backend — FastAPI Application
AI-powered creator dashboard that predicts content performance.
Runs locally (uvicorn) or on AWS Lambda (via Mangum adapter).
"""

# Load .env BEFORE any other imports so that config.py and all services
# can read API keys (GROQ_API_KEY, GEMINI_API_KEY, etc.) via os.getenv().
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.analyze import router as analyze_router
from api.history import router as history_router
from api.trends import router as trends_router
from api.profile import router as profile_router
from api.gallery import router as gallery_router
from api.metrics import router as metrics_router
from config import is_local, ALLOWED_ORIGINS, LOCAL_MEDIA_DIR

# Create tables on startup (local/Render — SQLite)
if is_local():
    from database import engine, Base
    # Import all models so Base.metadata knows about them
    import models.content_model  # noqa: F401
    import models.user_model     # noqa: F401
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ENGAUGE API",
    description="AI-powered content performance prediction engine",
    version="0.2.0",
)

# CORS — allow frontend origins
# In production (Render), allow all origins since there's no sensitive auth.
# For stricter control, set ALLOWED_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local media directory (local mode only — in AWS, media is served from S3/CloudFront)
if is_local():
    MEDIA_DIR = os.path.join(os.path.dirname(__file__), LOCAL_MEDIA_DIR)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Register routers
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(history_router, prefix="/api", tags=["History"])
app.include_router(trends_router, prefix="/api", tags=["Trends"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])
app.include_router(gallery_router, prefix="/api", tags=["Gallery"])
app.include_router(metrics_router, prefix="/api", tags=["Metrics"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "engauge-api", "version": "0.2.0"}


@app.get("/api/status")
async def api_status():
    """Show which AI providers are configured and test each one."""
    import os, asyncio
    groq_key = bool(os.getenv("GROQ_API_KEY", ""))
    gemini_key = bool(os.getenv("GEMINI_API_KEY", ""))
    assemblyai_key = bool(os.getenv("ASSEMBLYAI_API_KEY", ""))
    replicate_key = bool(os.getenv("REPLICATE_API_TOKEN", ""))
    aws_key = bool(os.getenv("AWS_ACCESS_KEY_ID", ""))

    providers = ["groq"] if groq_key else []
    if aws_key:
        providers.append("bedrock")

    return {
        "providers": providers,
        "keys_configured": {
            "GROQ_API_KEY": groq_key,
            "GEMINI_API_KEY": gemini_key,
            "ASSEMBLYAI_API_KEY": assemblyai_key,
            "REPLICATE_API_TOKEN": replicate_key,
            "AWS_ACCESS_KEY_ID": aws_key,
        },
    }


@app.get("/api/test-providers")
async def test_providers():
    """Actually test each configured provider with a minimal call and report errors."""
    import os, traceback, asyncio
    results = {}

    # Test Groq LLM
    if os.getenv("GROQ_API_KEY", ""):
        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            resp = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5,
                )
            )
            results["groq_llm"] = {"ok": True, "response": resp.choices[0].message.content.strip()[:50]}
        except Exception as e:
            results["groq_llm"] = {"ok": False, "error": str(e), "type": type(e).__name__}
    else:
        results["groq_llm"] = {"ok": False, "error": "GROQ_API_KEY not set"}

    # Test Gemini
    if os.getenv("GEMINI_API_KEY", ""):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
            resp = await asyncio.to_thread(lambda: model.generate_content("Say OK"))
            results["gemini"] = {"ok": True, "response": resp.text.strip()[:50]}
        except Exception as e:
            results["gemini"] = {"ok": False, "error": str(e), "type": type(e).__name__}
    else:
        results["gemini"] = {"ok": False, "error": "GEMINI_API_KEY not set"}

    # Test Bedrock
    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    if aws_key:
        try:
            import boto3
            sts = boto3.client("sts", region_name=os.getenv("AWS_REGION", "us-east-1"))
            identity = await asyncio.to_thread(sts.get_caller_identity)
            results["bedrock"] = {"ok": True, "account": identity.get("Account", "?")}
        except Exception as e:
            results["bedrock"] = {"ok": False, "error": str(e), "type": type(e).__name__}
    else:
        results["bedrock"] = {"ok": False, "error": "AWS_ACCESS_KEY_ID not set"}

    # Check ffmpeg (needed for video transcription)
    import shutil
    results["ffmpeg"] = {"ok": bool(shutil.which("ffmpeg"))}

    return results


@app.post("/api/clear-cache")
async def clear_cache():
    """Clear the in-memory analysis cache (useful after fixing config issues)."""
    from services.database_service import _analysis_cache
    count = len(_analysis_cache)
    _analysis_cache.clear()
    return {"cleared": count}

