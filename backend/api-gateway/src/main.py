from datetime import date, datetime
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
from pydantic import BaseModel

import requests
from . import database


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_SERVICE_DIR = BASE_DIR / "report-service"

load_dotenv(REPORT_SERVICE_DIR / ".env")

FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8010")

CHATBOT_SERVICE_URL = "http://localhost:8001/chat"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="Disease Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELS
# ============================================================


class ChatRequest(BaseModel):
    question: str


# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
def startup_event():
    database.init_db()


# ============================================================
# ROOT
# ============================================================


@app.get("/")
def root():
    return {"message": "Disease Management API is running"}


# ============================================================
# DASHBOARD + ARTICLES
# ============================================================


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
    limit: int = 50,
):
    return database.filter_articles(
        keyword=keyword,
        disease_name=disease_name,
        location=location,
        from_date=from_date,
        to_date=to_date,
        risk_level=risk_level,
        limit=limit,
    )


# ============================================================
# MAP LOCATIONS
# ============================================================


@app.get("/locations")
def get_locations(hours: Optional[int] = None):
    conn = database.get_connection()

    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        time_filter = ""

        if hours is not None and hours > 0:
            time_filter = f"""
            AND (
                COALESCE(r.published_at, a.processed_at)
                >= DATE_SUB(NOW(), INTERVAL {int(hours)} HOUR)
            )
            """

        query = f"""
            SELECT
                rg.name AS location_name,
                COUNT(de.id) AS article_count,
                GROUP_CONCAT(r.title SEPARATOR '|||') AS article_titles
            FROM DISEASE_EVENT de
            JOIN REGION rg ON de.region_id = rg.id
            JOIN ARTICLE a ON de.article_id = a.id
            JOIN RAW_ARTICLE r ON a.raw_article_id = r.id
            WHERE 1 = 1
            {time_filter}
            GROUP BY rg.id, rg.name
            ORDER BY article_count DESC
            LIMIT 50
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        LOCATION_COORDS = {
            "Hà Nội": {"lat": 21.0285, "lng": 105.8542},
            "TP. Hồ Chí Minh": {"lat": 10.8231, "lng": 106.6297},
            "Đà Nẵng": {"lat": 16.0544, "lng": 108.2022},
            "Kon Tum": {"lat": 14.3569, "lng": 108.0097},
            "Gia Lai": {"lat": 13.9833, "lng": 108.0167},
            "Đắk Lắk": {"lat": 12.6667, "lng": 108.0333},
        }

        result = []

        for row in rows:
            location_name = row["location_name"]

            if location_name not in LOCATION_COORDS:
                continue

            coords = LOCATION_COORDS[location_name]

            titles_str = row["article_titles"] or ""

            articles = [t.strip() for t in titles_str.split("|||") if t.strip()][:5]

            result.append(
                {
                    "name": location_name,
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "count": row["article_count"],
                    "articles": articles,
                }
            )

        return result

    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


# ============================================================
# REPORT SERVICE
# ============================================================


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


def _download_monthly_report():
    _ensure_report_service_import_path()

    from report_generator import generate_monthly_report

    result = generate_monthly_report()
    result = generate_weekly_report()

    if not result:
        return {"message": "Không có dữ liệu"}

    pdf_buffer, filename = result

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/report/monthly/download")
def download_monthly_report():
    return _download_monthly_report()


@app.get("/api/report/weekly/download")
def download_weekly_report():
    return _download_monthly_report()


# ============================================================
# FORECAST
# ============================================================


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
        raise HTTPException(
            status_code=503, detail=f"Forecast service unavailable: {exc}"
        )


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
        raise HTTPException(
            status_code=503, detail=f"Forecast service unavailable: {exc}"
        )


# ============================================================
# CHATBOT
# ============================================================


def serialize_rows(rows):
    result = []

    for row in rows:
        new_row = {}

        for k, v in row.items():
            if isinstance(v, (date, datetime)):
                new_row[k] = v.isoformat()
            else:
                new_row[k] = v

        result.append(new_row)

    return result


@app.post("/api/chat")
def chat(request: ChatRequest):
    rows = database.search_chatbot_context(request.question, limit=5)

    if not rows:
        return {"answer": "Không tìm thấy dữ liệu phù hợp.", "sources": []}

    ai_answer = call_chatbot_service(request.question, rows)

    sources = []

    for row in rows:
        sources.append(
            {
                "title": row.get("title"),
                "url": row.get("url"),
                "disease_name": row.get("disease_name"),
                "location": row.get("location"),
                "risk_level": row.get("risk_level"),
            }
        )

    return {"answer": ai_answer, "sources": sources}


def call_chatbot_service(question, rows):
    try:
        response = requests.post(
            CHATBOT_SERVICE_URL,
            json={
                "question": question,
                "context": serialize_rows(rows),
            },
            timeout=10,
        )

        if response.status_code == 200:
            return response.json().get("answer")

        return "Chatbot service đang lỗi."

    except Exception as e:
        print("❌ Lỗi gọi chatbot-service:", e)
        return "Không thể kết nối chatbot-service."


@app.get("/internal/search")
def search_for_chatbot(question: str):
    return database.search_chatbot_context(question, limit=20)
