import mysql.connector
from mysql.connector import Error
import time

def get_connection(retries=5, delay=2):
    """
    Tạo kết nối tới MySQL container.
    Có cơ chế tự động thử lại (Retry) nếu Database chưa khởi động xong.
    """
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="disease_db"
            )
            return conn
        except Error as e:
            print(f"⚠️ [Cảnh báo] Database chưa sẵn sàng. Thử lại sau {delay}s... ({attempt + 1}/{retries})")
            time.sleep(delay)
            
    print("❌ Lỗi nghiêm trọng: Không thể kết nối Database sau nhiều lần thử!")
    return None

def init_db():
    """Khởi tạo bảng articles (Chạy 1 lần ở API service hoặc script khởi tạo)"""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            title TEXT,
            link VARCHAR(255) UNIQUE,
            content LONGTEXT,
            keywords TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()
        print("✅ Đã khởi tạo cấu trúc bảng MySQL")

# --- Dành cho CRAWLER SERVICE ---
def save_raw_article(title, link, content):
    """Lưu tin thô, chưa có keywords"""
    conn = get_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = "INSERT INTO articles (title, link, content) VALUES (%s, %s, %s)"
        cursor.execute(query, (title, link, content))
        conn.commit()
        print(f"✅ Đã cào: {title[:30]}...")
    except Error:
        print("⚠️ Tin đã tồn tại, bỏ qua.")
    finally:
        conn.close()

# --- Dành cho PROCESSOR SERVICE ---
def get_unprocessed_articles(limit=10):
    """Lấy danh sách tin chưa được phân tích keywords"""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title, content FROM articles WHERE keywords IS NULL LIMIT %s", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_keywords(article_id, keywords_list):
    """Cập nhật keywords sau khi AI phân tích xong"""
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    kw_str = ",".join(keywords_list)
    cursor.execute("UPDATE articles SET keywords = %s WHERE id = %s", (kw_str, article_id))
    conn.commit()
    conn.close()

# --- Dành cho API GATEWAY ---
def get_all_processed_articles():
    """Lấy data sạch để hiển thị lên Dashboard"""
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE keywords IS NOT NULL ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def filter_articles(keyword=None, from_date=None, to_date=None, status=None, limit=50):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE %s OR content LIKE %s OR keywords LIKE %s)"
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword])

    if from_date:
        query += " AND DATE(created_at) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(created_at) <= %s"
        params.append(to_date)

    if status == "processed":
        query += " AND keywords IS NOT NULL"
    elif status == "unprocessed":
        query += " AND keywords IS NULL"

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(int(limit))

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    conn.close()
    return rows