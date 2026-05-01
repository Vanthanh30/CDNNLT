import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
from urllib.parse import quote_plus


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ========================
# DATE RANGE
# ========================
def get_date_range():
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)
    return from_date, to_date


# ========================
# SAFE REQUEST (retry)
# ========================
def fetch_url(url, retries=3):
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            return res.text
        except Exception as e:
            print(f"⚠️ Retry {i+1}: {url}")
            time.sleep(1)
    return None


# ========================
# FILTER LINK
# ========================
def is_valid_url(url):
    if not url:
        return False

    # bỏ video / ảnh
    bad_patterns = [
        "/video",
        "/infographic",
        ".jpg",
        ".png"
    ]

    return not any(p in url for p in bad_patterns)


# ========================
# VNEXPRESS
# ========================
def crawl_vnexpress(keyword, max_pages=3):
    from_date, to_date = get_date_range()
    from_ts = int(from_date.timestamp())
    to_ts = int(to_date.timestamp())

    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = (
            f"https://timkiem.vnexpress.net/?q={keyword_encoded}"
            f"&fromdate={from_ts}&todate={to_ts}&page={page}"
        )

        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        found = soup.select(".item-news h3.title-news a")

        if not found:
            print(f"[VnExpress] Hết trang {page}")
            break

        for a in found:
            href = a.get("href")

            if not is_valid_url(href):
                continue

            results.append({
                "url": href.strip(),
                "source_name": "VnExpress",
                "published_at": None
            })

        print(f"[VnExpress] Page {page}: {len(found)}")
        time.sleep(0.8)

    return results


# ========================
# DANTRI
# ========================
def crawl_dantri(keyword, max_pages=3):
    from_date, _ = get_date_range()
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://dantri.com.vn/tim-kiem.htm?q={keyword_encoded}&page={page}"

        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        articles = soup.select("article.article-item")

        if not articles:
            print(f"[DanTri] Hết trang {page}")
            break

        stop = False

        for art in articles:
            published_at = None

            # parse date
            time_tag = art.select_one("time")

            if time_tag and time_tag.get("datetime"):
                try:
                    pub_date = datetime.fromisoformat(
                        time_tag["datetime"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)

                    if pub_date < from_date:
                        stop = True
                        break

                    published_at = pub_date.strftime("%Y-%m-%d %H:%M:%S")

                except:
                    pass

            a_tag = art.select_one("h3.article-title a")

            if a_tag:
                href = a_tag.get("href")

                if href.startswith("/"):
                    href = "https://dantri.com.vn" + href

                if not is_valid_url(href):
                    continue

                results.append({
                    "url": href.strip(),
                    "source_name": "DanTri",
                    "published_at": published_at
                })

        print(f"[DanTri] Page {page}: {len(articles)}")
        time.sleep(0.8)

        if stop:
            break

    return results


# ========================
# GET CONTENT
# ========================
def get_content(url):
    try:
        article = Article(url, language="vi")
        article.download()
        article.parse()

        title = article.title
        content = article.text

        if not title or not content:
            return None, None

        # bỏ bài quá ngắn
        if len(content) < 200:
            return None, None

        return title.strip(), content.strip()

    except Exception:
        return fallback_get_content(url)


# ========================
# FALLBACK (bs4)
# ========================
def fallback_get_content(url):
    try:
        html = fetch_url(url)
        if not html:
            return None, None

        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string if soup.title else ""

        paragraphs = soup.find_all("p")
        content = " ".join([p.get_text() for p in paragraphs])

        if len(content) < 200:
            return None, None

        return title, content

    except:
        return None, None