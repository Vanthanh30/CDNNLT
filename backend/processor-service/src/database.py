import time
import uuid
import hashlib
import mysql.connector
from mysql.connector import Error
from datetime import date, datetime
from mysql.connector import Error
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "disease_management")


def _get_valid_sets():
    from nlp_engine import VALID_LOCATIONS, VALID_DISEASES

    return VALID_LOCATIONS, VALID_DISEASES


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
            print(f"Thử lại kết nối {attempt + 1}/{retries}: {e}")
            time.sleep(delay)
    print("Không thể kết nối MySQL")
    return None


def init_db():
    conn = get_connection()
    if conn:
        conn.close()
        print("Kết nối database disease_management thành công")
    else:
        raise RuntimeError("Không kết nối được MySQL!")


_DB_DATE_MIN = datetime(2016, 1, 1)


def _is_date_valid_for_db(dt: datetime) -> bool:
    """
    Trả về True nếu ngày hợp lệ:
      - >= 2016-01-01           (chặn epoch 1970, bài cổ vô nghĩa)
      - <= now + 1 ngày         (chặn ngày tương lai do lỗi timezone)
    KHÔNG giới hạn 30 ngày nữa — cào toàn bộ 10 năm để lọc.
    """
    from datetime import timedelta

    now = datetime.now()
    if dt < _DB_DATE_MIN:
        return False
    if dt > now + timedelta(days=1):
        return False
    return True


def _normalize_published_at(published_at) -> str | None:
    """
    Chuẩn hóa published_at về dạng 'YYYY-MM-DD HH:MM:SS' mà MySQL datetime chấp nhận.
    Còn validate khoảng ngày: loại bỏ 1970, quá cũ, tương lai → lưu NULL.
    Trả về None nếu không parse được hoặc ngoài khoảng — DB lưu NULL, crawled_at vẫn có.

    Nhận vào:
      - None / ""                         → None
      - datetime object                   → format trực tiếp
      - date object                       → thêm 00:00:00
      - str 'YYYY-MM-DD HH:MM:SS'         → giữ nguyên
      - str 'YYYY-MM-DD'                  → thêm 00:00:00
      - str ISO 8601 với timezone         → strip timezone, format lại
      - str RFC 2822                      → parse rồi format
    """
    if published_at is None or published_at == "":
        return None

    if isinstance(published_at, datetime):
        if not _is_date_valid_for_db(published_at):
            print(f"  published_at ngoài khoảng hợp lệ: {published_at} → lưu NULL")
            return None
        return published_at.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(published_at, date):
        dt = datetime(published_at.year, published_at.month, published_at.day)
        if not _is_date_valid_for_db(dt):
            print(f"  published_at ngoài khoảng hợp lệ: {published_at} → lưu NULL")
            return None
        return published_at.strftime("%Y-%m-%d") + " 00:00:00"

    if isinstance(published_at, str):
        raw = published_at.strip()
        if not raw:
            return None
        import re

        if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", raw):
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
                if not _is_date_valid_for_db(dt):
                    print(f"  ⚠️  published_at ngoài khoảng: {raw} → lưu NULL")
                    return None
                return raw
            except Exception:
                return None
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            dt = dt.replace(tzinfo=None)
            if not _is_date_valid_for_db(dt):
                print(f"  ⚠️  published_at ngoài khoảng: {raw} → lưu NULL")
                return None
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(raw).replace(tzinfo=None)
            if not _is_date_valid_for_db(dt):
                print(f"  published_at ngoài khoảng: {raw} → lưu NULL")
                return None
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        m = re.match(r"^(\d{4}-\d{2}-\d{2})$", raw)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                if not _is_date_valid_for_db(dt):
                    print(f"  published_at ngoài khoảng: {raw} → lưu NULL")
                    return None
                return m.group(1) + " 00:00:00"
            except Exception:
                pass

        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", raw)
        if m:
            try:
                dt = datetime.strptime(
                    f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "%Y-%m-%d"
                )
                if not _is_date_valid_for_db(dt):
                    print(f"  published_at ngoài khoảng: {raw} → lưu NULL")
                    return None
                return f"{m.group(3)}-{m.group(2)}-{m.group(1)} 00:00:00"
            except Exception:
                pass

        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})$", raw)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
                if not _is_date_valid_for_db(dt):
                    print(f"  published_at ngoài khoảng: {raw} → lưu NULL")
                    return None
                return m.group(1) + ":00"
            except Exception:
                pass

        print(f"  Không parse được published_at: '{raw}' → lưu NULL")
        return None

    print(f"  published_at kiểu không hợp lệ: {type(published_at)} → lưu NULL")
    return None


