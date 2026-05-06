from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from database import init_db
from report_generator import generate_weekly_report


app = FastAPI(title="Report Service")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "Report Service running"}


# 🔥 API FE gọi
@app.get("/api/report/weekly/download")
def download_weekly_report():
    result = generate_weekly_report()

    if not result:
        return {"message": "Không có dữ liệu"}

    pdf_path, filename = result

    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf"
    )