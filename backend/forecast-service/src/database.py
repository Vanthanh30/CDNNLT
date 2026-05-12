import time
from datetime import date, timedelta

import mysql.connector
import pandas as pd
from mysql.connector import Error

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


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
        except Error as exc:
            print(f"DB connection retry {attempt + 1}/{retries}: {exc}")
            time.sleep(delay)
    return None


def init_db():
    conn = get_connection()
    if not conn:
        raise RuntimeError("Cannot connect to MySQL")
    conn.close()


def fetch_daily_cases(
    disease_name: str | None = None,
    location: str | None = None,
    history_days: int = 180,
) -> pd.DataFrame:
    conn = get_connection()
    if not conn:
        return pd.DataFrame(columns=["event_date", "cases_infected", "event_count"])

    start_date = date.today() - timedelta(days=history_days)
    query = """
        SELECT
            de.event_date AS event_date,
            SUM(COALESCE(s.cases_infected, 0)) AS cases_infected,
            COUNT(*) AS event_count
        FROM DISEASE_EVENT de
        JOIN STATIC s ON s.event_id = de.id
        LEFT JOIN DISEASE d ON d.id = de.disease_id
        LEFT JOIN REGION r ON r.id = de.region_id
        WHERE de.event_date IS NOT NULL
          AND de.event_date >= %s
    """
    params: list[object] = [start_date]

    if disease_name:
        query += " AND d.name = %s"
        params.append(disease_name)
    if location:
        query += " AND r.name = %s"
        params.append(location)

    query += " GROUP BY de.event_date ORDER BY de.event_date ASC"

    try:
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(columns=["event_date", "cases_infected", "event_count"])

    df["event_date"] = pd.to_datetime(df["event_date"]).dt.date
    df["cases_infected"] = pd.to_numeric(df["cases_infected"], errors="coerce").fillna(0)
    df["event_count"] = pd.to_numeric(df["event_count"], errors="coerce").fillna(0)
    return df


def fetch_active_diseases(history_days: int = 180, limit: int = 20) -> list[dict]:
    conn = get_connection()
    if not conn:
        return []

    start_date = date.today() - timedelta(days=history_days)
    query = """
        SELECT
            d.name AS disease_name,
            COUNT(de.id) AS event_count,
            SUM(COALESCE(s.cases_infected, 0)) AS total_cases,
            MAX(de.event_date) AS last_event_date
        FROM DISEASE_EVENT de
        JOIN DISEASE d ON d.id = de.disease_id
        LEFT JOIN STATIC s ON s.event_id = de.id
        WHERE de.event_date IS NOT NULL
          AND de.event_date >= %s
          AND d.name IS NOT NULL
          AND d.name <> ''
        GROUP BY d.name
        ORDER BY last_event_date DESC, total_cases DESC
        LIMIT %s
    """

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, (start_date, int(limit)))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    for row in rows:
        if row.get("last_event_date"):
            row["last_event_date"] = row["last_event_date"].isoformat()
        row["event_count"] = int(row.get("event_count") or 0)
        row["total_cases"] = int(row.get("total_cases") or 0)
    return rows


def fetch_disease_regions(
    disease_name: str,
    history_days: int = 180,
    limit: int = 5,
) -> list[dict]:
    conn = get_connection()
    if not conn:
        return []

    start_date = date.today() - timedelta(days=history_days)
    query = """
        SELECT
            r.name AS region_name,
            COUNT(de.id) AS event_count,
            SUM(COALESCE(s.cases_infected, 0)) AS total_cases,
            MAX(de.event_date) AS last_event_date
        FROM DISEASE_EVENT de
        JOIN DISEASE d ON d.id = de.disease_id
        JOIN REGION r ON r.id = de.region_id
        LEFT JOIN STATIC s ON s.event_id = de.id
        WHERE de.event_date IS NOT NULL
          AND de.event_date >= %s
          AND d.name = %s
          AND r.name IS NOT NULL
          AND r.name <> ''
        GROUP BY r.name
        ORDER BY last_event_date DESC, total_cases DESC
        LIMIT %s
    """

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, (start_date, disease_name, int(limit)))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    for row in rows:
        if row.get("last_event_date"):
            row["last_event_date"] = row["last_event_date"].isoformat()
        row["event_count"] = int(row.get("event_count") or 0)
        row["total_cases"] = int(row.get("total_cases") or 0)
    return rows
