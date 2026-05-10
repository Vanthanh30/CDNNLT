"""
main.py (crawler-service) — Thu thập bài báo dịch bệnh Việt Nam
THAY ĐỔI:
- _fetch_and_save(): nhận published_at 3 tầng:
    1. published_at từ spider (RSS / list-page scrape)
    2. art.publish_date từ newspaper3k  (get_content trả về tuple 3 phần tử)
    3. _scrape_publish_date() từ HTML bài (meta/JSON-LD/URL regex)
- get_content() giờ trả về (title, content, pub_date) — import từ spiders
- APScheduler + while-loop fallback giữ nguyên
"""

import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from spiders import (
    crawl_vnexpress,
    crawl_vnexpress_rss,
    crawl_dantri,
    crawl_suckhoedoisong,
    crawl_suckhoe_rss,
    crawl_thanhnien,
    crawl_tuoitre,
    crawl_nongnghiep,
    crawl_nongnghiep_rss,
    crawl_nguoichannuoi,
    crawl_baovethucvat,
    crawl_thuy,
    crawl_cucbvtv,
    get_content,
    _scrape_publish_date,   # dùng làm fallback cuối
)
from database import save_raw_article, init_db


# ========================
# KEYWORDS
# ========================

KEYWORDS_HUMAN = [
    "dịch bệnh Việt Nam", "bệnh truyền nhiễm Việt Nam", "ổ dịch Việt Nam",
    "ca nhiễm Việt Nam", "bùng phát dịch Việt Nam", "nguy cơ dịch bệnh Việt Nam",
    "sốt xuất huyết Việt Nam", "tay chân miệng Việt Nam", "cúm Việt Nam",
    "sởi Việt Nam", "đậu mùa khỉ Việt Nam", "whitmore Việt Nam", "adenovirus Việt Nam",
]

KEYWORDS_ANIMAL = [
    "dịch bệnh động vật Việt Nam", "dịch bệnh gia súc Việt Nam",
    "dịch bệnh gia cầm Việt Nam", "ổ dịch động vật Việt Nam",
    "dịch tả lợn Việt Nam", "cúm gia cầm Việt Nam",
    "lở mồm long móng Việt Nam", "tai xanh Việt Nam",
    "bệnh dại Việt Nam", "tiêu hủy gia cầm Việt Nam",
]

KEYWORDS_PLANT = [
    "dịch bệnh cây trồng Việt Nam", "sâu bệnh cây trồng Việt Nam",
    "dịch hại cây trồng Việt Nam", "bệnh hại cây trồng Việt Nam",
    "rầy nâu lúa", "đạo ôn lúa", "bệnh lúa Việt Nam", "bảo vệ thực vật Việt Nam",
]

ALL_KEYWORDS    = KEYWORDS_HUMAN + KEYWORDS_ANIMAL + KEYWORDS_PLANT
BATCH_URL_LIMIT = 500


# ========================
# FILTER
# ========================

VIETNAM_WORDS = [
    "việt nam", "hà nội", "tp hcm", "thành phố hồ chí minh",
    "đà nẵng", "cần thơ", "hải phòng", "quảng nam",
    "nghệ an", "thanh hóa", "đồng nai", "bình dương",
    "an giang", "tiền giang", "bến tre", "vĩnh long",
    "khánh hòa", "lâm đồng", "đắk lắk", "gia lai",
    "tỉnh", "thành phố", "huyện", "xã",
]

EPIDEMIC_WORDS = [
    "dịch bệnh", "ổ dịch", "ca nhiễm", "ca mắc", "ca tử vong",
    "lây nhiễm", "bùng phát", "truyền nhiễm",
    "virus", "vi khuẩn", "vi rút",
    "dịch hại", "sâu bệnh", "bệnh hại",
    "cúm", "sốt xuất huyết", "tay chân miệng",
    "dịch tả", "lở mồm", "cúm gia cầm",
    "phòng chống dịch", "phun thuốc", "tiêu hủy đàn",
]


def is_valid_article(title: str, content: str) -> bool:
    text   = f"{title or ''} {content or ''}".lower()
    is_vn  = any(w in text for w in VIETNAM_WORDS)
    is_epi = any(w in text for w in EPIDEMIC_WORDS)
    return is_vn and is_epi


# ========================
# CRAWL TẤT CẢ NGUỒN
# ========================

