"""
main.py (crawler-service) — Thu thập bài báo dịch bệnh Việt Nam từ nhiều nguồn
Chạy mỗi CRAWL_INTERVAL_MIN phút (mặc định 30, cấu hình qua .env).

THAY ĐỔI:
  - Dùng get_contents_parallel() → fetch content song song (ThreadPoolExecutor)
  - published_at được lấy từ HTML (JSON-LD / meta / time tag) hoặc URL pattern
  - Tự động schedule bằng vòng lặp + sleep, có thể override qua CRAWL_INTERVAL_MIN
  - Log thêm thống kê date_found / date_missing sau mỗi chu kỳ
"""

import os
import time
from datetime import datetime

from spiders import (
    crawl_vnexpress,
    crawl_dantri,
    crawl_suckhoedoisong,
    crawl_nongnghiep,
    crawl_nguoichannuoi,
    crawl_baovethucvat,
    crawl_vnexpress_rss,
    crawl_suckhoe_rss,
    crawl_nongnghiep_rss,
    get_contents_parallel,
)
from ai_filter import classify_article, get_filter_status
from database import save_raw_article, init_db

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# ========================
# CONFIG (từ .env hoặc default)
# ========================
CRAWL_INTERVAL_MIN = int(os.getenv("CRAWL_INTERVAL_MIN", "30"))
CONTENT_WORKERS = int(
    os.getenv("CONTENT_WORKERS", "8")
)  # thread để fetch content song song
CRAWL_DAYS = int(os.getenv("CRAWL_DAYS", "30"))  # lấy bài trong N ngày gần nhất


# ========================
# KEYWORDS - 3 NHÓM
# ========================

KEYWORDS_HUMAN = [
    "dịch bệnh Việt Nam",
    "bệnh truyền nhiễm Việt Nam",
    "ổ dịch Việt Nam",
    "ca nhiễm Việt Nam",
    "bùng phát dịch Việt Nam",
    "nguy cơ dịch bệnh Việt Nam",
    "sốt xuất huyết Việt Nam",
    "tay chân miệng Việt Nam",
    "cúm Việt Nam",
    "sởi Việt Nam",
    "đậu mùa khỉ Việt Nam",
    "whitmore Việt Nam",
    "adenovirus Việt Nam",
]

KEYWORDS_ANIMAL = [
    "dịch bệnh động vật Việt Nam",
    "dịch bệnh gia súc Việt Nam",
    "dịch bệnh gia cầm Việt Nam",
    "ổ dịch động vật Việt Nam",
    "dịch tả lợn Việt Nam",
    "cúm gia cầm Việt Nam",
    "lở mồm long móng Việt Nam",
    "tai xanh Việt Nam",
    "bệnh dại Việt Nam",
    "tiêu hủy gia cầm Việt Nam",
]

KEYWORDS_PLANT = [
    "dịch bệnh cây trồng Việt Nam",
    "sâu bệnh cây trồng Việt Nam",
    "dịch hại cây trồng Việt Nam",
    "bệnh hại cây trồng Việt Nam",
    "rầy nâu lúa",
    "đạo ôn lúa",
    "bệnh lúa Việt Nam",
    "bảo vệ thực vật Việt Nam",
]

ALL_KEYWORDS = KEYWORDS_HUMAN + KEYWORDS_ANIMAL + KEYWORDS_PLANT


# ========================
# FILTER: chỉ lấy bài liên quan Việt Nam + dịch bệnh
# ========================

VIETNAM_WORDS = [
    "việt nam",
    "hà nội",
    "tp hcm",
    "thành phố hồ chí minh",
    "đà nẵng",
    "cần thơ",
    "hải phòng",
    "quảng nam",
    "nghệ an",
    "thanh hóa",
    "đồng nai",
    "bình dương",
    "an giang",
    "tiền giang",
    "bến tre",
    "vĩnh long",
    "khánh hòa",
    "lâm đồng",
    "đắk lắk",
    "gia lai",
    "tỉnh",
    "thành phố",
    "huyện",
    "xã",
]

EPIDEMIC_WORDS = [
    "dịch bệnh",
    "ổ dịch",
    "ca nhiễm",
    "ca mắc",
    "ca tử vong",
    "lây nhiễm",
    "bùng phát",
    "truyền nhiễm",
    "virus",
    "vi khuẩn",
    "vi rút",
    "dịch hại",
    "sâu bệnh",
    "bệnh hại",
    "cúm",
    "sốt xuất huyết",
    "tay chân miệng",
    "dịch tả",
    "lở mồm",
    "cúm gia cầm",
    "phòng chống dịch",
    "phun thuốc",
    "tiêu hủy đàn",
]


def is_valid_article(title: str, content: str) -> bool:
    text = f"{title or ''} {content or ''}".lower()
    is_vn = any(w in text for w in VIETNAM_WORDS)
    is_epi = any(w in text for w in EPIDEMIC_WORDS)
    return is_vn and is_epi


# ========================
# CRAWL TỪNG NGUỒN
# ========================


