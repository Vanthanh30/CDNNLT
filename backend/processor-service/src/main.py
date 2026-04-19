import time
from nlp_engine import detect_keyword
from database import get_unprocessed_articles, update_keywords, init_db

def process_data():
    # 1. Lấy tin chưa có keywords (NULL)
    articles = get_unprocessed_articles(limit=10)
    
    if not articles:
        print("😴 [Processor] Không có tin mới để xử lý.")
        return

    for art in articles:
        print(f"🧠 [AI] Đang phân tích: {art['title'][:50]}...")
        
        # 2. Bóc tách keyword từ content
        keywords = detect_keyword(art['content'])
        
        # 3. Cập nhật vào DB (Truyền vào list, hàm database.py sẽ tự join)
        update_keywords(art['id'], keywords)
        
        print(f"✅ [AI] Đã gắn nhãn: {keywords}")

if __name__ == "__main__":
    print("🚀 Processor Service đã sẵn sàng...")
    init_db()
    while True:
        process_data()
        time.sleep(10)