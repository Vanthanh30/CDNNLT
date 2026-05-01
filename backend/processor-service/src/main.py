import time
from nlp_engine import extract_info
from database import (
    get_unprocessed_articles,
    save_processed_article,
    init_db
)


def process_data():
    articles = get_unprocessed_articles(limit=10)

    if not articles:
        print("😴 Không có bài mới.")
        return

    for art in articles:
        print(f"\n🧠 Processing: {art['title'][:60]}...")

        try:
            result = extract_info(
                title=art.get("title"),
                content=art.get("content")
            )

            print("👉 Extracted:")
            print(result)

            save_processed_article(
                raw_article_id=art["id"],
                summary=art["title"],
                content_clean=art["content"],
                disease_name=result["disease_name"],
                location=result["location"],
                event_date=None,
                risk_level="LOW",
                cases_infected=result["cases"],
                cases_dead=0,
                cases_recovered=0
            )

            print("✅ Saved to DB")

        except Exception as e:
            print(f"❌ Lỗi xử lý: {e}")


if __name__ == "__main__":
    print("🚀 Processor Service started...")
    init_db()

    while True:
        process_data()
        time.sleep(10)