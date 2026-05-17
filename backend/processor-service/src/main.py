"""
main.py (processor-service) — Xử lý bài báo thô → lưu DB
THAY ĐỔI:
- BATCH_SIZE tăng từ 20 → 50
- ThreadPoolExecutor(5) để xử lý NLP song song
- APScheduler thay while True + sleep
- Thêm log tổng số bài pending khi khởi động
"""

import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_filter import classify_article
from nlp_engine import extract_info, is_valid_location
from database import (
    get_unprocessed_articles,
    save_processed_article,
    save_article_only,
    delete_raw_article,
    init_db,
)

BATCH_SIZE = 50
NLP_WORKERS = 5
SLEEP_EMPTY = 60
SLEEP_NORMAL = 5


def clean_content(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()


def make_summary(title: str, content: str, max_len: int = 500) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", content or "")
    snippet = " ".join(sentences[:3])

    summary = f"{title}. {snippet}" if title else snippet

    if len(summary) > max_len:
        summary = summary[:max_len].rsplit(" ", 1)[0] + "..."

    return summary.strip()


def parse_event_date(published_at) -> str | None:
    if not published_at:
        return datetime.now().strftime("%Y-%m-%d")

    if isinstance(published_at, datetime):
        return published_at.strftime("%Y-%m-%d")

    if isinstance(published_at, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(published_at, fmt).strftime("%Y-%m-%d")

            except ValueError:
                continue

    return datetime.now().strftime("%Y-%m-%d")


def _process_one(art: dict) -> dict:
    """
    Xử lý NLP cho 1 bài.
    """

    title = art.get("title", "") or ""
    content = art.get("content", "") or ""
    raw_id = art["id"]

    try:
        result = extract_info(title=title, content=content)

        content_clean = clean_content(content)

        summary = make_summary(title, content_clean)

        event_date = parse_event_date(art.get("published_at"))

        return {
            "raw_id": raw_id,
            "title": title,
            "summary": summary,
            "content_clean": content_clean,
            "event_date": event_date,
            "result": result,
            "error": None,
        }

    except Exception as e:
        return {
            "raw_id": raw_id,
            "title": title,
            "error": str(e),
        }


def process_batch(limit: int = BATCH_SIZE) -> int:

    articles = get_unprocessed_articles(limit=limit)

    if not articles:
        print("Không có bài chưa xử lý.")
        return 0

    print(f"\nXử lý {len(articles)} bài (NLP song song {NLP_WORKERS} workers)...")

    nlp_results = []

    with ThreadPoolExecutor(max_workers=NLP_WORKERS) as pool:
        futures = {pool.submit(_process_one, art): art for art in articles}

        for future in as_completed(futures):
            nlp_results.append(future.result())

    order = {art["id"]: i for i, art in enumerate(articles)}

    nlp_results.sort(key=lambda r: order.get(r["raw_id"], 999))
    success = 0
    partial = 0
    rejected = 0
    failed = 0

    for r in nlp_results:
        raw_id = r["raw_id"]
        title = r.get("title", "")

        print(f"\n[{raw_id[:8]}...] {title[:70]}")

        if r.get("error"):
            print(f"  NLP Error: {r['error']}")
            failed += 1
            continue

        try:
            ai_result = classify_article(title, r["content_clean"])

            if not ai_result["is_relevant"]:
                print(
                    "  AI loại bài không liên quan dịch bệnh: "
                    f"{ai_result.get('method', 'unknown')} | "
                    f"{ai_result.get('reason', 'không phù hợp')} "
                    f"(confidence={ai_result.get('confidence', 0):.2f})"
                )

                if delete_raw_article(raw_id):
                    rejected += 1
                    print("  Đã xóa RAW_ARTICLE khỏi hàng đợi")

                else:
                    failed += 1
                    print("  Không xóa được RAW_ARTICLE")

                continue
            result = r["result"]

            print(
                f"  Bệnh    : {result['disease_name']} "
                f"({'' if result['disease_valid'] else ''})"
            )

            print(
                f"  Địa điểm: {result['location']} "
                f"({'' if result['location_valid'] else ''})"
            )

            print(f"  Nhóm    : {result['group']}")
            print(f"    Rủi ro  : {result['risk_level']}")

            print(
                f"  Nhiễm   : {result['cases']} | "
                f"Chết: {result['cases_dead']} | "
                f"Khỏi: {result['cases_recovered']}"
            )

            if not result["disease_valid"] or not result["location_valid"]:
                ok = save_article_only(
                    raw_article_id=raw_id,
                    summary=r["summary"],
                    content_clean=r["content_clean"],
                )

                if ok:
                    partial += 1
                    print("  ARTICLE-only (không có event)")

                else:
                    failed += 1
                    print("   Lưu ARTICLE-only thất bại")

                continue

            locations = [
                loc
                for loc in (result.get("all_locations") or [result["location"]])
                if is_valid_location(loc)
            ] or [result["location"]]

            ok = save_processed_article(
                raw_article_id=raw_id,
                summary=r["summary"],
                content_clean=r["content_clean"],
                disease_name=result["disease_name"],
                location=locations[0],
                event_date=r["event_date"],
                risk_level=result["risk_level"],
                cases_infected=result["cases"],
                cases_dead=result["cases_dead"],
                cases_recovered=result["cases_recovered"],
            )

            if ok:
                success += 1
                print("  Lưu thành công")

            else:
                failed += 1
                print("  Lưu thất bại")

        except Exception as e:
            print(f"  Lỗi xử lý: {e}")
            failed += 1

    print(
        f"\nKết quả batch:"
        f"\n   {success} đầy đủ"
        f"\n   {partial} article-only"
        f"\n   {rejected} bị loại"
        f"\n   {failed} lỗi"
    )

    return success + partial + rejected


if __name__ == "__main__":
    print("Processor Service khởi động...")

    init_db()

    BATCH_SIZE = 20
    SLEEP_SECS = 10

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n[{now}] Bắt đầu xử lý batch...")

        processed = process_batch(limit=BATCH_SIZE)

        if processed == 0:
            time.sleep(SLEEP_EMPTY)

        else:
            time.sleep(SLEEP_SECS)
