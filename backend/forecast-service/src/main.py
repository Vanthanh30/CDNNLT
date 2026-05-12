from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import DEFAULT_FORECAST_DAYS, DEFAULT_HISTORY_DAYS
from database import init_db
from forecast_model import get_disease_forecast_summary, get_forecast, train_forecast_model


app = FastAPI(title="Disease Forecast Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/train")
def train(
    disease_name: Optional[str] = None,
    location: Optional[str] = None,
    history_days: int = Query(DEFAULT_HISTORY_DAYS, ge=30, le=730),
):
    return train_forecast_model(
        disease_name=disease_name,
        location=location,
        history_days=history_days,
    )


@app.get("/forecast")
def forecast(
    disease_name: Optional[str] = None,
    location: Optional[str] = None,
    days: int = Query(DEFAULT_FORECAST_DAYS, ge=7, le=14),
    history_days: int = Query(DEFAULT_HISTORY_DAYS, ge=30, le=730),
):
    return get_forecast(
        disease_name=disease_name,
        location=location,
        forecast_days=days,
        history_days=history_days,
    )


@app.get("/forecast/diseases")
def disease_forecast_summary(
    location: Optional[str] = None,
    history_days: int = Query(DEFAULT_HISTORY_DAYS, ge=30, le=730),
    limit: int = Query(12, ge=1, le=50),
    top_n: int = Query(3, ge=1, le=10),
):
    return get_disease_forecast_summary(
        location=location,
        history_days=history_days,
        limit=limit,
        top_n=top_n,
    )
