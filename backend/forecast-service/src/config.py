import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "disease_management")

MODEL_DIR = Path(os.getenv("FORECAST_MODEL_DIR", BASE_DIR / "models"))
DEFAULT_HISTORY_DAYS = int(os.getenv("FORECAST_HISTORY_DAYS", "180"))
DEFAULT_FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", "14"))
MIN_TRAINING_DAYS = int(os.getenv("FORECAST_MIN_TRAINING_DAYS", "7"))
