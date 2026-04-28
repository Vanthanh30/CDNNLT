from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src import database

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả các web gọi (hoặc thay bằng ["http://localhost:5174"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo bảng khi service bắt đầu chạy (Dành cho lần đầu deploy Docker)
@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/api/dashboard")
def read_dashboard():
    # Lấy tất cả tin đã xử lý sạch sẽ cho Dashboard
    return database.get_all_processed_articles()

@app.get("/articles")
def get_articles():
    return database.get_all_processed_articles()

@app.get("/search")
def search(q: str):
    conn = database.get_connection()
    if not conn: return {"error": "DB connection failed"}
    
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM articles WHERE title LIKE %s OR keywords LIKE %s ORDER BY created_at DESC"
    cursor.execute(query, (f"%{q}%", f"%{q}%"))
    results = cursor.fetchall()
    conn.close()
    return results

@app.get("/trend")
def trend(keyword: str):
    conn = database.get_connection()
    if not conn: return {"error": "DB connection failed"}
    
    cursor = conn.cursor()
    # MySQL dùng hàm DATE() tương tự SQLite để nhóm theo ngày
    query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM articles
        WHERE keywords LIKE %s
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    """
    cursor.execute(query, (f"%{keyword}%",))
    results = cursor.fetchall()
    conn.close()
    return results

@app.get("/api/articles/filter")
def filter_articles(
    keyword: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = "all",
    limit: int = 50
):
    return database.filter_articles(
        keyword=keyword,
        from_date=from_date,
        to_date=to_date,
        status=status,
        limit=limit
    )