def crawl_all_sources() -> list:
    all_items = []

    print("\n📡 Crawling RSS feeds...")
    for rss_fn, label in [
        (crawl_vnexpress_rss,  "VnExpress RSS"),
        (crawl_suckhoe_rss,    "SKDS RSS"),
        (crawl_nongnghiep_rss, "NongNghiep RSS"),
        (crawl_thuy,           "Cục Thú y"),
        (crawl_cucbvtv,        "Cục BVTV"),
    ]:
        try:
            items = rss_fn()
            all_items.extend(items)
            print(f"  ✅ {label}: {len(items)} links")
        except Exception as e:
            print(f"  ❌ {label}: {e}")

    keyword_sources = [
        ("VnExpress",           crawl_vnexpress,      5, ALL_KEYWORDS),
        ("DanTri",              crawl_dantri,          5, ALL_KEYWORDS),
        ("Sức khỏe & Đời sống", crawl_suckhoedoisong,  4, KEYWORDS_HUMAN),
        ("Thanh Niên",          crawl_thanhnien,       4, KEYWORDS_HUMAN),
        ("Tuổi Trẻ",            crawl_tuoitre,         4, KEYWORDS_HUMAN),
        ("Nông nghiệp VN",      crawl_nongnghiep,      3, KEYWORDS_ANIMAL + KEYWORDS_PLANT),
        ("Người Chăn nuôi",     crawl_nguoichannuoi,   3, KEYWORDS_ANIMAL),
        ("Tạp chí BVTV",        crawl_baovethucvat,    3, KEYWORDS_PLANT),
    ]

    for src_name, func, pages, kw_set in keyword_sources:
        print(f"\n📡 Crawling {src_name} ({len(kw_set)} keywords)...")
        for keyword in kw_set:
            try:
                items = func(keyword, max_pages=pages)
                all_items.extend(items)
                if items:
                    print(f"  ✅ '{keyword}': {len(items)} links")
            except Exception as e:
                print(f"  ❌ '{keyword}' @ {src_name}: {e}")

    return all_items


# ========================
# FETCH + SAVE (song song)
# ========================

def _merge_publish_date(
    spider_date: str | None,
    article_date: str | None,
    scraped_date: str | None,
) -> str | None:
    """
    Chọn ngày theo độ ưu tiên:
      1. spider_date  (từ RSS / list-page — thường chính xác nhất)
      2. article_date (từ newspaper3k)
      3. scraped_date (từ meta/JSON-LD/URL của bài)
    Trả về None nếu cả 3 đều None.
    """
    return spider_date or article_date or scraped_date


def _fetch_and_save(item: dict) -> str:
    """
    Worker chạy trong thread:
      1. Fetch bài bằng get_content() — trả về (title, content, pub_date_from_article)
      2. Merge published_at từ 3 nguồn
      3. Lưu DB
    """
    url         = item["url"]
    source_name = item.get("source_name", "Unknown")
    spider_date = item.get("published_at")   # Tầng 1: spider đã lấy

    try:
        # get_content() trả về tuple 3 phần tử (title, content, pub_date)
        title, content, article_date = get_content(url)   # Tầng 2: newspaper3k

        if not title or not content:
            return f"⚠️  Rỗng: {url[:60]}"

        if not is_valid_article(title, content):
            return f"⏭️  Không phải dịch bệnh VN: {url[:60]}"

        # Tầng 3: _scrape_publish_date chỉ gọi nếu 2 tầng trên chưa có
        scraped_date = None
        if not spider_date and not article_date:
            scraped_date = _scrape_publish_date(url)

        published_at = _merge_publish_date(spider_date, article_date, scraped_date)

        # Log để debug
        date_src = (
            "spider"   if spider_date  else
            "article"  if article_date else
            "scraped"  if scraped_date else
            "NULL"
        )
        print(f"    📅 published_at={published_at} (src={date_src})")

        ok = save_raw_article(
            title=title,
            link=url,
            content=content,
            source_name=source_name,
            published_at=published_at,
        )
        if ok:
            return f"✅ Lưu: {title[:60]}"
        else:
            return f"ℹ️  Trùng/lỗi: {url[:60]}"

    except Exception as e:
        return f"❌ Lỗi: {url[:60]} — {e}"


def process_urls_parallel(items: list, max_workers: int = 10) -> dict:
    counters = {"saved": 0, "skipped": 0, "failed": 0}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_fetch_and_save, item): item for item in items}

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            print(f"  [{i}/{len(items)}] {result}")

            if result.startswith("✅"):
                counters["saved"] += 1
            elif result.startswith(("⏭️", "ℹ️", "⚠️")):
                counters["skipped"] += 1
            else:
                counters["failed"] += 1

    return counters


# ========================
# MAIN CRAWL LOGIC
# ========================

def main():
    print("\n" + "=" * 60)
    print(f"🔍 Bắt đầu thu thập [{datetime.now():%Y-%m-%d %H:%M:%S}]")

    all_items = crawl_all_sources()

    unique: dict = {}
    for item in all_items:
        unique[item["url"]] = item
    all_items = list(unique.values())

    print(f"\n📦 Tổng link sau lọc trùng: {len(all_items)}")

    if len(all_items) > BATCH_URL_LIMIT:
        print(f"⚠️  Cắt bớt xuống {BATCH_URL_LIMIT} URL (batch limit)")
        all_items = all_items[:BATCH_URL_LIMIT]

    counters = process_urls_parallel(all_items, max_workers=10)

    print("\n" + "=" * 60)
    print(f"✅ Lưu thành công : {counters['saved']}")
    print(f"⏭️  Bỏ qua         : {counters['skipped']}")
    print(f"❌ Thất bại        : {counters['failed']}")
    print("=" * 60)


# ========================
# SCHEDULER
# ========================

if __name__ == "__main__":
    print("🚀 Crawler Service khởi động...")
    init_db()

    main()

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
        scheduler.add_job(main, "interval", minutes=30, id="crawl_job")
        print("\n⏱️  Scheduler khởi động — chạy mỗi 30 phút")
        scheduler.start()
    except ImportError:
        print("\n⚠️  APScheduler chưa cài, dùng while loop fallback")
        while True:
            time.sleep(30 * 60)
            main()