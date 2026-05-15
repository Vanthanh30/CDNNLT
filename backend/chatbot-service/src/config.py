from dotenv import load_dotenv
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
REPO_BACKEND_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

if not os.getenv("OPENAI_API_KEY"):
    load_dotenv(REPO_BACKEND_DIR / "report-service" / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API gateway
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000/internal/search")