def get_or_create_source(
    name: str = "Unknown", source_type: str = "News Website"
) -> str | None:
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
    """
    Lưu RAW_ARTICLE.
    published_at được chuẩn hóa qua _normalize_published_at() trước khi lưu.
    Nếu không parse được → lưu NULL (không crash).
    Duplicate URL → trả về False (không phải lỗi).
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        source_id = get_or_create_source(source_name, "News Website")
        raw_id = generate_id()
        content_hash = generate_hash(link + (content or ""))
        pub_at_val = _normalize_published_at(published_at)

        cursor.execute(
            """
            INSERT INTO RAW_ARTICLE
                (id, source_id, url, title, content, published_at, crawled_at, hash)
            VALUES
                (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (raw_id, source_id, link, title, content, pub_at_val, content_hash),
        )
        conn.commit()

        date_info = f"published_at={pub_at_val}" if pub_at_val else "published_at=NULL"
        print(f"  RAW_ARTICLE [{date_info}]: {(title or '')[:60]}...")
        return True

    except Error as e:
        if "Duplicate entry" in str(e):
            print("  Bài đã tồn tại, bỏ qua.")
        else:
            print(f"  Lỗi lưu RAW_ARTICLE: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def delete_raw_article(raw_article_id: str) -> bool:
    """
    Xóa RAW_ARTICLE không liên quan dịch bệnh để processor không xử lý lặp lại.
    Chỉ dùng khi bài đã bị bộ lọc AI xác nhận là không phù hợp.
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM RAW_ARTICLE WHERE id = %s", (raw_article_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        conn.rollback()
        print(f"delete_raw_article: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


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
    """
    name = (name or "").strip()

    if not name or name == "Không xác định":
        print(f"  Từ chối lưu disease rỗng/không xác định")
        return None

    try:
        valid_locations, valid_diseases = _get_valid_sets()
        if name not in valid_diseases:
            print(f"  Từ chối lưu disease không hợp lệ: '{name}'")
            return None
    except Exception:
        pass

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
        print(f"get_or_create_disease: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def get_or_create_region(name: str) -> str | None:
    """
    Chỉ INSERT nếu name có trong VALID_LOCATIONS (63 tỉnh/thành).
    """
    name = (name or "").strip()

    if not name or name == "Không xác định":
        print(f"  Từ chối lưu region rỗng/không xác định")
        return None

    try:
        valid_locations, valid_diseases = _get_valid_sets()
        if name not in valid_locations:
            print(f"  Từ chối lưu region không hợp lệ: '{name}'")
            return None
    except Exception:
        pass

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
        print(f"get_or_create_region: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def save_article_only(
    raw_article_id: str,
    summary: str,
    content_clean: str,
) -> bool:
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
        print(f"save_article_only: {e}")
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
    disease_id = get_or_create_disease(disease_name)
    region_id = get_or_create_region(location)

    if not disease_id:
        print(f"  Không lưu: disease_id = None ('{disease_name}')")
        return False
    if not region_id:
        print(f"  Không lưu: region_id = None ('{location}')")
        return False

    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        article_id = generate_id()
        event_id = generate_id()
        static_id = generate_id()

        cursor.execute(
            """
            INSERT INTO ARTICLE
                (id, raw_article_id, summary, content_clean, processed_at)
            VALUES
                (%s, %s, %s, %s, CURDATE())
            """,
            (article_id, raw_article_id, summary, content_clean),
        )

        cursor.execute(
            """
            INSERT INTO DISEASE_EVENT
                (id, article_id, region_id, disease_id, event_date, risk_level)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (event_id, article_id, region_id, disease_id, event_date, risk_level),
        )

        cursor.execute(
            """
            INSERT INTO STATIC
                (id, event_id, region_id, cases_infected, cases_dead, cases_recovered)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (
                static_id,
                event_id,
                region_id,
                cases_infected,
                cases_dead,
                cases_recovered,
            ),
        )

        conn.commit()
        return True

    except Error as e:
        conn.rollback()
        print(f"save_processed_article: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


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
                r.published_at,
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
    keyword: str = None,
    disease_name: str = None,
    location: str = None,
    from_date: str = None,
    to_date: str = None,
    risk_level: str = None,
    limit: int = 50,
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
            r.published_at,
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
