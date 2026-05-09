"""
database.py - Dùng chung cho crawler-service và processor-service
Quản lý kết nối MySQL và các thao tác CRUD theo ERD disease_management

THAY ĐỔI SO VỚI PHIÊN BẢN CŨ:
- Thêm save_article_only(): lưu ARTICLE mà không tạo DISEASE_EVENT/STATIC
  (dùng khi NLP không tìm được disease/location hợp lệ)
- get_or_create_disease/region: thêm validation trước khi INSERT
- save_processed_article: thêm guard check disease/location hợp lệ
"""

import time
import uuid
import hashlib
import mysql.connector
from mysql.connector import Error


# ========================
# CONFIG
# ========================
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"
DB_PASSWORD = "123456"
DB_NAME     = "disease_management"

# ── Import VALID sets từ nlp_engine để validate trước khi lưu DB ──
# Lazy import để tránh circular dependency
def _get_valid_sets():
    from nlp_engine import VALID_LOCATIONS, VALID_DISEASES
    return VALID_LOCATIONS, VALID_DISEASES


# ========================
# HELPERS
# ========================

def generate_id() -> str:
    return str(uuid.uuid4())


def generate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_connection(retries: int = 5, delay: int = 2):
    for attempt in range(retries):
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4",
                use_unicode=True,
            )
        except Error as e:
            print(f"⚠️  Thử lại kết nối {attempt + 1}/{retries}: {e}")
            time.sleep(delay)
    print("❌ Không thể kết nối MySQL")
    return None


def init_db():
    conn = get_connection()
    if conn:
        conn.close()
        print("✅ Kết nối database disease_management thành công")
    else:
        raise RuntimeError("Không kết nối được MySQL!")


# ========================
# CRAWLER SERVICE
# ========================

