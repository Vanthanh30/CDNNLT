import sys
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import database


BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_SERVICE_DIR = BASE_DIR / "report-service"

load_dotenv(REPORT_SERVICE_DIR / ".env")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8010")

app = FastAPI(title="Disease Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    database.init_db()


@app.get("/")
def root():
    return {"message": "Disease Management API is running"}


@app.get("/api/dashboard")
def read_dashboard():
    return database.get_all_processed_articles()


@app.get("/articles")
def get_articles():
    return database.get_all_processed_articles()


@app.get("/api/articles/filter")
def filter_articles(
    keyword: Optional[str] = None,
    disease_name: Optional[str] = None,
    location: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 50
):
    return database.filter_articles(
        keyword=keyword,
        disease_name=disease_name,
        location=location,
        from_date=from_date,
        to_date=to_date,
        risk_level=risk_level,
        limit=limit
    )


def _ensure_report_service_import_path():
    candidates = [
        REPORT_SERVICE_DIR / "src",
        Path("/app/report-service/src"),
    ]

    for path in candidates:
        if path.exists():
            path_str = str(path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
            return

    raise HTTPException(status_code=503, detail="Report service code is not available")


@app.get("/api/report/weekly/download")
def download_weekly_report():
    _ensure_report_service_import_path()

    from report_generator import generate_weekly_report

    result = generate_weekly_report()
    if not result:
        return {"message": "Không có dữ liệu"}

    pdf_buffer, filename = result
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/forecast")
def get_forecast(
    disease_name: Optional[str] = None,
    location: Optional[str] = None,
    days: int = 14,
    history_days: int = 180,
):
    params = {
        "days": str(days),
        "history_days": str(history_days),
    }
    if disease_name:
        params["disease_name"] = disease_name
    if location:
        params["location"] = location

    query = urllib.parse.urlencode(params)
    url = f"{FORECAST_SERVICE_URL.rstrip('/')}/forecast?{query}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=exc.code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Forecast service unavailable: {exc}")


@app.get("/api/forecast/diseases")
def get_disease_forecasts(
    location: Optional[str] = None,
    history_days: int = 180,
    limit: int = 12,
    top_n: int = 3,
):
    params = {
        "history_days": str(history_days),
        "limit": str(limit),
        "top_n": str(top_n),
    }
    if location:
        params["location"] = location

    query = urllib.parse.urlencode(params)
    url = f"{FORECAST_SERVICE_URL.rstrip('/')}/forecast/diseases?{query}"

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=exc.code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Forecast service unavailable: {exc}")
