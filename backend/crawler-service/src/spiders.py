"""
spiders.py - Thu thập bài báo dịch bệnh từ nhiều nguồn tại Việt Nam
Nguồn hiện tại (10 nguồn):
  Người  : VnExpress, DanTri, Sức khỏe & Đời sống, Báo Sức khỏe (bacsituvan.vn),
            Báo Thanh Niên, Báo Tuổi Trẻ
  Động vật: Báo Nông nghiệp VN, Người Chăn nuôi, Cục Thú y (thuy.gov.vn)
  Cây trồng: Cục BVTV (bvtv.gov.vn), Tạp chí BVTV

THAY ĐỔI SO VỚI PHIÊN BẢN CŨ:
  - Thêm _scrape_publish_date(): scrape ngày từ meta tags / JSON-LD / URL regex
  - Thêm _parse_iso_date(): parse ISO 8601 → chuỗi 'YYYY-MM-DD HH:MM:SS'
  - get_content() giờ trả về tuple (title, content, publish_date)
  - fallback_get_content() cũng trả về (title, content, publish_date)
  - _crawl_rss() cải thiện parse ngày: thử nhiều format hơn
  - Tất cả spider crawl_* trả về published_at từ trang danh sách nếu có
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin
from email.utils import parsedate_to_datetime


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
# DATE RANGE & VALIDATION
# ========================

# Cào 10 năm để phục vụ tính năng lọc theo ngày/tháng/năm
CRAWL_YEARS     = 10
_DATE_MIN       = datetime(2016, 1, 1)   # chặn epoch 1970, bài cổ
_DATE_MAX_DELTA = timedelta(days=1)      # cho phép lệch timezone 1 ngày


def get_date_range(years: int = CRAWL_YEARS):
    """Trả về (from_date, to_date) — mặc định 10 năm."""
    to_date   = datetime.now()
    from_date = to_date - timedelta(days=years * 365)
    return from_date, to_date


def _is_date_in_range(dt: datetime) -> bool:
    """
    Trả về True nếu ngày hợp lệ:
      - >= 2016-01-01  (chặn timestamp 1970, bài cổ vô nghĩa)
      - <= now + 1 ngày (chặn ngày tương lai do lỗi timezone)
    KHÔNG giới hạn 30 ngày — cào đủ 10 năm.
    """
    now = datetime.now()
    if dt < _DATE_MIN:
        return False
    if dt > now + _DATE_MAX_DELTA:
        return False
    return True


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
            time.sleep(2 ** i)
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
# DATE HELPERS
# ========================

def _parse_iso_date(raw: str) -> str | None:
    """
    Parse ISO 8601 / RFC 2822 / partial date → 'YYYY-MM-DD HH:MM:SS'.
    Sau khi parse sẽ kiểm tra _is_date_in_range():
      - Loại bỏ ngày 1970 (timestamp lỗi), quá cũ (>30 ngày), tương lai
    Trả về None nếu không parse được hoặc ngoài khoảng cho phép.
    """
    if not raw:
        return None
    raw = raw.strip()

    dt = None

    # ISO 8601 với timezone (2026-05-09T10:30:00+07:00 hoặc ...Z)
    if dt is None:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            dt = dt.replace(tzinfo=None)
        except Exception:
            pass

    # RFC 2822 (Fri, 09 May 2026 10:30:00 +0700)
    if dt is None:
        try:
            dt = parsedate_to_datetime(raw).replace(tzinfo=None)
        except Exception:
            pass

    # Chỉ có ngày YYYY-MM-DD
    if dt is None:
        m = re.match(r"^(\d{4}-\d{2}-\d{2})$", raw)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d")
            except Exception:
                pass

    # DD/MM/YYYY
    if dt is None:
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", raw)
        if m:
            try:
                dt = datetime.strptime(
                    f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "%Y-%m-%d"
                )
            except Exception:
                pass

    if dt is None:
        return None

    # ── Validate: loại bỏ ngày 1970, quá cũ, tương lai ──
    if not _is_date_in_range(dt):
        return None

    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Meta tag selectors theo thứ tự ưu tiên
_DATE_META_SELECTORS = [
    ('meta[property="article:published_time"]', "content"),
    ('meta[name="pubdate"]',                    "content"),
    ('meta[name="publishdate"]',                "content"),
    ('meta[name="publish_date"]',               "content"),
    ('meta[itemprop="datePublished"]',          "content"),
    ('meta[property="og:updated_time"]',        "content"),
    ('[itemprop="datePublished"]',              "datetime"),  # <time> tag
    ('[itemprop="datePublished"]',              "content"),
]


def _scrape_publish_date(url: str, html: str | None = None) -> str | None:
    """
    Scrape published_at từ meta tags / JSON-LD / URL path của trang bài báo.
    Nhận html đã fetch (tái dùng) hoặc tự fetch nếu html=None.
    Trả về 'YYYY-MM-DD HH:MM:SS' hoặc None.
    """
    try:
        if html is None:
            html = fetch_url(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # ── 1. Meta tags ──
        for selector, attr in _DATE_META_SELECTORS:
            tag = soup.select_one(selector)
            if tag and tag.get(attr):
                result = _parse_iso_date(tag[attr])
                if result:
                    return result

        # ── 2. JSON-LD ──
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0] if data else {}
                for field in ("datePublished", "dateCreated", "dateModified"):
                    val = data.get(field)
                    if val:
                        result = _parse_iso_date(val)
                        if result:
                            return result
            except Exception:
                pass

        # ── 3. <time> tags phổ biến ──
        for time_tag in soup.find_all("time"):
            dt_attr = time_tag.get("datetime") or time_tag.get("content")
            if dt_attr:
                result = _parse_iso_date(dt_attr)
                if result:
                    return result

        # ── 4. Regex từ URL path: /YYYY/MM/DD/ hoặc /YYYYMMDD ──
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})[/\-]", url)
        if m:
            result = _parse_iso_date(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
            if result:
                return result
        m = re.search(r"[_\-/](\d{8})[\-_/.]", url)
        if m:
            s = m.group(1)
            result = _parse_iso_date(f"{s[:4]}-{s[4:6]}-{s[6:]}")
            if result:
                return result

    except Exception:
        pass
    return None


# ========================
# RSS HELPER
# ========================
def _crawl_rss(rss_url: str, source_name: str, domain_filter: str = "") -> list[dict]:
    """
    Lấy bài báo từ RSS feed. Trả về list dict {url, source_name, published_at}.
    Cải thiện: thử nhiều format ngày hơn qua _parse_iso_date.
    """
    results = []
    html = fetch_url(rss_url)
    if not html:
        return results

    soup  = BeautifulSoup(html, "xml")
    items = soup.find_all("item") or soup.find_all("entry")

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
        pub_tag  = (
            item.find("pubDate")
            or item.find("published")
            or item.find("updated")
            or item.find("dc:date")
        )
        if pub_tag:
            pub_date = _parse_iso_date(pub_tag.get_text(strip=True))

        results.append({
            "url":          href.strip(),
            "source_name":  source_name,
            "published_at": pub_date,
        })

    print(f"  [{source_name}] RSS: {len(results)} items từ {rss_url}")
    return results


# ============================================================
# GET ARTICLE CONTENT  (newspaper3k + BeautifulSoup fallback)
# Trả về (title, content, publish_date) thay vì (title, content)
# ============================================================

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


def get_content(url: str) -> tuple[str | None, str | None, str | None]:
    """
    Lấy nội dung bài báo.
    Trả về (title, content, publish_date).
    publish_date là chuỗi 'YYYY-MM-DD HH:MM:SS' hoặc None.
    """
    html_cache = None
    pub_date   = None

    # ── Thử newspaper3k trước ──
    try:
        art = Article(url, language="vi")
        art.download()
        art.parse()

        title   = (art.title or "").strip()
        content = (art.text  or "").strip()

        # Lấy publish_date từ newspaper3k
        if art.publish_date:
            pub_date = art.publish_date.strftime("%Y-%m-%d %H:%M:%S")

        # Lấy HTML đã download để tái dùng cho _scrape_publish_date
        try:
            html_cache = art.html
        except Exception:
            pass

        if title and len(content) >= 200:
            # Nếu newspaper chưa lấy được ngày, thử scrape từ HTML
            if not pub_date and html_cache:
                pub_date = _scrape_publish_date(url, html_cache)
            return title, content, pub_date

    except Exception:
        pass

    return fallback_get_content(url)


def fallback_get_content(url: str) -> tuple[str | None, str | None, str | None]:
    """
    BeautifulSoup fallback với selector chuyên biệt theo domain.
    Trả về (title, content, publish_date).
    """
    try:
        html = fetch_url(url)
        if not html:
            return None, None, None

        soup   = BeautifulSoup(html, "html.parser")
        domain = _get_domain(url)

        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", ".ads", ".advertisement", ".related"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else ""

        content_text = ""
        for d, sel in _DOMAIN_CONTENT_SELECTORS.items():
            if d in domain:
                container = soup.select_one(sel)
                if container:
                    content_text = container.get_text(separator=" ", strip=True)
                    break

        if len(content_text) < 200:
            paragraphs   = soup.find_all("p")
            content_text = " ".join(p.get_text(separator=" ").strip() for p in paragraphs)

        content_text = " ".join(content_text.split())

        # Scrape publish_date từ HTML đã fetch (tái dùng html, không fetch lại)
        pub_date = _scrape_publish_date(url, html)

        if len(content_text) >= 200:
            return title, content_text, pub_date

    except Exception:
        pass

    return None, None, None


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
            if not is_valid_url(href):
                continue

            # VnExpress: lấy ngày từ URL path /YYYY/MM/DD/
            pub_date = None
            m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", href)
            if m:
                pub_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)} 00:00:00"

            # Thử lấy từ span.time trong kết quả tìm kiếm
            parent = a.find_parent(class_=re.compile(r"item-news"))
            if parent and not pub_date:
                time_el = parent.select_one("span.time, span.date, time")
                if time_el:
                    raw = time_el.get("datetime") or time_el.get_text(strip=True)
                    pub_date = _parse_iso_date(raw)

            results.append({
                "url":          href.strip(),
                "source_name":  "VnExpress",
                "published_at": pub_date,
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

    for page in range(1, max_pages + 1):
        url = f"https://dantri.com.vn/tim-kiem.htm?keywords={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            url = f"https://dantri.com.vn/tim-kiem.htm?q={keyword_encoded}&page={page}"
            html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        articles = (
            soup.select("article.article-item")
            or soup.select("div.article-item")
            or soup.select(".news-item")
            or soup.select("article[data-id]")
        )

        if not articles:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://dantri.com.vn" + href
                if re.search(r"dantri\.com\.vn/[a-z\-]+/[a-z0-9\-]+-\d{8,}\.htm", href):
                    if is_valid_url(href):
                        # Lấy ngày từ URL: -YYYYMMDD.htm
                        pub_date = None
                        m = re.search(r"-(\d{8})\.htm", href)
                        if m:
                            s = m.group(1)
                            pub_date = f"{s[:4]}-{s[4:6]}-{s[6:]} 00:00:00"
                        results.append({
                            "url":          href.strip(),
                            "source_name":  "DanTri",
                            "published_at": pub_date,
                        })
            print(f"  [DanTri] Trang {page}: fallback links")
            time.sleep(0.8)
            continue

        stop = False
        for art in articles:
            published_at = None
            time_tag = art.select_one("time")
            if time_tag:
                raw = time_tag.get("datetime") or time_tag.get_text(strip=True)
                parsed = _parse_iso_date(raw)
                if parsed:
                    try:
                        pub_dt = datetime.strptime(parsed[:10], "%Y-%m-%d")
                        if pub_dt < from_date:
                            stop = True
                            break
                    except Exception:
                        pass
                    published_at = parsed

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
                # Fallback ngày từ URL nếu chưa có
                if not published_at:
                    m = re.search(r"-(\d{8})\.htm", href)
                    if m:
                        s = m.group(1)
                        published_at = f"{s[:4]}-{s[4:6]}-{s[6:]} 00:00:00"
                if is_valid_url(href):
                    results.append({
                        "url":          href.strip(),
                        "source_name":  "DanTri",
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

        hrefs_dates = []
        for el in found:
            a = el.select_one("h3 a, h2 a, .story__heading a") if el.name != "a" else el
            if a:
                href = a.get("href", "")
                if href.startswith("/"):
                    href = "https://suckhoedoisong.vn" + href
                if is_valid_url(href) and "suckhoedoisong.vn" in href:
                    # Lấy ngày từ element cha
                    pub_date = None
                    parent   = a.find_parent()
                    if parent:
                        t = parent.select_one("time, .story__time, .story__date, .date")
                        if t:
                            raw = t.get("datetime") or t.get_text(strip=True)
                            pub_date = _parse_iso_date(raw)
                    hrefs_dates.append((href, pub_date))

        if not hrefs_dates:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://suckhoedoisong.vn" + href
                if "suckhoedoisong.vn" in href and is_valid_url(href):
                    if re.search(r"-n\d{5,}\.htm", href):
                        hrefs_dates.append((href, None))

        if not hrefs_dates:
            print(f"  [SKDS] Hết trang {page}")
            break

        seen = set()
        for href, pub_date in hrefs_dates:
            if href not in seen:
                seen.add(href)
                results.append({
                    "url":          href.strip(),
                    "source_name":  "Sức khỏe & Đời sống",
                    "published_at": pub_date,
                })

        print(f"  [SKDS] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(1.0)

    return results


# ============================================================
# 4. BÁO THANH NIÊN  (thanhnien.vn)
# ============================================================
def crawl_thanhnien(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://thanhnien.vn/tim-kiem/?q={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        items = (
            soup.select(".box-category-item")
            or soup.select(".story")
            or soup.select("article")
        )

        hrefs_dates = []
        for item in items:
            a = (
                item.select_one("h3 a")
                or item.select_one("h2 a")
                or item.select_one(".story__heading a")
                or item.select_one(".item--title a")
            )
            if not a:
                continue
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://thanhnien.vn" + href
            if not (is_valid_url(href) and "thanhnien.vn" in href):
                continue

            pub_date = None
            t = item.select_one("time, .story__time, .box-category-item__time, .date")
            if t:
                raw = t.get("datetime") or t.get("content") or t.get_text(strip=True)
                pub_date = _parse_iso_date(raw)

            # Fallback: lấy từ URL -185XXXXXXXXX.htm  (timestamp ms trong tên file)
            if not pub_date:
                m = re.search(r"-185(\d{7,})\.htm", href)
                if m:
                    try:
                        ts_ms = int("185" + m.group(1))
                        dt    = datetime.fromtimestamp(ts_ms / 1000)
                        # Validate trước khi dùng
                        if _is_date_in_range(dt):
                            pub_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

            hrefs_dates.append((href, pub_date))

        if not hrefs_dates:
            # Fallback regex
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://thanhnien.vn" + href
                if re.search(r"thanhnien\.vn/[a-z0-9\-]+/[a-z0-9\-]+-185\d+\.htm", href):
                    hrefs_dates.append((href, None))

        if not hrefs_dates:
            print(f"  [ThanhNien] Hết trang {page}")
            break

        seen = set()
        for href, pub_date in hrefs_dates:
            if href not in seen:
                seen.add(href)
                results.append({
                    "url":          href.strip(),
                    "source_name":  "Thanh Niên",
                    "published_at": pub_date,
                })

        print(f"  [ThanhNien] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(0.9)

    return results


# ============================================================
# 5. BÁO TUỔI TRẺ  (tuoitre.vn)
# ============================================================
def crawl_tuoitre(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://tuoitre.vn/tim-kiem?q={keyword_encoded}&p={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        items = (
            soup.select(".news-item")
            or soup.select(".search-result li")
            or soup.select("article")
        )

        hrefs_dates = []
        for item in items:
            a = (
                item.select_one("h3 a")
                or item.select_one("h2 a")
                or item.select_one(".title-news a")
                or item.select_one("a.title")
            )
            if not a:
                continue
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://tuoitre.vn" + href
            if not (is_valid_url(href) and "tuoitre.vn" in href):
                continue

            pub_date = None
            t = item.select_one("time, .date, .news-item__time")
            if t:
                raw = t.get("datetime") or t.get_text(strip=True)
                pub_date = _parse_iso_date(raw)

            # Fallback: timestamp giây trong URL -XXXXXXXXXX.htm
            if not pub_date:
                m = re.search(r"-(\d{10})\.htm", href)
                if m:
                    try:
                        dt = datetime.fromtimestamp(int(m.group(1)))
                        # Validate: tránh timestamp 1970 hoặc quá cũ
                        if _is_date_in_range(dt):
                            pub_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

            hrefs_dates.append((href, pub_date))

        if not hrefs_dates:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://tuoitre.vn" + href
                if re.search(r"tuoitre\.vn/[a-z0-9\-]+-\d{10,}\.htm", href):
                    hrefs_dates.append((href, None))

        if not hrefs_dates:
            print(f"  [TuoiTre] Hết trang {page}")
            break

        seen = set()
        for href, pub_date in hrefs_dates:
            if href not in seen:
                seen.add(href)
                results.append({
                    "url":          href.strip(),
                    "source_name":  "Tuổi Trẻ",
                    "published_at": pub_date,
                })

        print(f"  [TuoiTre] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(0.9)

    return results


# ============================================================
# 6. BÁO NÔNG NGHIỆP VIỆT NAM  (nongnghiep.vn)
# ============================================================
def crawl_nongnghiep(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://nongnghiep.vn/tim-kiem/?keyword={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            url = f"https://nongnghiep.vn/tim-kiem/?s={keyword_encoded}&page={page}"
            html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")

        items = (
            soup.select("article")
            or soup.select(".story")
            or soup.select(".news-item")
        )

        hrefs_dates = []
        for item in items:
            a = (
                item.select_one("h2.story__heading a")
                or item.select_one("h3.story__heading a")
                or item.select_one(".article-title a")
                or item.select_one("h3 a")
                or item.select_one("h2 a")
            )
            if not a:
                continue
            href = a.get("href", "")
            if href.startswith("/"):
                href = "https://nongnghiep.vn" + href
            if not (is_valid_url(href) and "nongnghiep.vn" in href):
                continue

            pub_date = None
            t = item.select_one("time, .story__time, .date, .post-date")
            if t:
                raw = t.get("datetime") or t.get_text(strip=True)
                pub_date = _parse_iso_date(raw)

            hrefs_dates.append((href, pub_date))

        if not hrefs_dates:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://nongnghiep.vn" + href
                if re.search(r"nongnghiep\.vn/[a-z0-9\-]+(?:-d\d+)?\.html?", href):
                    if is_valid_url(href):
                        hrefs_dates.append((href, None))

        if not hrefs_dates:
            print(f"  [NongNghiep] Hết trang {page}")
            break

        seen = set()
        for href, pub_date in hrefs_dates:
            if href not in seen:
                seen.add(href)
                results.append({
                    "url":          href.strip(),
                    "source_name":  "Nông nghiệp Việt Nam",
                    "published_at": pub_date,
                })

        print(f"  [NongNghiep] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(1.0)

    return results


# ============================================================
# 7. NGƯỜI CHĂN NUÔI  (nguoichannuoi.vn)
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

        items = (
            soup.select("article")
            or soup.select(".post")
        )

        hrefs_dates = []
        for item in items:
            a = (
                item.select_one("h2.entry-title a")
                or item.select_one("h3.entry-title a")
                or item.select_one(".post-title a")
                or item.select_one("h3 a")
            )
            if not a:
                continue
            href = a.get("href", "")
            if not (is_valid_url(href) and "nguoichannuoi.vn" in href):
                continue

            pub_date = None
            t = item.select_one("time.entry-date, time, .post-date")
            if t:
                raw = t.get("datetime") or t.get_text(strip=True)
                pub_date = _parse_iso_date(raw)

            hrefs_dates.append((href, pub_date))

        if not hrefs_dates:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"nguoichannuoi\.vn/\d{4}/\d{2}/", href) or \
                   re.search(r"nguoichannuoi\.vn/[a-z0-9\-]+/$", href):
                    if is_valid_url(href):
                        # Lấy ngày từ URL path /YYYY/MM/
                        pub_date = None
                        m = re.search(r"/(\d{4})/(\d{2})/", href)
                        if m:
                            pub_date = f"{m.group(1)}-{m.group(2)}-01 00:00:00"
                        hrefs_dates.append((href, pub_date))
            print(f"  [NguoiChanNuoi] Trang {page}: fallback")
            time.sleep(1.0)
            if not hrefs_dates:
                break
            for href, pub_date in hrefs_dates:
                results.append({
                    "url":          href.strip(),
                    "source_name":  "Người Chăn nuôi",
                    "published_at": pub_date,
                })
            continue

        for href, pub_date in hrefs_dates:
            results.append({
                "url":          href.strip(),
                "source_name":  "Người Chăn nuôi",
                "published_at": pub_date,
            })

        print(f"  [NguoiChanNuoi] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(1.0)

    return results


# ============================================================
# 8. CỤC THÚ Y  (thuy.gov.vn)
# ============================================================
def crawl_thuy(keyword: str = "", max_pages: int = 3) -> list[dict]:
    results = []
    BASE = "https://www.thuy.gov.vn"

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

    if not results:
        news_sections = ["/tin-tuc-su-kien", "/dich-benh", "/kiem-dich-dong-vat"]
        for section in news_sections:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break

                soup = BeautifulSoup(html, "html.parser")
                items = (
                    soup.select(".views-row")
                    or soup.select("article")
                    or soup.select(".news-title")
                )

                found = 0
                for item in items:
                    a = item.select_one("a") if item.name != "a" else item
                    if not a:
                        continue
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if not (is_valid_url(href) and "thuy.gov.vn" in href):
                        continue

                    pub_date = None
                    t = item.select_one("time, .date, .views-field-created")
                    if t:
                        raw = t.get("datetime") or t.get_text(strip=True)
                        pub_date = _parse_iso_date(raw)

                    results.append({
                        "url":          href.strip(),
                        "source_name":  "Cục Thú y",
                        "published_at": pub_date,
                    })
                    found += 1

                if not found:
                    break
                print(f"  [CucThuy] {section} trang {page}: {found} links")
                time.sleep(1.0)

    return results


# ============================================================
# 9. CỤC BẢO VỆ THỰC VẬT  (bvtv.gov.vn)
# ============================================================
def crawl_cucbvtv(keyword: str = "", max_pages: int = 3) -> list[dict]:
    results = []
    BASE = "https://bvtv.gov.vn"

    rss_urls = [f"{BASE}/feed/", f"{BASE}/rss.xml", f"{BASE}/tin-tuc/feed/"]
    for rss_url in rss_urls:
        rss_items = _crawl_rss(rss_url, "Cục BVTV", "bvtv.gov.vn")
        if rss_items:
            results.extend(rss_items)
            break

    if not results:
        news_sections = ["/tin-tuc-su-kien", "/canh-bao-dich-hai", "/kiem-dich-thuc-vat"]
        for section in news_sections:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break

                soup = BeautifulSoup(html, "html.parser")
                items = (
                    soup.select(".views-row")
                    or soup.select("article")
                    or soup.select(".news-title")
                )

                found = 0
                for item in items:
                    a = item.select_one("a") if item.name != "a" else item
                    if not a:
                        continue
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if not (is_valid_url(href) and "bvtv.gov.vn" in href):
                        continue

                    pub_date = None
                    t = item.select_one("time, .date, .views-field-created")
                    if t:
                        raw = t.get("datetime") or t.get_text(strip=True)
                        pub_date = _parse_iso_date(raw)

                    results.append({
                        "url":          href.strip(),
                        "source_name":  "Cục BVTV",
                        "published_at": pub_date,
                    })
                    found += 1

                if not found:
                    break
                print(f"  [CucBVTV] {section} trang {page}: {found} links")
                time.sleep(1.0)

    return results


# ============================================================
# 10. TẠP CHÍ BẢO VỆ THỰC VẬT  (tapchibaovethucvat.vn)
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
        items = (
            soup.select("article")
            or soup.select(".post")
        )

        if not items:
            print(f"  [BVTV] Hết trang {page}")
            break

        count = 0
        for item in items:
            a = (
                item.select_one("h2.entry-title a")
                or item.select_one("h3.entry-title a")
                or item.select_one(".post-title a")
                or item.select_one("h3 a")
            )
            if not a:
                continue
            href = a.get("href", "")
            if not (is_valid_url(href) and "tapchibaovethucvat.vn" in href):
                continue

            pub_date = None
            t = item.select_one("time.entry-date, time, .post-date")
            if t:
                raw = t.get("datetime") or t.get_text(strip=True)
                pub_date = _parse_iso_date(raw)

            results.append({
                "url":          href.strip(),
                "source_name":  "Tạp chí BVTV",
                "published_at": pub_date,
            })
            count += 1

        if not count:
            print(f"  [BVTV] Hết trang {page}")
            break

        print(f"  [BVTV] Trang {page}: {count} links")
        time.sleep(1.0)

    return results


# ============================================================
# 11. RSS FEEDS
# ============================================================
def crawl_suckhoe_rss() -> list[dict]:
    rss_feeds = [
        ("https://suckhoedoisong.vn/rss/phong-chong-dich-benh.rss", "Sức khỏe & Đời sống"),
        ("https://suckhoedoisong.vn/rss/suc-khoe.rss",              "Sức khỏe & Đời sống"),
        ("https://suckhoedoisong.vn/rss/y-te.rss",                  "Sức khỏe & Đời sống"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "suckhoedoisong.vn"))
        time.sleep(0.5)
    return results


def crawl_vnexpress_rss() -> list[dict]:
    rss_feeds = [
        ("https://vnexpress.net/rss/suc-khoe.rss",         "VnExpress"),
        ("https://vnexpress.net/rss/suc-khoe/tin-tuc.rss", "VnExpress"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "vnexpress.net"))
        time.sleep(0.5)
    return results


def crawl_nongnghiep_rss() -> list[dict]:
    rss_feeds = [
        ("https://nongnghiep.vn/chan-nuoi-thu-y.rss",  "Nông nghiệp Việt Nam"),
        ("https://nongnghiep.vn/bao-ve-thuc-vat.rss",  "Nông nghiệp Việt Nam"),
        ("https://nongnghiep.vn/thi-truong.rss",       "Nông nghiệp Việt Nam"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "nongnghiep.vn"))
        time.sleep(0.5)
    return results