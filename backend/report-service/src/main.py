from pathlib import Path
from dotenv import load_dotenv

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from database import init_db
from report_generator import generate_monthly_report

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/report/monthly/download")
def download_monthly():
    result = generate_monthly_report()
    if not result:
        return {"message": "No data available"}
    pdf_buffer, filename = result
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/report/weekly/download")
def download_weekly():
    return download_monthly()
