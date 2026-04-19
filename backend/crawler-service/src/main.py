import time
from datetime import datetime
from spiders import crawl_vnexpress, crawl_dantri, get_content
from database import save_raw_article

KEYWORDS = ["dịch bệnh", "virus", "covid", "sốt xuất huyết", "cúm"]

def main():
    all_links = []

    for kw in KEYWORDS:
        print(f"\n🔍 Đang cào từ khóa: '{kw}'")
        all_links += crawl_vnexpress(kw, max_pages=5)
        all_links += crawl_dantri(kw, max_pages=5)

    # Loại link trùng trong lượt này
    all_links = list(set(filter(None, all_links)))
    print(f"\n📦 Tổng link sau khi lọc trùng: {len(all_links)}")

    saved = 0
    for link in all_links:
        title, content = get_content(link)
        if content:
            save_raw_article(title, link, content)
            saved += 1

    print(f"\n✅ Đã lưu {saved}/{len(all_links)} bài vào database.")

if __name__ == "__main__":
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚀 [{now}] Crawler bắt đầu quét 1 tháng gần nhất...")
        main()
        print("⏱️ Hoàn thành. Nghỉ 30 phút rồi quét tiếp...")
        time.sleep(1800)  # 30 phút (thay vì 5 phút)