def get_or_create_source(name: str = "Unknown", source_type: str = "News Website") -> str | None:
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM SOURCE WHERE name = %s LIMIT 1", (name,))
        row = cursor.fetchone()
        if row:
            return row["id"]

        source_id = generate_id()
        cursor.execute(
            "INSERT INTO SOURCE (id, name, type) VALUES (%s, %s, %s)",
            (source_id, name, source_type),
        )
        conn.commit()
        return source_id

    except Error as e:
        print(f"❌ get_or_create_source: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def save_raw_article(
    title: str,
    link: str,
    content: str,
    source_name: str = "Unknown",
    published_at=None,
) -> bool:
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        source_id    = get_or_create_source(source_name, "News Website")
        raw_id       = generate_id()
        content_hash = generate_hash(link + (content or ""))

        cursor.execute(
            """
            INSERT INTO RAW_ARTICLE
                (id, source_id, url, title, content, published_at, crawled_at, hash)
            VALUES
                (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (raw_id, source_id, link, title, content, published_at, content_hash),
        )
        conn.commit()
        print(f"  ✅ RAW_ARTICLE: {(title or '')[:60]}...")
        return True

    except Error as e:
        if "Duplicate entry" in str(e):
            print("  ℹ️  Bài đã tồn tại, bỏ qua.")
        else:
            print(f"  ❌ Lỗi lưu RAW_ARTICLE: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


# ========================
# PROCESSOR SERVICE
# ========================

def get_unprocessed_articles(limit: int = 20) -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT r.id, r.title, r.content, r.url, r.published_at
            FROM RAW_ARTICLE r
            LEFT JOIN ARTICLE a ON a.raw_article_id = r.id
            WHERE a.id IS NULL
            ORDER BY r.crawled_at ASC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def get_or_create_disease(name: str) -> str | None:
    """
    Chỉ INSERT nếu name có trong VALID_DISEASES.
    Từ chối lưu "Không xác định" hay tên bệnh rác.
    """
    name = (name or "").strip()

    if not name or name == "Không xác định":
        print(f"  ⚠️  Từ chối lưu disease rỗng/không xác định")
        return None

    try:
        valid_locations, valid_diseases = _get_valid_sets()
        if name not in valid_diseases:
            print(f"  ⚠️  Từ chối lưu disease không hợp lệ: '{name}'")
            return None
    except Exception:
        pass  # Nếu import lỗi, bỏ qua validate

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM DISEASE WHERE name = %s LIMIT 1", (name,))
        row = cursor.fetchone()
        if row:
            return row["id"]

        disease_id = generate_id()
        cursor.execute(
            "INSERT INTO DISEASE (id, name) VALUES (%s, %s)",
            (disease_id, name),
        )
        conn.commit()
        return disease_id

    except Error as e:
        print(f"❌ get_or_create_disease: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def get_or_create_region(name: str) -> str | None:
    """
    Chỉ INSERT nếu name có trong VALID_LOCATIONS (63 tỉnh/thành).
    Từ chối lưu "Không xác định", "Bộ Y Tế", "Trung Quốc", v.v.
    """
    name = (name or "").strip()

    if not name or name == "Không xác định":
        print(f"  ⚠️  Từ chối lưu region rỗng/không xác định")
        return None

    try:
        valid_locations, valid_diseases = _get_valid_sets()
        if name not in valid_locations:
            print(f"  ⚠️  Từ chối lưu region không hợp lệ: '{name}'")
            return None
    except Exception:
        pass  # Nếu import lỗi, bỏ qua validate

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM REGION WHERE name = %s LIMIT 1", (name,))
        row = cursor.fetchone()
        if row:
            return row["id"]

        region_id = generate_id()
        cursor.execute(
            "INSERT INTO REGION (id, name) VALUES (%s, %s)",
            (region_id, name),
        )
        conn.commit()
        return region_id

    except Error as e:
        print(f"❌ get_or_create_region: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def save_article_only(
    raw_article_id: str,
    summary: str,
    content_clean: str,
) -> bool:
    """
    Lưu ARTICLE mà không tạo DISEASE_EVENT / STATIC.
    Dùng khi NLP không extract được disease/location hợp lệ.
    Bài này sẽ được đánh dấu là đã xử lý (không bị re-process)
    nhưng không sinh dữ liệu rác vào event table.
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        article_id = generate_id()
        cursor.execute(
            """
            INSERT INTO ARTICLE
                (id, raw_article_id, summary, content_clean, processed_at)
            VALUES
                (%s, %s, %s, %s, CURDATE())
            """,
            (article_id, raw_article_id, summary, content_clean),
        )
        conn.commit()
        return True

    except Error as e:
        conn.rollback()
        print(f"❌ save_article_only: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def save_processed_article(
    raw_article_id: str,
    summary: str,
    content_clean: str,
    disease_name: str,
    location: str,
    event_date=None,
    risk_level: str = "LOW",
    cases_infected: int = 0,
    cases_dead: int = 0,
    cases_recovered: int = 0,
) -> bool:
    """
    Lưu đầy đủ: RAW_ARTICLE → ARTICLE → DISEASE_EVENT → STATIC
    Từ chối nếu disease_name hoặc location không hợp lệ.
    """
    # Guard tại database layer (backup cho guard ở processor)
    disease_id = get_or_create_disease(disease_name)
    region_id  = get_or_create_region(location)

    if not disease_id:
        print(f"  ❌ Không lưu: disease_id = None ('{disease_name}')")
        return False
    if not region_id:
        print(f"  ❌ Không lưu: region_id = None ('{location}')")
        return False

    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        article_id = generate_id()
        event_id   = generate_id()
        static_id  = generate_id()

        # ARTICLE
        cursor.execute(
            """
            INSERT INTO ARTICLE
                (id, raw_article_id, summary, content_clean, processed_at)
            VALUES
                (%s, %s, %s, %s, CURDATE())
            """,
            (article_id, raw_article_id, summary, content_clean),
        )

        # DISEASE_EVENT
        cursor.execute(
            """
            INSERT INTO DISEASE_EVENT
                (id, article_id, region_id, disease_id, event_date, risk_level)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (event_id, article_id, region_id, disease_id, event_date, risk_level),
        )

        # STATIC
        cursor.execute(
            """
            INSERT INTO STATIC
                (id, event_id, region_id, cases_infected, cases_dead, cases_recovered)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (static_id, event_id, region_id, cases_infected, cases_dead, cases_recovered),
        )

        conn.commit()
        return True

    except Error as e:
        conn.rollback()
        print(f"❌ save_processed_article: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


# ========================
# API GATEWAY
# ========================

def get_all_processed_articles(limit: int = 100) -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                a.id          AS article_id,
                r.title,
                r.url,
                r.content     AS raw_content,
                a.summary,
                a.content_clean,
                d.name        AS disease_name,
                rg.name       AS location,
                de.event_date,
                de.risk_level,
                s.cases_infected,
                s.cases_dead,
                s.cases_recovered,
                a.processed_at
            FROM ARTICLE a
            JOIN RAW_ARTICLE r        ON a.raw_article_id = r.id
            LEFT JOIN DISEASE_EVENT de ON de.article_id   = a.id
            LEFT JOIN DISEASE d        ON de.disease_id   = d.id
            LEFT JOIN REGION rg        ON de.region_id    = rg.id
            LEFT JOIN STATIC s         ON s.event_id      = de.id
            ORDER BY a.processed_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def filter_articles(
    keyword: str      = None,
    disease_name: str = None,
    location: str     = None,
    from_date: str    = None,
    to_date: str      = None,
    risk_level: str   = None,
    limit: int        = 50,
) -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            a.id          AS article_id,
            r.title,
            r.url,
            a.summary,
            a.content_clean,
            d.name        AS disease_name,
            rg.name       AS location,
            de.event_date,
            de.risk_level,
            s.cases_infected,
            s.cases_dead,
            s.cases_recovered,
            a.processed_at
        FROM ARTICLE a
        JOIN RAW_ARTICLE r        ON a.raw_article_id = r.id
        LEFT JOIN DISEASE_EVENT de ON de.article_id   = a.id
        LEFT JOIN DISEASE d        ON de.disease_id   = d.id
        LEFT JOIN REGION rg        ON de.region_id    = rg.id
        LEFT JOIN STATIC s         ON s.event_id      = de.id
        WHERE 1 = 1
    """
    params = []

    if keyword:
        query += """
            AND (r.title LIKE %s OR r.content LIKE %s
                 OR a.summary LIKE %s OR a.content_clean LIKE %s)
        """
        like = f"%{keyword}%"
        params.extend([like, like, like, like])

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

    try:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ========================
# STATS HELPERS
# ========================

def get_stats_by_disease(limit: int = 20) -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                d.name       AS disease_name,
                COUNT(de.id) AS total_events,
                SUM(s.cases_infected)  AS total_infected,
                SUM(s.cases_dead)      AS total_dead,
                SUM(s.cases_recovered) AS total_recovered
            FROM DISEASE_EVENT de
            JOIN DISEASE d ON de.disease_id = d.id
            LEFT JOIN STATIC s ON s.event_id = de.id
            GROUP BY d.id, d.name
            ORDER BY total_infected DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_stats_by_region(limit: int = 20) -> list:
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                rg.name      AS region_name,
                COUNT(de.id) AS total_events,
                SUM(s.cases_infected)  AS total_infected,
                SUM(s.cases_dead)      AS total_dead
            FROM DISEASE_EVENT de
            JOIN REGION rg ON de.region_id = rg.id
            LEFT JOIN STATIC s ON s.event_id = de.id
            GROUP BY rg.id, rg.name
            ORDER BY total_infected DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()