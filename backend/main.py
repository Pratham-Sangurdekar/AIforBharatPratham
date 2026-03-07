"""
ENGAUGE Backend — FastAPI Application
AI-powered creator dashboard that predicts content performance.
Runs locally (uvicorn) or on AWS Lambda (via Mangum adapter).
"""

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

# Create tables on startup (local mode only)
if is_local():
    from database import engine, Base
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ENGAUGE API",
    description="AI-powered content performance prediction engine",
    version="0.2.0",
)

# CORS — allow frontend (configurable via env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
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

