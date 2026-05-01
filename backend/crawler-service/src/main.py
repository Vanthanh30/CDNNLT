import time
from datetime import datetime

from spiders import (
    crawl_vnexpress,
    crawl_dantri,
    get_content,
)
from database import save_raw_article, init_db


# ========================
# KEYWORDS (GENERALIZED)
# ========================
KEYWORDS = [
    # Human
    "dịch bệnh Việt Nam",
    "bệnh truyền nhiễm Việt Nam",
    "ổ dịch Việt Nam",
    "ca nhiễm Việt Nam",
    "bùng phát dịch Việt Nam",
    "nguy cơ dịch bệnh Việt Nam",

    # Animal
    "dịch bệnh động vật Việt Nam",
    "dịch bệnh gia súc Việt Nam",
    "dịch bệnh gia cầm Việt Nam",
    "ổ dịch động vật Việt Nam",

    # Plant
    "dịch bệnh cây trồng Việt Nam",
    "sâu bệnh cây trồng Việt Nam",
    "dịch hại cây trồng Việt Nam",
    "bệnh hại cây trồng Việt Nam",
]


# ========================
# FILTER VIETNAM + EPIDEMIC
# ========================
VIETNAM_WORDS = [
    "việt nam", "hà nội", "tp hcm", "thành phố hồ chí minh",
    "đà nẵng", "cần thơ", "hải phòng", "quảng nam",
    "nghệ an", "thanh hóa", "đồng nai", "bình dương"
]

EPIDEMIC_WORDS = [
    "dịch", "dịch bệnh", "ổ dịch", "ca nhiễm",
    "lây nhiễm", "bùng phát", "truyền nhiễm",
    "virus", "vi khuẩn",
    "dịch hại", "sâu bệnh", "bệnh hại"
]


def is_valid_article(title, content):
    text = f"{title or ''} {content or ''}".lower()

    is_vn = any(w in text for w in VIETNAM_WORDS)
    is_epi = any(w in text for w in EPIDEMIC_WORDS)

    return is_vn and is_epi


# ========================
# MAIN CRAWL LOGIC
# ========================
def main():
    all_items = []

    # Crawl links
    for keyword in KEYWORDS:
        print(f"\n🔍 Keyword: {keyword}")

        try:
            all_items.extend(crawl_vnexpress(keyword, max_pages=3))
            all_items.extend(crawl_dantri(keyword, max_pages=3))
        except Exception as e:
            print(f"❌ Crawl lỗi keyword {keyword}: {e}")

    # Remove duplicate links
    unique = {}
    for item in all_items:
        unique[item["url"]] = item

    all_items = list(unique.values())

    print(f"\n📦 Tổng link sau lọc trùng: {len(all_items)}")

    saved = 0
    skipped = 0
    failed = 0

    # Crawl content
    for i, item in enumerate(all_items):
        url = item["url"]
        source_name = item.get("source_name", "Unknown")
        published_at = item.get("published_at")

        print(f"\n[{i+1}/{len(all_items)}] 🔗 {url}")

        try:
            title, content = get_content(url)

            if not title or not content:
                print("⚠️ Không có nội dung → bỏ")
                skipped += 1
                continue

            # Filter Vietnam + epidemic
            if not is_valid_article(title, content):
                print("⏭️ Không phải bài dịch bệnh VN → bỏ")
                skipped += 1
                continue

            ok = save_raw_article(
                title=title,
                link=url,
                content=content,
                source_name=source_name,
                published_at=published_at
            )

            if ok:
                saved += 1
            else:
                failed += 1

        except Exception as e:
            print(f"❌ Lỗi xử lý bài: {e}")
            failed += 1

        # tránh bị block
        time.sleep(0.5)

    print("\n====================")
    print(f"✅ Saved: {saved}")
    print(f"⏭️ Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    print("====================")


# ========================
# RUN SERVICE
# ========================
if __name__ == "__main__":
    print("🚀 Crawler Service started...")
    init_db()

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚀 [{now}] Start crawling...")

        main()

        print("\n⏱️ Sleep 30 minutes...\n")
        time.sleep(1800)