# ENGAUGE — AI-Powered Creator Dashboard

> Analyse, optimise, and predict the virality of your content using **free, local AI models**.  
> No paid APIs required. Everything runs on your machine.

---

## What It Does

ENGAUGE is a full-stack creator dashboard that:

| Feature | How |
|---------|-----|
| **AI Content Analysis** | Local LLM via [Ollama](https://ollama.com) (Mistral / Llama 3 / Phi-3) |
| **Image Understanding** | BLIP captioning + CLIP zero-shot classification |
| **Video Analysis** | OpenCV frame extraction → BLIP/CLIP + Whisper transcription |
| **Audio Transcription** | OpenAI Whisper (runs locally, completely free) |
| **Real-Time Trends** | Reddit public JSON, Google Trends (pytrends), GDELT news |
| **Virality Scoring** | 6-factor hybrid formula (AI + trend + hook + emotion + visual + clarity) |
| **Content DNA** | Hook type, emotion, structure, psychological triggers |
| **Suggestions** | Actionable, trend-aware, media-aware improvement recommendations |
| **AWS Compatible** | Can switch to Bedrock/DynamoDB/S3 by toggling env vars |

---

## Architecture

```
┌─────────────────────────────────────┐
│            Next.js Frontend         │
│   Dashboard / Editor / Trends /     │
│   Gallery / History / Metrics       │
└───────────────┬─────────────────────┘
                │  REST API
┌───────────────▼─────────────────────┐
│          FastAPI Backend            │
│                                     │
│  ┌──────────┐  ┌─────────────────┐  │
│  │  Ollama  │  │  BLIP / CLIP    │  │
│  │  (LLM)   │  │  (Image AI)     │  │
│  └──────────┘  └─────────────────┘  │
│  ┌──────────┐  ┌─────────────────┐  │
│  │ Whisper  │  │  OpenCV         │  │
│  │ (Audio)  │  │  (Video frames) │  │
│  └──────────┘  └─────────────────┘  │
│  ┌──────────────────────────────┐   │
│  │  Trend Engine (Reddit /      │   │
│  │  Google Trends / GDELT)      │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  SQLite (local) or DynamoDB  │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **Ollama** | Latest | Local LLM inference |
| **ffmpeg** | Any | Video audio extraction (optional) |

---

## Quick Start

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start the server
ollama serve

# Pull a model (pick one)
ollama pull mistral      # default, balanced
# ollama pull llama3     # stronger, slower
# ollama pull phi3       # smallest, fastest
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# The first run will auto-download BLIP, CLIP, and Whisper models (~2-3 GB total)
# This only happens once.

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open **http://localhost:3000** — the dashboard is ready.

---

## Environment Variables

All configuration lives in `backend/.env`:

```env
# --- AI Model Selection ---
USE_LOCAL_LLM=true              # Use Ollama (set false to use Bedrock)
LOCAL_LLM_MODEL=mistral         # Ollama model name
WHISPER_MODEL_SIZE=base         # tiny | base | small

# --- Trend Engine ---
TREND_REFRESH_INTERVAL=600      # Seconds between trend refreshes (default 10 min)

# --- AWS (only needed if USE_LOCAL_LLM=false) ---
ENGAUGE_ENV=local               # local | aws
USE_LLM=false
AWS_DEFAULT_REGION=us-east-1
```

---

## AI Models Used

| Model | Size | Purpose | Loaded |
|-------|------|---------|--------|
| **Mistral 7B** (via Ollama) | ~4 GB | Content analysis, suggestions, variants | On first LLM call |
| **BLIP** (Salesforce/blip-image-captioning-base) | ~1 GB | Image captioning | On first image analysis |
| **CLIP** (openai/clip-vit-base-patch32) | ~600 MB | Image classification (themes, emotions, meme detection) | On first image analysis |
| **Whisper base** | ~150 MB | Audio/video transcription | On first audio analysis |

All models are downloaded automatically on first use and cached locally.

---

## Project Structure

```
backend/
├── main.py                       # FastAPI app entry
├── config.py                     # Environment & feature flags
├── database.py                   # SQLite / DynamoDB setup
├── .env                          # Local env vars
├── requirements.txt              # Python dependencies
├── api/
│   ├── analyze.py                # Multimodal analysis endpoint
│   ├── trends.py                 # Real-time trends endpoint
│   ├── history.py                # Analysis history
│   ├── metrics.py                # Dashboard metrics
│   ├── gallery.py                # Content gallery
│   └── profile.py                # User profile
├── models/
│   ├── content_model.py          # Content SQLAlchemy model
│   └── user_model.py             # User model
└── services/
    ├── local_llm_service.py      # Ollama integration (Section 1)
    ├── llm_service.py            # LLM router (local → Bedrock → heuristic)
    ├── trend_engine.py           # Real-time trend provider (Section 2)
    ├── image_analysis_service.py # BLIP + CLIP (Section 3)
    ├── video_analysis_service.py # OpenCV + Whisper + BLIP/CLIP (Section 4)
    ├── audio_analysis_service.py # Whisper transcription (Section 5)
    ├── content_analyzer.py       # Content type detection
    ├── viral_score_engine.py     # 6-factor hybrid scoring (Section 8)
    ├── optimization_engine.py    # Suggestion generation (Section 9)
    ├── platform_adapter.py       # Platform-specific optimisations
    ├── database_service.py       # Storage abstraction
    └── storage_service.py        # File storage (local / S3)

frontend/
├── src/
│   ├── app/(dashboard)/
│   │   ├── page.tsx              # Dashboard home
│   │   ├── editor/page.tsx       # Content editor
│   │   ├── trends/page.tsx       # Real-time trends (Section 10)
│   │   ├── gallery/page.tsx      # Media gallery (Section 11)
│   │   ├── history/page.tsx      # Analysis history
│   │   └── metrics/page.tsx      # Performance metrics
│   ├── components/               # Shared UI components
│   └── services/api.ts           # Backend API client

aws/
├── template.yaml                 # SAM template
├── lambda_handler.py             # Lambda entry
├── trend_ingestion_handler.py    # Multi-source trend ingestion
└── deploy.sh                     # Deployment script
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze` | Analyse text, image, video, or audio content |
| GET | `/api/trends` | Get trending topics by category |
| GET | `/api/trends/live` | Live trends with source & popularity data |
| GET | `/api/trends/platforms` | Platform-specific trends |
| GET | `/api/history` | Past analyses with pagination |
| GET | `/api/history/:id` | Single analysis detail |
| GET | `/api/gallery` | Content gallery with filters |
| GET | `/api/metrics` | Dashboard aggregate metrics |
| GET | `/api/profile` | User profile |
| PUT | `/api/profile` | Update profile |

---

## Virality Scoring Formula

The hybrid score blends 6 factors:

```
Score = 0.40 × AI Score
      + 0.20 × Trend Relevance
      + 0.15 × Hook Strength
      + 0.10 × Emotional Intensity
      + 0.10 × Visual Engagement
      + 0.05 × Clarity
```

Each factor is scored 0–100 and displayed in the dashboard breakdown bars.

---

## Switching to AWS

To deploy on AWS with Bedrock instead of local models:

```env
ENGAUGE_ENV=aws
USE_LOCAL_LLM=false
USE_LLM=true
AWS_DEFAULT_REGION=us-east-1
```

Then deploy with SAM:

```bash
cd aws
./deploy.sh
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama not found | Run `ollama serve` in a separate terminal |
| Model not available | Run `ollama pull mistral` |
| BLIP/CLIP slow first time | Models download on first use (~1.6 GB). Subsequent loads are instant. |
| Whisper not found | `pip install openai-whisper` |
| ffmpeg not found | `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux) |
| Trends not loading | Trends refresh in background every 10 min. Wait 30s after startup. |
| Out of memory | Use `WHISPER_MODEL_SIZE=tiny` and `LOCAL_LLM_MODEL=phi3` |

---

## Tech Stack

**Backend**: Python 3.11, FastAPI, SQLAlchemy, Ollama, HuggingFace Transformers, OpenCV, Whisper  
**Frontend**: Next.js 16, TypeScript, TailwindCSS v4, Framer Motion, Recharts  
**AI Models**: Mistral 7B, BLIP, CLIP, Whisper (all free, local, open-source)  
**Data Sources**: Reddit, Google Trends, GDELT (all free, no API keys required)

---

## License

MIT
