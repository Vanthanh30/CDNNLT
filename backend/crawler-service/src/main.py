"""
main.py (crawler-service) - Thu thập bài báo dịch bệnh Việt Nam từ nhiều nguồn
Chạy mỗi 30 phút. Cào trong vòng 30 ngày.
"""

import time
from datetime import datetime

from spiders import (
    crawl_vnexpress,
    crawl_dantri,
    crawl_suckhoedoisong,
    crawl_nongnghiep,
    crawl_nguoichannuoi,
    crawl_baovethucvat,
    get_content,
)
from ai_filter import classify_article, get_filter_status
from database import save_raw_article, init_db


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
# CRAWL TỪNG NGUỒN THEO KEYWORD
# ========================


def crawl_all_sources(keywords: list) -> list:
    all_items = []

    # Định nghĩa nguồn và max_pages
    sources = [
        ("VnExpress", crawl_vnexpress, 5, True),  # (name, func, pages, use_all_kw)
        ("DanTri", crawl_dantri, 5, True),
        ("Sức khỏe & Đời sống", crawl_suckhoedoisong, 4, False),  # chỉ kw người
        ("Nông nghiệp VN", crawl_nongnghiep, 4, False),  # chỉ kw động vật + cây
        ("Người Chăn nuôi", crawl_nguoichannuoi, 4, False),
        ("Bảo vệ Thực vật", crawl_baovethucvat, 3, False),
    ]

    kw_human = KEYWORDS_HUMAN
    kw_animal = KEYWORDS_ANIMAL
    kw_plant = KEYWORDS_PLANT

    for src_name, func, pages, use_all in sources:
        if use_all:
            kw_set = ALL_KEYWORDS
        elif "sức khỏe" in src_name.lower():
            kw_set = kw_human
        elif "nông nghiệp" in src_name.lower() or "chăn nuôi" in src_name.lower():
            kw_set = kw_animal + kw_plant
        elif "thực vật" in src_name.lower():
            kw_set = kw_plant
        else:
            kw_set = ALL_KEYWORDS

        print(f"\n📡 Crawling {src_name} ({len(kw_set)} keywords)...")

        for keyword in kw_set:
            try:
                items = func(keyword, max_pages=pages)
                all_items.extend(items)
                print(f"  ✅ '{keyword}': {len(items)} links")
            except Exception as e:
                print(f"  ❌ '{keyword}' @ {src_name}: {e}")

    return all_items


# ========================
# MAIN CRAWL LOGIC
# ========================


def main():
    print("\n" + "=" * 60)
    print("🔍 Bắt đầu thu thập dữ liệu...")
    print(f"🤖 Bộ lọc AI: {get_filter_status()}")

    # Crawl từ tất cả nguồn
    all_items = crawl_all_sources(ALL_KEYWORDS)

    # Loại trùng URL
    unique: dict = {}
    for item in all_items:
        unique[item["url"]] = item
    all_items = list(unique.values())

    print(f"\n📦 Tổng link sau lọc trùng: {len(all_items)}")

    saved = 0
    skipped = 0
    failed = 0

    for i, item in enumerate(all_items):
        url = item["url"]
        source_name = item.get("source_name", "Unknown")
        pub_at = item.get("published_at")

        print(f"\n[{i + 1}/{len(all_items)}] 🔗 {url[:80]}")

        try:
            title, content = get_content(url)

            if not title or not content:
                print("  ⚠️ Không có nội dung → bỏ qua")
                skipped += 1
                continue

            if not is_valid_article(title, content):
                print("  ⏭️ Không phải bài dịch bệnh VN → bỏ qua")
                skipped += 1
                continue

            ai_result = classify_article(title, content)
            if not ai_result["is_relevant"]:
                print(
                    "  🤖 AI loại bài: "
                    f"{ai_result.get('reason', 'không phù hợp')} "
                    f"(confidence={ai_result.get('confidence', 0):.2f})"
                )
                skipped += 1
                continue

            print(
                "  🤖 AI giữ bài: "
                f"{ai_result.get('method', 'unknown')} | "
                f"{ai_result.get('category', 'unknown')} | "
                f"{ai_result.get('primary_topic', '')} "
                f"(confidence={ai_result.get('confidence', 0):.2f})"
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

        # Tránh bị block
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"✅ Lưu thành công : {saved}")
    print(f"⏭️ Bỏ qua         : {skipped}")
    print(f"❌ Thất bại        : {failed}")
    print("=" * 60)


# ========================
# RUN SERVICE (loop mỗi 30 phút)
# ========================

if __name__ == "__main__":
    print("🚀 Crawler Service khởi động...")
    init_db()

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚀 [{now}] Bắt đầu chu kỳ cào dữ liệu...")

        main()

        wait_min = 30
        print(f"\n⏱️  Nghỉ {wait_min} phút...\n")
        time.sleep(wait_min * 60)
