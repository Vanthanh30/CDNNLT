"""
main.py (processor-service) — Xử lý bài báo thô → lưu vào DB theo ERD
Pipeline: RAW_ARTICLE → ARTICLE + DISEASE_EVENT + STATIC

THAY ĐỔI SO VỚI PHIÊN BẢN CŨ:
- Bắt buộc disease_valid = True trước khi lưu (không lưu bệnh "Không xác định")
- Bắt buộc location_valid = True trước khi lưu (không lưu region rác)
- Các bài không extract được vẫn được lưu vào ARTICLE nhưng KHÔNG tạo DISEASE_EVENT/STATIC
  → Tránh mất bài nhưng cũng không sinh rác vào DB
"""

import time
import re
from datetime import datetime

from nlp_engine import extract_info, is_valid_disease, is_valid_location
from database import (
    get_unprocessed_articles,
    save_processed_article,
    save_article_only,          # ← hàm mới, xem database.py
    init_db,
)


# ========================
# TEXT CLEANING
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
# PROCESS LOOP
# ========================

def process_batch(limit: int = 20):
    articles = get_unprocessed_articles(limit=limit)

    if not articles:
        print("😴 Không có bài chưa xử lý.")
        return 0

    print(f"\n📋 Xử lý {len(articles)} bài...")
    success = 0
    partial = 0   # lưu ARTICLE nhưng không có event (thiếu disease/location)
    failed  = 0

    for art in articles:
        title   = art.get("title", "") or ""
        content = art.get("content", "") or ""
        raw_id  = art["id"]

        print(f"\n🧠 [{raw_id[:8]}...] {title[:70]}")

        try:
            result = extract_info(title=title, content=content)

            print(f"  🦠 Bệnh    : {result['disease_name']} ({'✅' if result['disease_valid'] else '❌'})")
            print(f"  📍 Địa điểm: {result['location']} ({'✅' if result['location_valid'] else '❌'})")
            print(f"  👥 Nhóm    : {result['group']}")
            print(f"  ⚠️  Rủi ro  : {result['risk_level']}")
            print(f"  🤒 Nhiễm   : {result['cases']} | Chết: {result['cases_dead']} | Khỏi: {result['cases_recovered']}")

            content_clean = clean_content(content)
            summary       = make_summary(title, content_clean)
            event_date    = parse_event_date(art.get("published_at"))

            # ── GUARD: chỉ lưu đầy đủ khi cả disease VÀ location hợp lệ ──
            if not result["disease_valid"] or not result["location_valid"]:
                reason = []
                if not result["disease_valid"]:
                    reason.append(f"bệnh không xác định ('{result['disease_name']}')")
                if not result["location_valid"]:
                    reason.append(f"địa điểm không hợp lệ ('{result['location']}')")
                print(f"  ⚠️  Bỏ qua tạo DISEASE_EVENT: {', '.join(reason)}")

                # Vẫn lưu ARTICLE để không mất bài, nhưng không tạo event
                ok = save_article_only(
                    raw_article_id=raw_id,
                    summary=summary,
                    content_clean=content_clean,
                )
                if ok:
                    partial += 1
                    print("  ℹ️  Lưu ARTICLE-only (không có event)")
                else:
                    failed += 1
                continue

            # ── Lưu đầy đủ tất cả địa điểm tìm được ──
            locations = result.get("all_locations") or [result["location"]]
            # Lọc lại, chỉ giữ location hợp lệ
            locations = [loc for loc in locations if is_valid_location(loc)]
            if not locations:
                locations = [result["location"]]

            ok = save_processed_article(
                raw_article_id  = raw_id,
                summary         = summary,
                content_clean   = content_clean,
                disease_name    = result["disease_name"],
                location        = locations[0],
                event_date      = event_date,
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

        except Exception as e:
            print(f"  ❌ Lỗi xử lý: {e}")
            failed += 1

    print(f"\n📊 Kết quả batch: ✅ {success} đầy đủ | ℹ️  {partial} article-only | ❌ {failed} lỗi")
    return success + partial


# ========================
# RUN SERVICE
# ========================

if __name__ == "__main__":
    print("🚀 Processor Service khởi động...")
    init_db()

    BATCH_SIZE = 20
    SLEEP_SECS = 10

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⚙️  [{now}] Bắt đầu xử lý batch...")

        processed = process_batch(limit=BATCH_SIZE)

        if processed == 0:
            time.sleep(60)
        else:
            time.sleep(SLEEP_SECS)