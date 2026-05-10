"""
main.py (processor-service) — Xử lý bài báo thô → lưu DB
THAY ĐỔI:
- BATCH_SIZE tăng từ 20 → 50
- ThreadPoolExecutor(5) để xử lý NLP song song
  (NLP là CPU-bound nên 5 worker là hợp lý, không đặt quá cao)
- APScheduler thay while True + sleep
- Thêm log tổng số bài pending khi khởi động
"""

import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from nlp_engine import extract_info, is_valid_disease, is_valid_location
from database import (
    get_unprocessed_articles,
    save_processed_article,
    save_article_only,
    init_db,
)

BATCH_SIZE   = 50    # Tăng từ 20 lên 50
NLP_WORKERS  = 5     # Thread cho NLP (CPU-bound)
SLEEP_EMPTY  = 60    # Giây chờ khi không có bài
SLEEP_NORMAL = 5     # Giây chờ giữa các batch


# ========================
# TEXT CLEANING (giữ nguyên)
# ========================

def clean_content(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def make_summary(title: str, content: str, max_len: int = 500) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", content or "")
    snippet   = " ".join(sentences[:3])
    summary   = f"{title}. {snippet}" if title else snippet
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


# ========================
# XỬ LÝ 1 BÀI (worker)
# ========================

def _process_one(art: dict) -> dict:
    """
    Xử lý NLP cho 1 bài, trả về dict kết quả để main thread lưu DB.
    Tách phần NLP (có thể song song) khỏi phần DB (tuần tự).
    """
    title   = art.get("title", "") or ""
    content = art.get("content", "") or ""
    raw_id  = art["id"]

    try:
        result        = extract_info(title=title, content=content)
        content_clean = clean_content(content)
        summary       = make_summary(title, content_clean)
        event_date    = parse_event_date(art.get("published_at"))

        return {
            "raw_id":        raw_id,
            "title":         title,
            "summary":       summary,
            "content_clean": content_clean,
            "event_date":    event_date,
            "result":        result,
            "error":         None,
        }

    except Exception as e:
        return {
            "raw_id": raw_id,
            "title":  title,
            "error":  str(e),
        }


# ========================
# BATCH PROCESSING (song song NLP, tuần tự DB)
# ========================

def process_batch(limit: int = BATCH_SIZE) -> int:
    articles = get_unprocessed_articles(limit=limit)

    if not articles:
        print("😴 Không có bài chưa xử lý.")
        return 0

    print(f"\n📋 Xử lý {len(articles)} bài (NLP song song {NLP_WORKERS} workers)...")

    # ── Bước 1: NLP song song ──
    nlp_results = []
    with ThreadPoolExecutor(max_workers=NLP_WORKERS) as pool:
        futures = {pool.submit(_process_one, art): art for art in articles}
        for future in as_completed(futures):
            nlp_results.append(future.result())

    # Sắp xếp lại theo thứ tự gốc để log dễ đọc
    order = {art["id"]: i for i, art in enumerate(articles)}
    nlp_results.sort(key=lambda r: order.get(r["raw_id"], 999))

    # ── Bước 2: Lưu DB tuần tự (tránh deadlock) ──
    success = 0
    partial = 0
    failed  = 0

    for r in nlp_results:
        raw_id = r["raw_id"]
        title  = r.get("title", "")[:70]

        print(f"\n💾 [{raw_id[:8]}...] {title}")

        if r["error"]:
            print(f"  ❌ Lỗi NLP: {r['error']}")
            failed += 1
            continue

        result = r["result"]

        print(f"  🦠 {result['disease_name']} ({'✅' if result['disease_valid'] else '❌'})")
        print(f"  📍 {result['location']} ({'✅' if result['location_valid'] else '❌'})")
        print(f"  ⚠️  {result['risk_level']} | 🤒{result['cases']} 💀{result['cases_dead']}")

        if not result["disease_valid"] or not result["location_valid"]:
            ok = save_article_only(
                raw_article_id=raw_id,
                summary=r["summary"],
                content_clean=r["content_clean"],
            )
            if ok:
                partial += 1
                print("  ℹ️  ARTICLE-only (không có event)")
            else:
                failed += 1
            continue

        # Lưu đầy đủ
        locations = [
            loc for loc in (result.get("all_locations") or [result["location"]])
            if is_valid_location(loc)
        ] or [result["location"]]

        ok = save_processed_article(
            raw_article_id  = raw_id,
            summary         = r["summary"],
            content_clean   = r["content_clean"],
            disease_name    = result["disease_name"],
            location        = locations[0],
            event_date      = r["event_date"],
            risk_level      = result["risk_level"],
            cases_infected  = result["cases"],
            cases_dead      = result["cases_dead"],
            cases_recovered = result["cases_recovered"],
        )

        if ok:
            success += 1
            print("  ✅ Lưu thành công")
        else:
            failed += 1
            print("  ❌ Lưu thất bại")

    print(f"\n📊 Batch: ✅{success} đầy đủ | ℹ️{partial} article-only | ❌{failed} lỗi")
    return success + partial


# ========================
# ENTRY POINT
# ========================

if __name__ == "__main__":
    print("🚀 Processor Service khởi động...")
    init_db()

    # Hiển thị số bài pending
    try:
        from database import get_unprocessed_count
        pending = get_unprocessed_count()
        print(f"📥 Bài chưa xử lý: {pending}")
    except Exception:
        pass

    # Chạy ngay lần đầu
    process_batch()

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
        scheduler.add_job(process_batch, "interval", minutes=10, id="process_job")
        print("\n⏱️  Scheduler: xử lý mỗi 10 phút")
        scheduler.start()
    except ImportError:
        print("\n⚠️  APScheduler chưa cài, dùng while loop fallback")
        while True:
            processed = process_batch()
            time.sleep(SLEEP_EMPTY if processed == 0 else SLEEP_NORMAL)