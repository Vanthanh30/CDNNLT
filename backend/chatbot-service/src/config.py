from dotenv import load_dotenv
import os
from pathlib import Path

# load .env đúng path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API gateway
GATEWAY_URL = "http://localhost:8080/internal/search"