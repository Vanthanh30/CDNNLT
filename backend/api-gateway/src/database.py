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
                host="db",
                user="root",
                password="password",
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