from dotenv import load_dotenv
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
REPO_BACKEND_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

if not os.getenv("CHATBOT_OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    load_dotenv(REPO_BACKEND_DIR / "report-service" / ".env")

OPENAI_API_KEY = os.getenv("CHATBOT_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("CHATBOT_OPENAI_MODEL") or os.getenv(
    "OPENAI_MODEL", "gpt-4.1-mini"
)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000/internal/search")
