from fastapi import FastAPI
from pydantic import BaseModel
from src.ai_service import generate_answer

app = FastAPI(title="Chatbot Service")


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {"message": "Chatbot running"}


@app.post("/chat")
def chat(req: ChatRequest):
    return {
        "answer": generate_answer(req.question)
    }