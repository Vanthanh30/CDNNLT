import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
import time

headers = {"User-Agent": "Mozilla/5.0"}

def get_date_range():
    """Trả về (from_date, to_date) trong 30 ngày gần nhất"""
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    return from_date, to_date

# -------- VnExpress --------
def crawl_vnexpress(keyword, max_pages=5):
    """
    Crawl VnExpress với bộ lọc 30 ngày gần nhất.
    VnExpress hỗ trợ: fromdate & todate dạng Unix timestamp.
    """
    from_date, to_date = get_date_range()
    from_ts = int(from_date.timestamp())
    to_ts   = int(to_date.timestamp())

    links = []

    for page in range(1, max_pages + 1):
        url = (
            f"https://timkiem.vnexpress.net/?q={keyword}"
            f"&fromdate={from_ts}&todate={to_ts}&page={page}"
        )
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            found = [a.get("href") for a in soup.select(".item-news h3.title-news a")]
            if not found:
                print(f"[VnExpress] Hết kết quả ở trang {page}, dừng.")
                break

            links += found
            print(f"[VnExpress] Trang {page}: +{len(found)} link")
            time.sleep(1)  # Tránh bị chặn

        except Exception as e:
            print(f"[VnExpress] Lỗi trang {page}: {e}")
            break

    return links


# -------- Dân Trí --------
def crawl_dantri(keyword, max_pages=5):
    """
    Crawl Dân Trí, dừng khi gặp bài viết cũ hơn 30 ngày.
    Dân Trí không có date filter trên URL → kiểm tra ngày từng bài.
    """
    from_date, _ = get_date_range()
    links = []

    for page in range(1, max_pages + 1):
        url = f"https://dantri.com.vn/tim-kiem.htm?q={keyword}&page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            articles = soup.select("article.article-item")
            if not articles:
                print(f"[DanTri] Hết kết quả ở trang {page}, dừng.")
                break

            stop_crawl = False
            for art in articles:
                # Lấy ngày đăng
                time_tag = art.select_one("time")
                if time_tag and time_tag.get("datetime"):
                    try:
                        pub_date = datetime.fromisoformat(
                            time_tag["datetime"].replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        if pub_date < from_date:
                            print(f"[DanTri] Gặp bài cũ hơn 30 ngày, dừng pagination.")
                            stop_crawl = True
                            break
                    except Exception:
                        pass  # Không parse được ngày → cứ lấy

                a_tag = art.select_one("h3.article-title a")
                if a_tag and a_tag.get("href"):
                    href = a_tag["href"]
                    # DanTri dùng relative URL
                    if href.startswith("/"):
                        href = "https://dantri.com.vn" + href
                    links.append(href)

            print(f"[DanTri] Trang {page}: +{len(articles)} bài")
            time.sleep(1)

            if stop_crawl:
                break

        except Exception as e:
            print(f"[DanTri] Lỗi trang {page}: {e}")
            break

    return links


# -------- Lấy nội dung --------
def get_content(url):
    try:
        article = Article(url, language="vi")
        article.download()
        article.parse()
        return article.title, article.text
    except:
        return None, None