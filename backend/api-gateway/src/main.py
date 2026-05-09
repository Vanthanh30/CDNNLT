from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src import database
import requests

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
        return {
            "answer": "Không tìm thấy dữ liệu phù hợp.",
            "sources": []
        }

    ai_answer = call_chatbot_service(request.question, rows)

    sources = []
    for row in rows:
        sources.append({
            "title": row.get("title"),
            "url": row.get("url"),
            "disease_name": row.get("disease_name"),
            "location": row.get("location"),
            "risk_level": row.get("risk_level")
        })

    return {
        "answer": ai_answer,
        "sources": sources
    }


def call_chatbot_service(question, rows):
    try:
        response = requests.post(
            CHATBOT_SERVICE_URL,
            json={
                "question": question,
                "context": serialize_rows(rows)  # ✅ fix
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("answer")

        return "Chatbot service lỗi."

    except Exception as e:
        print("❌ Lỗi gọi chatbot-service:", e)
        return "Không thể kết nối chatbot-service."


@app.get("/internal/search")
def search_for_chatbot(question: str):
    return database.search_chatbot_context(question, limit=20)