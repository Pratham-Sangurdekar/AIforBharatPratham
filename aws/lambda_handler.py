"""
AWS Lambda Handler — Wraps the FastAPI app using Mangum.
This is the entry point when running on AWS Lambda + API Gateway.
"""

import os

# Force AWS mode when running in Lambda
os.environ.setdefault("ENGAUGE_ENV", "aws")

from mangum import Mangum
from main import app

# Mangum adapter translates API Gateway events to ASGI
handler = Mangum(app, lifespan="off")