def crawl_all_links() -> list[dict]:
    """
    Bước 1: Thu thập danh sách link từ tất cả nguồn.
    Chưa fetch content — chỉ lấy URL + metadata.
    """
    all_items: list[dict] = []

    print("\n📡 Crawling links từ các nguồn...")

    # ── RSS trước (nhanh + date chuẩn) ──
    rss_sources = [
        ("VnExpress RSS", crawl_vnexpress_rss),
        ("Sức khỏe RSS", crawl_suckhoe_rss),
        ("Nông nghiệp RSS", crawl_nongnghiep_rss),
    ]
    for name, func in rss_sources:
        try:
            items = func()
            all_items.extend(items)
            print(f"  ✅ {name}: {len(items)} links")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

    # ── Search page ──
    search_sources = [
        ("VnExpress", crawl_vnexpress, ALL_KEYWORDS, 5),
        ("DanTri", crawl_dantri, ALL_KEYWORDS, 5),
        ("Sức khỏe & Đời sống", crawl_suckhoedoisong, KEYWORDS_HUMAN, 4),
        ("Nông nghiệp VN", crawl_nongnghiep, KEYWORDS_ANIMAL + KEYWORDS_PLANT, 4),
        ("Người Chăn nuôi", crawl_nguoichannuoi, KEYWORDS_ANIMAL, 4),
        ("Tạp chí BVTV", crawl_baovethucvat, KEYWORDS_PLANT, 3),
    ]

    for src_name, func, kw_set, pages in search_sources:
        print(f"\n  📡 {src_name} ({len(kw_set)} keywords × {pages} pages)...")
        src_count = 0
        for keyword in kw_set:
            try:
                items = func(keyword, max_pages=pages)
                all_items.extend(items)
                src_count += len(items)
            except Exception as e:
                print(f"    ❌ '{keyword}': {e}")
        print(f"  ✅ {src_name}: {src_count} links tổng")

    return all_items


def deduplicate(items: list[dict]) -> list[dict]:
    seen: dict = {}
    for item in items:
        seen[item["url"]] = item
    return list(seen.values())


# ========================
# MAIN CRAWL LOGIC
# ========================


def main():
    print("\n" + "=" * 60)
    print(
        f"🔍 Bắt đầu thu thập dữ liệu — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"🤖 Bộ lọc AI: {get_filter_status()}")
    print(f"⚡ Content workers: {CONTENT_WORKERS} luồng song song")

    # Bước 1: Thu thập link
    all_items = crawl_all_links()
    all_items = deduplicate(all_items)
    print(f"\n📦 Tổng link sau lọc trùng: {len(all_items)}")

    if not all_items:
        print("⚠️  Không có link nào, kết thúc chu kỳ.")
        return

    # Bước 2: Fetch content song song
    print(f"\n⚡ Fetching content song song ({CONTENT_WORKERS} workers)...")
    t0 = time.time()
    all_items = get_contents_parallel(all_items, max_workers=CONTENT_WORKERS)
    elapsed = time.time() - t0
    print(f"   Hoàn thành trong {elapsed:.1f}s")

    # Bước 3: Filter + lưu DB
    saved = 0
    skipped = 0
    failed = 0
    date_found = 0
    date_missing = 0

    total = len(all_items)
    for i, item in enumerate(all_items):
        url = item["url"]
        source_name = item.get("source_name", "Unknown")
        title = item.get("title") or ""
        content = item.get("content") or ""
        pub_at = item.get("published_at")

        if pub_at:
            date_found += 1
        else:
            date_missing += 1

        print(f"\n[{i + 1}/{total}] 🔗 {url[:80]}")
        if pub_at:
            print(f"   📅 {pub_at}")

        try:
            if not title or not content:
                print("  ⚠️  Không có nội dung → bỏ qua")
                skipped += 1
                continue

            if not is_valid_article(title, content):
                print("  ⏭️  Không phải bài dịch bệnh VN → bỏ qua")
                skipped += 1
                continue

            ai_result = classify_article(title, content)
            if not ai_result["is_relevant"]:
                print(
                    f"  🤖 AI loại: {ai_result.get('reason', 'không phù hợp')} "
                    f"(conf={ai_result.get('confidence', 0):.2f})"
                )
                skipped += 1
                continue

            print(
                f"  🤖 AI giữ: {ai_result.get('method')} | "
                f"{ai_result.get('category')} | "
                f"{ai_result.get('primary_topic')} "
                f"(conf={ai_result.get('confidence', 0):.2f})"
            )

            ok = save_raw_article(
                title=title,
                link=url,
                content=content,
                source_name=source_name,
                published_at=pub_at,
            )

            if ok:
                saved += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ❌ Lỗi xử lý: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"✅ Lưu thành công : {saved}")
    print(f"⏭️  Bỏ qua         : {skipped}")
    print(f"❌ Thất bại        : {failed}")
    print(
        f"📅 Có ngày đăng   : {date_found} / {total} ({100 * date_found // total if total else 0}%)"
    )
    print(f"📅 Thiếu ngày     : {date_missing}")
    print("=" * 60)


# ========================
# RUN SERVICE — tự động lặp theo schedule
# ========================

if __name__ == "__main__":
    print("🚀 Crawler Service khởi động...")
    print(f"⏱️  Chu kỳ cào: mỗi {CRAWL_INTERVAL_MIN} phút")
    print(f"⚡ Số worker song song: {CONTENT_WORKERS}")
    init_db()

    while True:
        start = time.time()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚀 [{now}] Bắt đầu chu kỳ cào dữ liệu...")

        try:
            main()
        except Exception as e:
            print(f"❌ Lỗi nghiêm trọng trong chu kỳ: {e}")

        elapsed_min = (time.time() - start) / 60
        wait_min = max(1, CRAWL_INTERVAL_MIN - elapsed_min)

        next_run = datetime.now().replace(microsecond=0)
        print(f"\n⏱️  Chu kỳ hoàn thành trong {elapsed_min:.1f} phút.")
        print(f"⏳ Nghỉ {wait_min:.1f} phút → chu kỳ tiếp theo lúc ~{next_run}\n")
        time.sleep(wait_min * 60)
