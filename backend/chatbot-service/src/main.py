from typing import Optional, List, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.ai_service import generate_answer

app = FastAPI(title="Chatbot Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    context: Optional[List[Dict[str, Any]]] = []


@app.get("/")
def root():
    return {"message": "Chatbot running"}


@app.post("/chat")
def chat(req: ChatRequest):
    return {"answer": generate_answer(question=req.question, rows=req.context or [])}
