import time
import uuid
import hashlib
import mysql.connector
from mysql.connector import Error


DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"
DB_PASSWORD = ""
DB_NAME     = "disease_management"


def generate_id():
    return str(uuid.uuid4())


def generate_hash(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_connection(retries=5, delay=2):
    for attempt in range(retries):
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4"
            )
        except Error as e:
            print(f"⚠️ Không kết nối được MySQL. Thử lại {attempt + 1}/{retries}: {e}")
            time.sleep(delay)

    print("❌ Không thể kết nối MySQL")
    return None


def init_db():
    """
    DB đã tạo sẵn bằng XAMPP/phpMyAdmin.
    Hàm này chỉ kiểm tra kết nối.
    """
    conn = get_connection()
    if conn:
        conn.close()
        print("✅ Kết nối database disease_management thành công")


# =========================
# CRAWLER SERVICE
# =========================

def get_or_create_source(name="Unknown", source_type="News Website"):
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM SOURCE WHERE name = %s LIMIT 1", (name,))
    row = cursor.fetchone()

    if row:
        cursor.close()
        conn.close()
        return row["id"]

    source_id = generate_id()

    cursor.execute(
        "INSERT INTO SOURCE (id, name, type) VALUES (%s, %s, %s)",
        (source_id, name, source_type)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return source_id


def save_raw_article(title, link, content, source_name="Unknown", published_at=None):
    """
    Lưu bài báo thô vào bảng RAW_ARTICLE.
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        source_id = get_or_create_source(source_name, "News Website")
        raw_id = generate_id()
        content_hash = generate_hash(link + (content or ""))

        query = """
            INSERT INTO RAW_ARTICLE
            (id, source_id, url, title, content, published_at, crawled_at, hash)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
        """

        cursor.execute(
            query,
            (
                raw_id,
                source_id,
                link,
                title,
                content,
                published_at,
                content_hash
            )
        )

        conn.commit()
        print(f"✅ Đã lưu RAW_ARTICLE: {title[:50]}...")
        return True

    except Error as e:
        if "Duplicate entry" in str(e):
            print("⚠️ Bài đã tồn tại, bỏ qua.")
        else:
            print(f"❌ Lỗi lưu RAW_ARTICLE: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


# =========================
# PROCESSOR SERVICE
# =========================

def get_unprocessed_articles(limit=10):
    """
    Lấy bài RAW_ARTICLE chưa được xử lý sang ARTICLE.
    """
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            r.id,
            r.title,
            r.content,
            r.url,
            r.published_at
        FROM RAW_ARTICLE r
        LEFT JOIN ARTICLE a ON a.raw_article_id = r.id
        WHERE a.id IS NULL
        ORDER BY r.crawled_at ASC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def get_or_create_disease(name):
    if not name:
        name = "Không xác định"

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM DISEASE WHERE name = %s LIMIT 1", (name,))
    row = cursor.fetchone()

    if row:
        cursor.close()
        conn.close()
        return row["id"]

    disease_id = generate_id()

    cursor.execute(
        "INSERT INTO DISEASE (id, name) VALUES (%s, %s)",
        (disease_id, name)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return disease_id


def get_or_create_region(name):
    if not name:
        name = "Không xác định"

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM REGION WHERE name = %s LIMIT 1", (name,))
    row = cursor.fetchone()

    if row:
        cursor.close()
        conn.close()
        return row["id"]

    region_id = generate_id()

    cursor.execute(
        "INSERT INTO REGION (id, name) VALUES (%s, %s)",
        (region_id, name)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return region_id


def save_processed_article(
    raw_article_id,
    summary,
    content_clean,
    disease_name,
    location,
    event_date=None,
    risk_level="LOW",
    cases_infected=0,
    cases_dead=0,
    cases_recovered=0
):
    """
    Lưu dữ liệu sau xử lý:
    RAW_ARTICLE -> ARTICLE
    DISEASE
    REGION
    DISEASE_EVENT
    STATIC
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        article_id = generate_id()
        disease_id = get_or_create_disease(disease_name)
        region_id = get_or_create_region(location)
        event_id = generate_id()
        static_id = generate_id()

        cursor.execute(
            """
            INSERT INTO ARTICLE
            (id, raw_article_id, summary, content_clean, processed_at)
            VALUES (%s, %s, %s, %s, CURDATE())
            """,
            (
                article_id,
                raw_article_id,
                summary,
                content_clean
            )
        )

        cursor.execute(
            """
            INSERT INTO DISEASE_EVENT
            (id, article_id, region_id, disease_id, event_date, risk_level)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                event_id,
                article_id,
                region_id,
                disease_id,
                event_date,
                risk_level
            )
        )

        cursor.execute(
            """
            INSERT INTO STATIC
            (id, event_id, region_id, cases_infected, cases_dead, cases_recovered)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                static_id,
                event_id,
                region_id,
                cases_infected,
                cases_dead,
                cases_recovered
            )
        )

        conn.commit()
        print("✅ Đã lưu ARTICLE + DISEASE_EVENT + STATIC")
        return True

    except Error as e:
        conn.rollback()
        print(f"❌ Lỗi xử lý article: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


# =========================
# API GATEWAY
# =========================

def get_all_processed_articles(limit=100):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            a.id AS article_id,
            r.title,
            r.url,
            r.content AS raw_content,
            a.summary,
            a.content_clean,
            d.name AS disease_name,
            rg.name AS location,
            de.event_date,
            de.risk_level,
            s.cases_infected,
            s.cases_dead,
            s.cases_recovered,
            a.processed_at
        FROM ARTICLE a
        JOIN RAW_ARTICLE r ON a.raw_article_id = r.id
        LEFT JOIN DISEASE_EVENT de ON de.article_id = a.id
        LEFT JOIN DISEASE d ON de.disease_id = d.id
        LEFT JOIN REGION rg ON de.region_id = rg.id
        LEFT JOIN STATIC s ON s.event_id = de.id
        ORDER BY a.processed_at DESC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def filter_articles(
    keyword=None,
    disease_name=None,
    location=None,
    from_date=None,
    to_date=None,
    risk_level=None,
    limit=50
):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            a.id AS article_id,
            r.title,
            r.url,
            a.summary,
            a.content_clean,
            d.name AS disease_name,
            rg.name AS location,
            de.event_date,
            de.risk_level,
            s.cases_infected,
            s.cases_dead,
            s.cases_recovered,
            a.processed_at
        FROM ARTICLE a
        JOIN RAW_ARTICLE r ON a.raw_article_id = r.id
        LEFT JOIN DISEASE_EVENT de ON de.article_id = a.id
        LEFT JOIN DISEASE d ON de.disease_id = d.id
        LEFT JOIN REGION rg ON de.region_id = rg.id
        LEFT JOIN STATIC s ON s.event_id = de.id
        WHERE 1 = 1
    """

    params = []

    if keyword:
        query += """
            AND (
                r.title LIKE %s
                OR r.content LIKE %s
                OR a.summary LIKE %s
                OR a.content_clean LIKE %s
            )
        """
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword, like_keyword])

    if disease_name:
        query += " AND d.name LIKE %s"
        params.append(f"%{disease_name}%")

    if location:
        query += " AND rg.name LIKE %s"
        params.append(f"%{location}%")

    if from_date:
        query += " AND DATE(de.event_date) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(de.event_date) <= %s"
        params.append(to_date)

    if risk_level:
        query += " AND de.risk_level = %s"
        params.append(risk_level)

    query += " ORDER BY a.processed_at DESC LIMIT %s"
    params.append(int(limit))

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

def extract_keywords(question: str):
    q = question.lower()

    disease = None
    location = None

    # lấy tất cả disease trong DB
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name FROM DISEASE")
    diseases = [d["name"].lower() for d in cursor.fetchall()]

    cursor.execute("SELECT name FROM REGION")
    regions = [r["name"].lower() for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    for d in diseases:
        if d in q:
            disease = d
            break

    for r in regions:
        if r in q:
            location = r
            break

    return disease, location

def search_chatbot_context(question: str, limit: int = 5):
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    disease, location = extract_keywords(question)

    query = """
        SELECT
            r.title,
            r.url,
            a.summary,
            a.content_clean,
            d.name AS disease_name,
            rg.name AS location,
            de.event_date,
            de.risk_level,
            s.cases_infected,
            s.cases_dead,
            s.cases_recovered
        FROM ARTICLE a
        JOIN RAW_ARTICLE r ON a.raw_article_id = r.id
        LEFT JOIN DISEASE_EVENT de ON de.article_id = a.id
        LEFT JOIN DISEASE d ON de.disease_id = d.id
        LEFT JOIN REGION rg ON de.region_id = rg.id
        LEFT JOIN STATIC s ON s.event_id = de.id
        WHERE 1=1
    """

    params = []

    # lọc theo disease
    if disease:
        query += " AND d.name LIKE %s"
        params.append(f"%{disease}%")

    # lọc theo location
    if location:
        query += " AND rg.name LIKE %s"
        params.append(f"%{location}%")

    # nếu không có gì thì fallback search nhẹ
    if not disease and not location:
        like = f"%{question}%"
        query += """
            AND (
                r.title LIKE %s
                OR a.summary LIKE %s
            )
        """
        params.extend([like, like])

    query += " ORDER BY a.processed_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def generate_chatbot_answer(question: str):
    rows = search_chatbot_context(question, limit=5)

    if not rows:
        return {
            "answer": "❌ Không tìm thấy dữ liệu phù hợp.",
            "sources": []
        }

    # gom theo khu vực
    result = {}

    for row in rows:
        disease = row.get("disease_name") or "Không xác định"
        location = row.get("location") or "Không xác định"

        if disease not in result:
            result[disease] = []

        result[disease].append(location)

    answer_parts = []

    for disease, locations in result.items():
        unique_locations = list(set(locations))
        answer_parts.append(
            f"📌 Dịch bệnh '{disease}' xuất hiện tại: {', '.join(unique_locations)}"
        )

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
        "answer": "\n".join(answer_parts),
        "sources": sources
    }