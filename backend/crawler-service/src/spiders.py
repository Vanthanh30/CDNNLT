"""
spiders.py - Thu thập bài báo dịch bệnh từ nhiều nguồn tại Việt Nam
Nguồn hiện tại (10 nguồn):
  Người  : VnExpress, DanTri, Sức khỏe & Đời sống, Báo Sức khỏe (bacsituvan.vn),
            Báo Thanh Niên, Báo Tuổi Trẻ
  Động vật: Báo Nông nghiệp VN, Người Chăn nuôi, Cục Thú y (thuY.gov.vn)
  Cây trồng: Cục BVTV (bvtv.gov.vn), Tạp chí BVTV

THAY ĐỔI SO VỚI PHIÊN BẢN CŨ:
  - Cập nhật CSS selector cho DanTri, NongNghiep, NguoiChanNuoi
  - Thêm 4 nguồn mới: Thanh Niên, Tuổi Trẻ, Cục Thú y, Cục BVTV
  - Thêm crawl_thuy() và crawl_cucbvtv() dùng RSS/sitemap để tránh bị block
  - Cải thiện fallback_get_content: thêm selector chuyên biệt cho từng domain
  - is_valid_url: bổ sung thêm pattern lọc link rác
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin


# ========================
# HEADERS
# ========================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ========================
# DATE RANGE
# ========================
def get_date_range(days: int = 30):
    to_date   = datetime.now()
    from_date = to_date - timedelta(days=days)
    return from_date, to_date


# ========================
# SAFE REQUEST (retry + backoff)
# ========================
def fetch_url(url: str, retries: int = 3, timeout: int = 15) -> str | None:
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=timeout)
            res.raise_for_status()
            res.encoding = res.apparent_encoding or "utf-8"
            return res.text
        except Exception as e:
            print(f"  ⚠️  Retry {i+1}/{retries}: {url[:60]} — {e}")
            time.sleep(2 ** i)          # exponential backoff: 1s, 2s, 4s
    return None


# ========================
# FILTER LINK
# ========================
_BAD_URL_PATTERNS = [
    "/video", "/infographic", "/photo", "/gallery", "/clip",
    "/tag/", "/chu-de/", "/tac-gia/", "/category/",
    ".jpg", ".png", ".gif", ".mp4", ".webp",
    "javascript:", "#", "mailto:",
    "facebook.com", "youtube.com", "twitter.com",
]

def is_valid_url(url: str) -> bool:
    if not url or len(url) < 10:
        return False
    return not any(p in url.lower() for p in _BAD_URL_PATTERNS)


# ========================
# RSS HELPER (dùng cho các nguồn có RSS)
# ========================
def _crawl_rss(rss_url: str, source_name: str, domain_filter: str = "") -> list[dict]:
    """
    Lấy bài báo từ RSS feed. Trả về list dict {url, source_name, published_at}.
    """
    results = []
    html = fetch_url(rss_url)
    if not html:
        return results

    soup = BeautifulSoup(html, "xml")
    items = soup.find_all("item")

    if not items:
        # Fallback: Atom feed
        items = soup.find_all("entry")

    for item in items:
        link_tag = item.find("link")
        if link_tag:
            href = link_tag.get_text(strip=True) or link_tag.get("href", "")
        else:
            href = ""

        if not href:
            continue
        if domain_filter and domain_filter not in href:
            continue
        if not is_valid_url(href):
            continue

        pub_date = None
        pub_tag = item.find("pubDate") or item.find("published") or item.find("updated")
        if pub_tag:
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(pub_tag.get_text(strip=True))\
                               .strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        results.append({
            "url": href.strip(),
            "source_name": source_name,
            "published_at": pub_date,
        })

    print(f"  [{source_name}] RSS: {len(results)} items từ {rss_url}")
    return results


# ============================================================
# 1. VNEXPRESS  (tìm kiếm có phân trang)
# ============================================================
def crawl_vnexpress(keyword: str, max_pages: int = 5) -> list[dict]:
    from_date, to_date = get_date_range()
    from_ts = int(from_date.timestamp())
    to_ts   = int(to_date.timestamp())
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

        soup  = BeautifulSoup(html, "html.parser")
        found = soup.select(".item-news h3.title-news a")

        if not found:
            print(f"  [VnExpress] Hết trang {page}")
            break

        for a in found:
            href = a.get("href", "")
            if is_valid_url(href):
                results.append({
                    "url": href.strip(),
                    "source_name": "VnExpress",
                    "published_at": None,
                })

        print(f"  [VnExpress] Trang {page}: {len(found)} links")
        time.sleep(0.8)

    return results


# ============================================================
# 2. DANTRI  (cập nhật selector 2024-2025)
# ============================================================
def crawl_dantri(keyword: str, max_pages: int = 5) -> list[dict]:
    from_date, _ = get_date_range()
    results = []
    keyword_encoded = quote_plus(keyword)

    # DanTri đã đổi URL tìm kiếm
    for page in range(1, max_pages + 1):
        url = f"https://dantri.com.vn/tim-kiem.htm?keywords={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            # Thử URL cũ nếu URL mới thất bại
            url = f"https://dantri.com.vn/tim-kiem.htm?q={keyword_encoded}&page={page}"
            html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        # Thử nhiều selector khác nhau
        articles = (
            soup.select("article.article-item")
            or soup.select("div.article-item")
            or soup.select(".news-item")
            or soup.select("article[data-id]")
        )

        if not articles:
            # Fallback: lấy tất cả link bài báo
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://dantri.com.vn" + href
                # DanTri article URL dạng /chu-de/title-YYYYMMDD.htm
                if re.search(r"dantri\.com\.vn/[a-z\-]+/[a-z0-9\-]+-\d{8,}\.htm", href):
                    if is_valid_url(href):
                        results.append({
                            "url": href.strip(),
                            "source_name": "DanTri",
                            "published_at": None,
                        })
            print(f"  [DanTri] Trang {page}: fallback links")
            time.sleep(0.8)
            continue

        stop = False
        for art in articles:
            published_at = None
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
                except Exception:
                    pass

            a_tag = (
                art.select_one("h3.article-title a")
                or art.select_one("h2.article-title a")
                or art.select_one("h3 a")
                or art.select_one("h2 a")
                or art.select_one("a.article-title")
            )
            if a_tag:
                href = a_tag.get("href", "")
                if href.startswith("/"):
                    href = "https://dantri.com.vn" + href
                if is_valid_url(href):
                    results.append({
                        "url": href.strip(),
                        "source_name": "DanTri",
                        "published_at": published_at,
                    })

        print(f"  [DanTri] Trang {page}: {len(articles)} bài")
        time.sleep(0.8)
        if stop:
            break

    return results


# ============================================================
# 3. SỨC KHỎE & ĐỜI SỐNG  (suckhoedoisong.vn)
# ============================================================
def crawl_suckhoedoisong(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://suckhoedoisong.vn/tim-kiem.html?keyword={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            break

        soup  = BeautifulSoup(html, "html.parser")
        found = soup.select("article.story, div.story, li.story, .search-result-item a")

        hrefs = []
        for el in found:
            a = el.select_one("h3 a, h2 a, .story__heading a") if el.name != "a" else el
            if a:
                href = a.get("href", "")
                if href.startswith("/"):
                    href = "https://suckhoedoisong.vn" + href
                if is_valid_url(href) and "suckhoedoisong.vn" in href:
                    hrefs.append(href)

        if not hrefs:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://suckhoedoisong.vn" + href
                if "suckhoedoisong.vn" in href and is_valid_url(href):
                    # Lọc chỉ giữ URL bài báo (có dạng /tieu-de-nNNNNNNN.htm)
                    if re.search(r"-n\d{5,}\.htm", href):
                        hrefs.append(href)

        if not hrefs:
            print(f"  [SKDS] Hết trang {page}")
            break

        for href in set(hrefs):
            results.append({
                "url": href.strip(),
                "source_name": "Sức khỏe & Đời sống",
                "published_at": None,
            })

        print(f"  [SKDS] Trang {page}: {len(hrefs)} links")
        time.sleep(1.0)

    return results


# ============================================================
# 4. BÁO THANH NIÊN  (thanhnien.vn)  — nguồn MỚI
# ============================================================
def crawl_thanhnien(keyword: str, max_pages: int = 5) -> list[dict]:
    """
    Thanh Niên có search engine riêng: /tim-kiem/?q=...&page=...
    Bài báo URL dạng: https://thanhnien.vn/chu-de/tieu-de-185XXXXXXXX.htm
    """
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://thanhnien.vn/tim-kiem/?q={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        # Thử selector chính
        links = (
            soup.select(".box-category-item h3 a")
            or soup.select(".story__heading a")
            or soup.select(".item--title a")
            or soup.select("article h3 a")
            or soup.select("article h2 a")
        )

        hrefs = []
        for a in links:
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://thanhnien.vn" + href
            if is_valid_url(href) and "thanhnien.vn" in href:
                hrefs.append(href)

        if not hrefs:
            # Fallback: regex URL dạng Thanh Niên
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://thanhnien.vn" + href
                if re.search(r"thanhnien\.vn/[a-z0-9\-]+/[a-z0-9\-]+-185\d+\.htm", href):
                    hrefs.append(href)

        if not hrefs:
            print(f"  [ThanhNien] Hết trang {page}")
            break

        for href in set(hrefs):
            results.append({
                "url": href.strip(),
                "source_name": "Thanh Niên",
                "published_at": None,
            })

        print(f"  [ThanhNien] Trang {page}: {len(hrefs)} links")
        time.sleep(0.9)

    return results


# ============================================================
# 5. BÁO TUỔI TRẺ  (tuoitre.vn)  — nguồn MỚI
# ============================================================
def crawl_tuoitre(keyword: str, max_pages: int = 5) -> list[dict]:
    """
    Tuổi Trẻ dùng endpoint: /tim-kiem?q=...&p=...
    URL bài dạng: https://tuoitre.vn/tieu-de-XXXXXXXXXX.htm
    """
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://tuoitre.vn/tim-kiem?q={keyword_encoded}&p={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        links = (
            soup.select(".news-item h3 a")
            or soup.select(".search-result h3 a")
            or soup.select("li.search-result a")
            or soup.select("article h3 a")
            or soup.select(".title-news a")
        )

        hrefs = []
        for a in links:
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://tuoitre.vn" + href
            if is_valid_url(href) and "tuoitre.vn" in href:
                hrefs.append(href)

        if not hrefs:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://tuoitre.vn" + href
                if re.search(r"tuoitre\.vn/[a-z0-9\-]+-\d{10,}\.htm", href):
                    hrefs.append(href)

        if not hrefs:
            print(f"  [TuoiTre] Hết trang {page}")
            break

        for href in set(hrefs):
            results.append({
                "url": href.strip(),
                "source_name": "Tuổi Trẻ",
                "published_at": None,
            })

        print(f"  [TuoiTre] Trang {page}: {len(hrefs)} links")
        time.sleep(0.9)

    return results


# ============================================================
# 6. BÁO NÔNG NGHIỆP VIỆT NAM  (nongnghiep.vn)  — cập nhật selector
# ============================================================
def crawl_nongnghiep(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://nongnghiep.vn/tim-kiem/?keyword={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            # Thử URL format khác
            url = f"https://nongnghiep.vn/tim-kiem/?s={keyword_encoded}&page={page}"
            html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        links = (
            soup.select("h2.story__heading a")
            or soup.select("h3.story__heading a")
            or soup.select(".article-title a")
            or soup.select(".post-title a")
            or soup.select("article h3 a")
            or soup.select("article h2 a")
            or soup.select(".news-item__title a")
        )

        hrefs = []
        for a in links:
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://nongnghiep.vn" + href
            if is_valid_url(href) and "nongnghiep.vn" in href:
                hrefs.append(href)

        if not hrefs:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://nongnghiep.vn" + href
                # URL bài dạng /tieu-de-d123456.html hoặc /tieu-de.html
                if re.search(r"nongnghiep\.vn/[a-z0-9\-]+(?:-d\d+)?\.html?", href):
                    if is_valid_url(href):
                        hrefs.append(href)

        if not hrefs:
            print(f"  [NongNghiep] Hết trang {page}")
            break

        for href in set(hrefs):
            results.append({
                "url": href.strip(),
                "source_name": "Nông nghiệp Việt Nam",
                "published_at": None,
            })

        print(f"  [NongNghiep] Trang {page}: {len(hrefs)} links")
        time.sleep(1.0)

    return results


# ============================================================
# 7. NGƯỜI CHĂN NUÔI  (nguoichannuoi.vn)  — cập nhật selector
# ============================================================
def crawl_nguoichannuoi(keyword: str, max_pages: int = 4) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://nguoichannuoi.vn/?s={keyword_encoded}&paged={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        links = (
            soup.select("h2.entry-title a")
            or soup.select("h3.entry-title a")
            or soup.select(".post-title a")
            or soup.select(".article__title a")
            or soup.select("article h3 a")
            or soup.select("article h2 a")
        )

        if not links:
            # Fallback regex
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"nguoichannuoi\.vn/\d{4}/\d{2}/", href) or \
                   re.search(r"nguoichannuoi\.vn/[a-z0-9\-]+/$", href):
                    if is_valid_url(href):
                        results.append({
                            "url": href.strip(),
                            "source_name": "Người Chăn nuôi",
                            "published_at": None,
                        })
            print(f"  [NguoiChanNuoi] Trang {page}: fallback")
            time.sleep(1.0)
            continue

        count = 0
        for a in links:
            href = a.get("href", "")
            if is_valid_url(href) and "nguoichannuoi.vn" in href:
                results.append({
                    "url": href.strip(),
                    "source_name": "Người Chăn nuôi",
                    "published_at": None,
                })
                count += 1

        if not count:
            print(f"  [NguoiChanNuoi] Hết trang {page}")
            break

        print(f"  [NguoiChanNuoi] Trang {page}: {count} links")
        time.sleep(1.0)

    return results


# ============================================================
# 8. CỤC THÚ Y  (thuy.gov.vn)  — nguồn MỚI (RSS + scrape)
# ============================================================
def crawl_thuy(keyword: str = "", max_pages: int = 3) -> list[dict]:
    """
    Cục Thú y: nguồn chính thức về dịch bệnh động vật.
    Dùng RSS feed + scrape trang tin tức trực tiếp.
    keyword không dùng vì site không có search — lấy toàn bộ tin mới.
    """
    results = []
    BASE = "https://www.thuy.gov.vn"

    # Thử RSS
    rss_urls = [
        f"{BASE}/feed/",
        f"{BASE}/rss.xml",
        f"{BASE}/tin-tuc/feed/",
    ]
    for rss_url in rss_urls:
        rss_items = _crawl_rss(rss_url, "Cục Thú y", "thuy.gov.vn")
        if rss_items:
            results.extend(rss_items)
            break

    # Nếu RSS không có, scrape trang tin tức
    if not results:
        news_sections = [
            "/tin-tuc-su-kien",
            "/dich-benh",
            "/kiem-dich-dong-vat",
        ]
        for section in news_sections:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break

                soup = BeautifulSoup(html, "html.parser")
                links = (
                    soup.select(".views-row a")
                    or soup.select("article h3 a")
                    or soup.select(".news-title a")
                    or soup.select(".field-content a")
                )

                found = 0
                for a in links:
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if is_valid_url(href) and "thuy.gov.vn" in href:
                        results.append({
                            "url": href.strip(),
                            "source_name": "Cục Thú y",
                            "published_at": None,
                        })
                        found += 1

                if not found:
                    break
                print(f"  [CucThuy] {section} trang {page}: {found} links")
                time.sleep(1.0)

    return results


# ============================================================
# 9. CỤC BẢO VỆ THỰC VẬT  (bvtv.gov.vn)  — nguồn MỚI
# ============================================================
def crawl_cucbvtv(keyword: str = "", max_pages: int = 3) -> list[dict]:
    """
    Cục BVTV: nguồn chính thức về sâu bệnh cây trồng.
    Dùng RSS + scrape trang tin tức/cảnh báo dịch hại.
    """
    results = []
    BASE = "https://bvtv.gov.vn"

    # Thử RSS
    rss_urls = [
        f"{BASE}/feed/",
        f"{BASE}/rss.xml",
        f"{BASE}/tin-tuc/feed/",
    ]
    for rss_url in rss_urls:
        rss_items = _crawl_rss(rss_url, "Cục BVTV", "bvtv.gov.vn")
        if rss_items:
            results.extend(rss_items)
            break

    if not results:
        news_sections = [
            "/tin-tuc-su-kien",
            "/canh-bao-dich-hai",
            "/kiem-dich-thuc-vat",
        ]
        for section in news_sections:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break

                soup = BeautifulSoup(html, "html.parser")
                links = (
                    soup.select(".views-row a")
                    or soup.select("article h3 a")
                    or soup.select(".news-title a")
                    or soup.select("h3.title a")
                )

                found = 0
                for a in links:
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if is_valid_url(href) and "bvtv.gov.vn" in href:
                        results.append({
                            "url": href.strip(),
                            "source_name": "Cục BVTV",
                            "published_at": None,
                        })
                        found += 1

                if not found:
                    break
                print(f"  [CucBVTV] {section} trang {page}: {found} links")
                time.sleep(1.0)

    return results


# ============================================================
# 10. TẠP CHÍ BẢO VỆ THỰC VẬT  (tapchibaovethucvat.vn)  — cập nhật
# ============================================================
def crawl_baovethucvat(keyword: str, max_pages: int = 3) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://tapchibaovethucvat.vn/?s={keyword_encoded}&paged={page}"
        html = fetch_url(url)
        if not html:
            break

        soup  = BeautifulSoup(html, "html.parser")
        links = (
            soup.select("h2.entry-title a")
            or soup.select("h3.entry-title a")
            or soup.select(".post-title a")
            or soup.select("article h3 a")
        )

        if not links:
            print(f"  [BVTV] Hết trang {page}")
            break

        count = 0
        for a in links:
            href = a.get("href", "")
            if is_valid_url(href) and "tapchibaovethucvat.vn" in href:
                results.append({
                    "url": href.strip(),
                    "source_name": "Tạp chí BVTV",
                    "published_at": None,
                })
                count += 1

        if not count:
            print(f"  [BVTV] Hết trang {page}")
            break

        print(f"  [BVTV] Trang {page}: {count} links")
        time.sleep(1.0)

    return results


# ============================================================
# 11. BÁO SỨC KHOẺ  (suckhoedoisong.vn RSS + bacsituvan.net)  — nguồn MỚI
# ============================================================
def crawl_suckhoe_rss() -> list[dict]:
    """
    Lấy tin từ RSS của Sức khỏe & Đời sống (nhanh và ổn định hơn scrape).
    """
    rss_feeds = [
        ("https://suckhoedoisong.vn/rss/phong-chong-dich-benh.rss",   "Sức khỏe & Đời sống"),
        ("https://suckhoedoisong.vn/rss/suc-khoe.rss",                "Sức khỏe & Đời sống"),
        ("https://suckhoedoisong.vn/rss/y-te.rss",                    "Sức khỏe & Đời sống"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        items = _crawl_rss(rss_url, name, "suckhoedoisong.vn")
        results.extend(items)
        time.sleep(0.5)
    return results


def crawl_vnexpress_rss() -> list[dict]:
    """
    VnExpress RSS cho các chuyên mục sức khỏe — tốc độ nhanh, không bị rate limit.
    """
    rss_feeds = [
        ("https://vnexpress.net/rss/suc-khoe.rss",         "VnExpress"),
        ("https://vnexpress.net/rss/suc-khoe/tin-tuc.rss", "VnExpress"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        items = _crawl_rss(rss_url, name, "vnexpress.net")
        results.extend(items)
        time.sleep(0.5)
    return results


def crawl_nongnghiep_rss() -> list[dict]:
    """Nông nghiệp VN RSS cho chuyên mục chăn nuôi / BVTV."""
    rss_feeds = [
        ("https://nongnghiep.vn/chan-nuoi-thu-y.rss",      "Nông nghiệp Việt Nam"),
        ("https://nongnghiep.vn/bao-ve-thuc-vat.rss",      "Nông nghiệp Việt Nam"),
        ("https://nongnghiep.vn/thi-truong.rss",           "Nông nghiệp Việt Nam"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        items = _crawl_rss(rss_url, name, "nongnghiep.vn")
        results.extend(items)
        time.sleep(0.5)
    return results


# ============================================================
# GET ARTICLE CONTENT  (newspaper3k + BeautifulSoup fallback)
# ============================================================

# CSS selector chuyên biệt theo domain
_DOMAIN_CONTENT_SELECTORS: dict[str, str] = {
    "vnexpress.net":          "article.fck_detail, .sidebar-1 p",
    "dantri.com.vn":          "div.singular-content, .dt-news__content",
    "suckhoedoisong.vn":      "div.detail-content, .article__body",
    "thanhnien.vn":           "div.detail-content, .article-body",
    "tuoitre.vn":             "div#main-detail-body, .article-body",
    "nongnghiep.vn":          "div.article__body, .content-detail",
    "nguoichannuoi.vn":       "div.entry-content",
    "tapchibaovethucvat.vn":  "div.entry-content",
    "thuy.gov.vn":            "div.field-body, .node__content",
    "bvtv.gov.vn":            "div.field-body, .node__content",
}


def _get_domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1).lower() if m else ""


def get_content(url: str) -> tuple[str | None, str | None]:
    """Lấy nội dung bài báo — newspaper3k trước, fallback BeautifulSoup."""
    try:
        art = Article(url, language="vi")
        art.download()
        art.parse()

        title   = (art.title or "").strip()
        content = (art.text  or "").strip()

        if title and len(content) >= 200:
            return title, content

    except Exception:
        pass

    return fallback_get_content(url)


def fallback_get_content(url: str) -> tuple[str | None, str | None]:
    """BeautifulSoup fallback với selector chuyên biệt theo domain."""
    try:
        html = fetch_url(url)
        if not html:
            return None, None

        soup   = BeautifulSoup(html, "html.parser")
        domain = _get_domain(url)

        # Xóa noise
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", ".ads", ".advertisement", ".related"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else ""

        # Thử selector domain-specific trước
        content_text = ""
        for d, sel in _DOMAIN_CONTENT_SELECTORS.items():
            if d in domain:
                container = soup.select_one(sel)
                if container:
                    content_text = container.get_text(separator=" ", strip=True)
                    break

        # Fallback: lấy tất cả thẻ <p>
        if len(content_text) < 200:
            paragraphs   = soup.find_all("p")
            content_text = " ".join(p.get_text(separator=" ").strip() for p in paragraphs)

        content_text = " ".join(content_text.split())  # normalize whitespace

        if len(content_text) >= 200:
            return title, content_text

    except Exception:
        pass

    return None, None