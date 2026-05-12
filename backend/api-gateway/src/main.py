from datetime import date, datetime, timedelta
import sys
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
from . import database


BASE_DIR = Path(__file__).resolve().parents[2]
REPORT_SERVICE_DIR = BASE_DIR / "report-service"

load_dotenv(REPORT_SERVICE_DIR / ".env")
FORECAST_SERVICE_URL = os.getenv("FORECAST_SERVICE_URL", "http://localhost:8010")

CHATBOT_SERVICE_URL = "http://localhost:8001/chat"
CHATBOT_SERVICE_URL = "http://localhost:8001/chat"

app = FastAPI(title="Disease Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


@app.on_event("startup")
def startup_event():
    database.init_db()


# ============================================================
# ✨ ENDPOINT CHO MAP - VỚI TIME FILTER
# ============================================================


@app.get("/locations")
def get_locations(hours: Optional[int] = None):
    """
    Trả về danh sách các vùng dịch bệnh với tọa độ GPS

    Query params:
    - hours (optional): Lọc dữ liệu trong N giờ qua (vd: 24 = 24 giờ qua)
               Nếu không có hoặc None, trả toàn bộ dữ liệu

    Response:
    [
      {
        "name": "Đà Nẵng",
        "lat": 16.0544,
        "lng": 108.2022,
        "count": 15,
        "articles": ["Tiêu đề bài 1", "Tiêu đề bài 2"]
      }
    ]
    """
    conn = database.get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ FIX: Thêm điều kiện thời gian nếu hours được truyền vào
        time_filter = ""
        if hours is not None and hours > 0:
            # Lọc theo processed_at của ARTICLE (thời điểm xử lý xong)
            # hoặc published_at của RAW_ARTICLE (nếu có)
            # Ưu tiên dùng published_at của RAW_ARTICLE nếu có, fallback sang processed_at
            time_filter = f"""
            AND (
                COALESCE(r.published_at, a.processed_at) >= DATE_SUB(NOW(), INTERVAL {int(hours)} HOUR)
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

        # Mapping tọa độ GPS cho các tỉnh/thành Việt Nam
        LOCATION_COORDS = {
            "Hà Nội": {"lat": 21.0285, "lng": 105.8542},
            "TP. Hồ Chí Minh": {"lat": 10.8231, "lng": 106.6297},
            "Đà Nẵng": {"lat": 16.0544, "lng": 108.2022},
            "Hải Phòng": {"lat": 20.8449, "lng": 106.6881},
            "Cần Thơ": {"lat": 10.0379, "lng": 105.7869},
            "Huế": {"lat": 16.4637, "lng": 107.5909},
            "Hạ Long": {"lat": 20.9521, "lng": 107.0349},
            "Nha Trang": {"lat": 12.2388, "lng": 109.1967},
            "Đà Lạt": {"lat": 11.9404, "lng": 108.4453},
            "Vũng Tàu": {"lat": 10.3461, "lng": 107.0637},
            "Long Xuyên": {"lat": 10.3655, "lng": 105.4272},
            "Bắc Ninh": {"lat": 21.1857, "lng": 106.0738},
            "Hải Dương": {"lat": 20.9510, "lng": 106.3263},
            "Quảng Ninh": {"lat": 21.0394, "lng": 107.2847},
            "Nam Định": {"lat": 20.4200, "lng": 106.1733},
            "Thái Bình": {"lat": 20.4483, "lng": 106.5098},
            "Phú Thọ": {"lat": 21.6060, "lng": 105.3283},
            "Vĩnh Phúc": {"lat": 21.3343, "lng": 105.4050},
            "Thái Nguyên": {"lat": 21.5955, "lng": 105.8446},
            "Tuyên Quang": {"lat": 22.3155, "lng": 105.2173},
            "Cao Bằng": {"lat": 22.8667, "lng": 106.2500},
            "Bắc Kạn": {"lat": 22.1393, "lng": 105.8315},
            "Lạng Sơn": {"lat": 21.8507, "lng": 106.7633},
            "Hà Giang": {"lat": 22.8000, "lng": 104.9833},
            "Yên Bái": {"lat": 21.7250, "lng": 104.9167},
            "Điện Biên": {"lat": 21.3868, "lng": 103.0225},
            "Lai Châu": {"lat": 22.0418, "lng": 101.9831},
            "Sơn La": {"lat": 21.3333, "lng": 103.7667},
            "Hòa Bình": {"lat": 20.8142, "lng": 105.3383},
            "Thanh Hóa": {"lat": 19.8081, "lng": 105.7742},
            "Nghệ An": {"lat": 19.0304, "lng": 104.8517},
            "Hà Tĩnh": {"lat": 18.3393, "lng": 105.8931},
            "Quảng Bình": {"lat": 17.4706, "lng": 106.5903},
            "Quảng Trị": {"lat": 16.7411, "lng": 107.1852},
            "Thừa Thiên Huế": {"lat": 16.4637, "lng": 107.5909},
            "Quảng Nam": {"lat": 15.5393, "lng": 108.0122},
            "Quảng Ngãi": {"lat": 15.1188, "lng": 108.8068},
            "Bình Định": {"lat": 13.7832, "lng": 109.2245},
            "Phú Yên": {"lat": 13.0947, "lng": 109.0889},
            "Khánh Hòa": {"lat": 12.2388, "lng": 109.1967},
            "Ninh Thuận": {"lat": 11.5883, "lng": 109.0211},
            "Bình Thuận": {"lat": 11.3288, "lng": 108.0903},
            "Lâm Đồng": {"lat": 11.9404, "lng": 108.4453},
            "Đồng Nai": {"lat": 10.9449, "lng": 107.0636},
            "Bình Dương": {"lat": 11.3282, "lng": 106.6848},
            "Bà Rịa - Vũng Tàu": {"lat": 10.3461, "lng": 107.0637},
            "An Giang": {"lat": 10.5403, "lng": 105.1250},
            "Kiên Giang": {"lat": 10.0097, "lng": 104.7661},
            "Hậu Giang": {"lat": 9.7769, "lng": 105.5281},
            "Sóc Trăng": {"lat": 9.5997, "lng": 105.9795},
            "Bạc Liêu": {"lat": 9.2941, "lng": 105.7210},
            "Cà Mau": {"lat": 8.9720, "lng": 104.7519},
            "Long An": {"lat": 10.5335, "lng": 106.4194},
            "Tiền Giang": {"lat": 10.3674, "lng": 106.3585},
            "Bến Tre": {"lat": 10.2376, "lng": 106.3735},
            "Trà Vinh": {"lat": 9.9415, "lng": 106.3435},
            "Đồng Tháp": {"lat": 10.5046, "lng": 105.6318},
            "Kon Tum": {"lat": 14.3569, "lng": 108.0097},
            "Gia Lai": {"lat": 13.9833, "lng": 108.0167},
            "Đắk Lắk": {"lat": 12.6667, "lng": 108.0333},
            "Đắk Nông": {"lat": 12.1464, "lng": 107.8000},
            "Bình Phước": {"lat": 11.9150, "lng": 106.8500},
            "Tây Ninh": {"lat": 11.3100, "lng": 106.1000},
            "Lào Cai": {"lat": 22.3393, "lng": 104.9281},
        }

        result = []
        for row in rows:
            location_name = row["location_name"]

            # Lấy tọa độ từ mapping
            if location_name not in LOCATION_COORDS:
                continue

            coords = LOCATION_COORDS[location_name]

            # Parse article titles (được join bằng |||)
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
# ENDPOINTS CŨ (giữ nguyên)
# ============================================================


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
            json={"question": question, "context": serialize_rows(rows)},
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
