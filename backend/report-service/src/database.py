import uuid
import mysql.connector
from datetime import date
from config import *


# DB_HOST = "localhost"
# DB_PORT = 3306
# DB_USER = "root"
# DB_PASSWORD = ""
# DB_NAME = "disease_management"

REPORT_FOLDER = "reports"   

def generate_id():
    return str(uuid.uuid4())


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )

def init_db():
    conn = get_connection()
    if conn:
        conn.close()
        print("✅ Report service DB connected")
    else:
        raise RuntimeError("❌ Cannot connect DB")


# =========================
# GET DATA
# =========================

def get_articles_in_range(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.id AS article_id,
            r.title,
            a.summary,
            d.name AS disease,
            rg.name AS location,
            de.risk_level,
            s.cases_infected,
            s.cases_dead,
            s.cases_recovered,
            COALESCE(de.event_date, DATE(r.published_at)) AS report_date
        FROM ARTICLE a
        JOIN RAW_ARTICLE r ON r.id = a.raw_article_id
        JOIN DISEASE_EVENT de ON de.article_id = a.id
        LEFT JOIN DISEASE d ON d.id = de.disease_id
        LEFT JOIN REGION rg ON rg.id = de.region_id
        LEFT JOIN STATIC s ON s.event_id = de.id
        WHERE DATE(COALESCE(de.event_date, r.published_at)) BETWEEN %s AND %s
        ORDER BY report_date DESC
    """, (start_date, end_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# =========================
# SAVE REPORT
# =========================

def save_weekly_report(start_date, end_date, summary_text, total_articles, pdf_url, article_ids):
    conn = get_connection()
    cursor = conn.cursor()

    report_id = generate_id()

    cursor.execute("""
        INSERT INTO WEEKLY_REPORT
        (id, week_start, week_end, summary_text, total_articles, pdf_url)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (report_id, start_date, end_date, summary_text, total_articles, pdf_url))

    for aid in article_ids:
        cursor.execute("""
            INSERT INTO WEEKLY_REPORT_ARTICLE (report_id, article_id)
            VALUES (%s, %s)
        """, (report_id, aid))

    conn.commit()
    cursor.close()
    conn.close()

    return report_id
