#!/bin/bash
# Start ENGAUGE backend server
# Suppresses noisy ML model output that causes tty suspension issues

cd "$(dirname "$0")"
source .venv/bin/activate

# Suppress HuggingFace progress bars and warnings
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TRANSFORMERS_NO_ADVISORY_WARNINGS=1
export TOKENIZERS_PARALLELISM=false

exec python -m uvicorn main:app --host 127.0.0.1 --port 8000
