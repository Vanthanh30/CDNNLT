"""
spiders.py - Thu thập bài báo dịch bệnh từ nhiều nguồn tại Việt Nam
Nguồn: VnExpress, DanTri, Sức khỏe & Đời sống, Nông nghiệp VN,
       Người Chăn nuôi, Tạp chí BVTV, Cục Thú y, Cục BVTV

THAY ĐỔI:
  - Fix published_at: parse date từ JSON-LD, meta tags, og:tags, time tags
  - Tăng tốc get_content: ThreadPoolExecutor, timeout giảm xuống 10s
  - VnExpress: parse date từ JSON-LD (chuẩn nhất)
  - DanTri: fix logic stop/skip, parse date từ time[datetime]
  - Tất cả spider: fallback date từ URL pattern (YYYY/MM/DD)
  - RSS feeds: parse date chuẩn RFC-2822 và ISO-8601

BUG FIXES:
  - Bug 1: crawl_suckhoedoisong() — NameError 'hrefs' → dùng hrefs_dates
  - Bug 2: crawl_nongnghiep()     — NameError 'hrefs' → dùng hrefs_dates
  - Bug 3: crawl_thuy()           — NameError 'items' → dùng 'links'
  - Bug 4: crawl_cucbvtv()        — NameError 'items' → dùng 'links'
  - Bug 5: _parse_iso_date()      — hàm không tồn tại → thay bằng _parse_iso()
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 10
CONTENT_TIMEOUT = 12


CRAWL_YEARS = 10
_DATE_MIN = datetime(2016, 1, 1)
_DATE_MAX_DELTA = timedelta(days=1)


def get_date_range(years: int = CRAWL_YEARS):
    """Trả về (from_date, to_date) — mặc định 10 năm."""
    to_date = datetime.now()
    from_date = to_date - timedelta(days=years * 365)
    return from_date, to_date


def _parse_iso(s: str) -> str | None:
    """Parse ISO-8601 / RFC-3339: 2025-05-10T14:30:00+07:00"""
    if not s:
        return None
    try:
        s = s.strip().replace("Z", "+00:00")
        s_clean = re.sub(r"[+-]\d{2}:\d{2}$", "", s)
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(s_clean, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _parse_rfc2822(s: str) -> str | None:
    """Parse RFC-2822: Wed, 10 May 2025 14:30:00 +0700"""
    if not s:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return (
            parsedate_to_datetime(s.strip())
            .replace(tzinfo=None)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception:
        return None


def _parse_vn_date(s: str) -> str | None:
    """Parse ngày tiếng Việt: 10/05/2025, 10-05-2025, ngày 10 tháng 5 năm 2025"""
    if not s:
        return None
    m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    m = re.search(
        r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", s, re.IGNORECASE
    )
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    return None


def _parse_date_from_url(url: str) -> str | None:
    """Trích ngày từ URL pattern: /2025/05/10/ hoặc -20250510.htm"""
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    m = re.search(r"[-_](\d{4})(\d{2})(\d{2})[.\-_]", url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    m = re.search(r"/(\d{4})-(\d{2})-(\d{2})", url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    return None


def extract_date_from_html(html: str, url: str = "") -> str | None:
    """
    Thử lần lượt các nguồn date trong HTML:
    1. JSON-LD datePublished (chuẩn nhất - VnExpress, báo lớn dùng)
    2. <meta property="article:published_time">
    3. <meta name="pubdate"> / <meta name="date">
    4. <time datetime="...">
    5. URL pattern
    """
    if not html:
        return _parse_date_from_url(url)

    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json

            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0] if data else {}
            pub = data.get("datePublished") or data.get("dateCreated") or ""
            result = _parse_iso(pub)
            if result:
                return result
        except Exception:
            pass
    for attr_name, attr_val in [
        ("property", "article:published_time"),
        ("property", "og:updated_time"),
        ("name", "pubdate"),
        ("name", "date"),
        ("name", "DC.date"),
        ("itemprop", "datePublished"),
    ]:
        tag = soup.find("meta", attrs={attr_name: attr_val})
        if tag:
            content = tag.get("content", "")
            result = _parse_iso(content) or _parse_vn_date(content)
            if result:
                return result

    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        result = _parse_iso(time_tag["datetime"])
        if result:
            return result

    return _parse_date_from_url(url)


def fetch_url(url: str, retries: int = 2, timeout: int = REQUEST_TIMEOUT) -> str | None:
    for i in range(retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=timeout)
            res.raise_for_status()
            res.encoding = res.apparent_encoding or "utf-8"
            return res.text
        except Exception as e:
            if i < retries - 1:
                time.sleep(1.5**i)
    return None


_BAD_URL_PATTERNS = [
    "/video",
    "/infographic",
    "/photo",
    "/gallery",
    "/clip",
    "/tag/",
    "/chu-de/",
    "/tac-gia/",
    "/category/",
    ".jpg",
    ".png",
    ".gif",
    ".mp4",
    ".webp",
    "javascript:",
    "#",
    "mailto:",
    "facebook.com",
    "youtube.com",
    "twitter.com",
]


def is_valid_url(url: str) -> bool:
    if not url or len(url) < 10:
        return False
    return not any(p in url.lower() for p in _BAD_URL_PATTERNS)


def _crawl_rss(rss_url: str, source_name: str, domain_filter: str = "") -> list[dict]:
    results = []
    html = fetch_url(rss_url)
    if not html:
        return results

    soup = BeautifulSoup(html, "xml")
    items = soup.find_all("item") or soup.find_all("entry")

    for item in items:
        link_tag = item.find("link")
        href = ""
        if link_tag:
            href = link_tag.get_text(strip=True) or link_tag.get("href", "")
        if (
            not href
            or (domain_filter and domain_filter not in href)
            or not is_valid_url(href)
        ):
            continue

        pub_date = None
        pub_tag = (
            item.find("pubDate")
            or item.find("published")
            or item.find("updated")
            or item.find("dc:date")
        )
        if pub_tag:
            raw = pub_tag.get_text(strip=True)
            pub_date = _parse_rfc2822(raw) or _parse_iso(raw)

        results.append(
            {
                "url": href.strip(),
                "source_name": source_name,
                "published_at": pub_date,
            }
        )

    print(f"  [{source_name}] RSS: {len(results)} items từ {rss_url}")
    return results


def crawl_vnexpress(keyword: str, max_pages: int = 5) -> list[dict]:
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
        items = soup.select(".item-news")
        if not items:
            items = soup.select("article.item-news-main, article.item-news")

        if not items:
            found = soup.select("h3.title-news a, h2.title-news a")
            if not found:
                print(f"  [VnExpress] Hết trang {page}")
                break
            for a in found:
                href = a.get("href", "")
                if is_valid_url(href):
                    results.append(
                        {
                            "url": href.strip(),
                            "source_name": "VnExpress",
                            "published_at": _parse_date_from_url(href),
                        }
                    )
            print(f"  [VnExpress] Trang {page}: {len(found)} links (fallback)")
            time.sleep(0.5)
            continue

        count = 0
        for item in items:
            a_tag = item.select_one("h3.title-news a, h2.title-news a, .title-news a")
            if not a_tag:
                continue
            href = a_tag.get("href", "")
            if not is_valid_url(href):
                continue
            pub_date = None
            ts = item.get("data-publish-time") or item.select_one("[data-publish-time]")
            if isinstance(ts, str) and ts.isdigit():
                try:
                    pub_date = datetime.fromtimestamp(int(ts)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except Exception:
                    pass
            elif hasattr(ts, "get"):
                raw_ts = ts.get("data-publish-time", "")
                if raw_ts and raw_ts.isdigit():
                    try:
                        pub_date = datetime.fromtimestamp(int(raw_ts)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    except Exception:
                        pass

            if not pub_date:
                pub_date = _parse_date_from_url(href)

            results.append(
                {
                    "url": href.strip(),
                    "source_name": "VnExpress",
                    "published_at": pub_date,
                }
            )
            count += 1

        print(f"  [VnExpress] Trang {page}: {count} links")
        time.sleep(0.5)

    return results


def crawl_dantri(keyword: str, max_pages: int = 5) -> list[dict]:
    from_date, _ = get_date_range()
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = (
            f"https://dantri.com.vn/tim-kiem.htm?keywords={keyword_encoded}&page={page}"
        )
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
            found_count = 0
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://dantri.com.vn" + href
                if re.search(r"dantri\.com\.vn/[a-z\-]+/[a-z0-9\-]+-\d{8,}\.htm", href):
                    if is_valid_url(href):
                        results.append(
                            {
                                "url": href.strip(),
                                "source_name": "DanTri",
                                "published_at": _parse_date_from_url(href),
                            }
                        )
                        found_count += 1
            print(f"  [DanTri] Trang {page}: {found_count} links (fallback)")
            time.sleep(0.5)
            continue

        old_article_count = 0
        for art in articles:
            published_at = None
            time_tag = art.select_one("time[datetime]")
            if time_tag:
                raw_dt = time_tag.get("datetime", "")
                parsed = _parse_iso(raw_dt)
                if parsed:
                    published_at = parsed
                    try:
                        pub_obj = datetime.strptime(parsed[:10], "%Y-%m-%d")
                        if pub_obj < from_date:
                            old_article_count += 1
                            continue
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
                if not published_at:
                    m = re.search(r"-(\d{8})\.htm", href)
                    if m:
                        s = m.group(1)
                        published_at = f"{s[:4]}-{s[4:6]}-{s[6:]} 00:00:00"
                if is_valid_url(href):
                    if not published_at:
                        published_at = _parse_date_from_url(href)
                    results.append(
                        {
                            "url": href.strip(),
                            "source_name": "DanTri",
                            "published_at": published_at,
                        }
                    )

        print(
            f"  [DanTri] Trang {page}: {len(articles)} bài ({old_article_count} quá cũ)"
        )
        time.sleep(0.5)
        if old_article_count == len(articles) and old_article_count > 0:
            print(f"  [DanTri] Toàn trang đều cũ, dừng.")
            break

    return results


def crawl_suckhoedoisong(keyword: str, max_pages: int = 5) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://suckhoedoisong.vn/tim-kiem.html?keyword={keyword_encoded}&page={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        found = soup.select("article.story, div.story, li.story, .search-result-item a")

        hrefs_dates = []
        for el in found:
            a = el.select_one("h3 a, h2 a, .story__heading a") if el.name != "a" else el
            if a:
                href = a.get("href", "")
                if href.startswith("/"):
                    href = "https://suckhoedoisong.vn" + href
                if is_valid_url(href) and "suckhoedoisong.vn" in href:
                    pub_date = None
                    parent = a.find_parent()
                    if parent:
                        t = parent.select_one("time, .story__time, .story__date, .date")
                        if t:
                            raw = t.get("datetime") or t.get_text(strip=True)
                            pub_date = _parse_iso(raw) or _parse_vn_date(raw)
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
        for href, pub_date in hrefs_dates:
            results.append(
                {
                    "url": href.strip(),
                    "source_name": "Sức khỏe & Đời sống",
                    "published_at": pub_date or _parse_date_from_url(href),
                }
            )

        print(f"  [SKDS] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(0.6)

    return results


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
            soup.select("article") or soup.select(".story") or soup.select(".news-item")
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
                pub_date = _parse_iso(raw) or _parse_vn_date(raw)

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

        for href, pub_date in hrefs_dates:
            results.append(
                {
                    "url": href.strip(),
                    "source_name": "Nông nghiệp Việt Nam",
                    "published_at": pub_date or _parse_date_from_url(href),
                }
            )

        print(f"  [NongNghiep] Trang {page}: {len(hrefs_dates)} links")
        time.sleep(0.6)

    return results


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
            count = 0
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"nguoichannuoi\.vn/\d{4}/\d{2}/", href) or re.search(
                    r"nguoichannuoi\.vn/[a-z0-9\-]+/$", href
                ):
                    if is_valid_url(href):
                        results.append(
                            {
                                "url": href.strip(),
                                "source_name": "Người Chăn nuôi",
                                "published_at": _parse_date_from_url(href),
                            }
                        )
                        count += 1
            print(f"  [NguoiChanNuoi] Trang {page}: {count} links (fallback)")
            time.sleep(0.7)
            continue

        count = 0
        for a in links:
            href = a.get("href", "")
            if is_valid_url(href) and "nguoichannuoi.vn" in href:
                results.append(
                    {
                        "url": href.strip(),
                        "source_name": "Người Chăn nuôi",
                        "published_at": _parse_date_from_url(href),
                    }
                )
                count += 1

        if not count:
            print(f"  [NguoiChanNuoi] Hết trang {page}")
            break

        print(f"  [NguoiChanNuoi] Trang {page}: {count} links")
        time.sleep(0.7)

    return results


def crawl_thuy(keyword: str = "", max_pages: int = 3) -> list[dict]:
    results = []
    BASE = "https://www.thuy.gov.vn"

    rss_urls = [f"{BASE}/feed/", f"{BASE}/rss.xml", f"{BASE}/tin-tuc/feed/"]
    for rss_url in rss_urls:
        rss_items = _crawl_rss(rss_url, "Cục Thú y", "thuy.gov.vn")
        if rss_items:
            results.extend(rss_items)
            break

    if not results:
        for section in ["/tin-tuc-su-kien", "/dich-benh"]:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break
                soup = BeautifulSoup(html, "html.parser")
                links = (
                    soup.select(".views-row a")
                    or soup.select("article h3 a")
                    or soup.select(".field-content a")
                )
                found = 0
                for a in links:
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if is_valid_url(href) and "thuy.gov.vn" in href:
                        results.append(
                            {
                                "url": href.strip(),
                                "source_name": "Cục Thú y",
                                "published_at": _parse_date_from_url(href),
                            }
                        )
                        found += 1
                if not found:
                    break
                print(f"  [CucThuy] {section} trang {page}: {found} links")
                time.sleep(0.7)

    return results


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
        for section in ["/tin-tuc-su-kien", "/canh-bao-dich-hai"]:
            for page in range(1, max_pages + 1):
                url = f"{BASE}{section}?page={page}" if page > 1 else f"{BASE}{section}"
                html = fetch_url(url)
                if not html:
                    break
                soup = BeautifulSoup(html, "html.parser")
                links = (
                    soup.select(".views-row a")
                    or soup.select("article h3 a")
                    or soup.select("h3.title a")
                )
                found = 0
                for a in links:
                    href = a.get("href", "")
                    if href.startswith("/"):
                        href = BASE + href
                    if is_valid_url(href) and "bvtv.gov.vn" in href:
                        results.append(
                            {
                                "url": href.strip(),
                                "source_name": "Cục BVTV",
                                "published_at": _parse_date_from_url(href),
                            }
                        )
                        found += 1
                if not found:
                    break
                print(f"  [CucBVTV] {section} trang {page}: {found} links")
                time.sleep(0.7)

    return results


def crawl_baovethucvat(keyword: str, max_pages: int = 3) -> list[dict]:
    results = []
    keyword_encoded = quote_plus(keyword)

    for page in range(1, max_pages + 1):
        url = f"https://tapchibaovethucvat.vn/?s={keyword_encoded}&paged={page}"
        html = fetch_url(url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("article") or soup.select(".post")

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
            if is_valid_url(href) and "tapchibaovethucvat.vn" in href:
                results.append(
                    {
                        "url": href.strip(),
                        "source_name": "Tạp chí BVTV",
                        "published_at": _parse_date_from_url(href),
                    }
                )
                count += 1

        if not count:
            print(f"  [BVTV] Hết trang {page}")
            break

        print(f"  [BVTV] Trang {page}: {count} links")
        time.sleep(0.7)

    return results


def crawl_suckhoe_rss() -> list[dict]:
    rss_feeds = [
        (
            "https://suckhoedoisong.vn/rss/phong-chong-dich-benh.rss",
            "Sức khỏe & Đời sống",
        ),
        ("https://suckhoedoisong.vn/rss/suc-khoe.rss", "Sức khỏe & Đời sống"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "suckhoedoisong.vn"))
    return results


def crawl_vnexpress_rss() -> list[dict]:
    rss_feeds = [
        ("https://vnexpress.net/rss/suc-khoe.rss", "VnExpress"),
        ("https://vnexpress.net/rss/suc-khoe/tin-tuc.rss", "VnExpress"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "vnexpress.net"))
    return results


def crawl_nongnghiep_rss() -> list[dict]:
    rss_feeds = [
        ("https://nongnghiep.vn/chan-nuoi-thu-y.rss", "Nông nghiệp Việt Nam"),
        ("https://nongnghiep.vn/bao-ve-thuc-vat.rss", "Nông nghiệp Việt Nam"),
    ]
    results = []
    for rss_url, name in rss_feeds:
        results.extend(_crawl_rss(rss_url, name, "nongnghiep.vn"))
    return results


_DOMAIN_CONTENT_SELECTORS: dict[str, str] = {
    "vnexpress.net": "article.fck_detail, .sidebar-1 p",
    "dantri.com.vn": "div.singular-content, .dt-news__content",
    "suckhoedoisong.vn": "div.detail-content, .article__body",
    "thanhnien.vn": "div.detail-content, .article-body",
    "tuoitre.vn": "div#main-detail-body, .article-body",
    "nongnghiep.vn": "div.article__body, .content-detail",
    "nguoichannuoi.vn": "div.entry-content",
    "tapchibaovethucvat.vn": "div.entry-content",
    "thuy.gov.vn": "div.field-body, .node__content",
    "bvtv.gov.vn": "div.field-body, .node__content",
}


def _get_domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1).lower() if m else ""


def get_content(url: str) -> tuple[str | None, str | None, str | None]:
    """
    Lấy (title, content, published_at) từ URL bài báo.
    Trả về tuple 3 phần tử (title, content, published_at).
    published_at: "YYYY-MM-DD HH:MM:SS" hoặc None.
    """
    html_text = None
    title = None
    content = None
    pub_date = None

    try:
        art = Article(url, language="vi", request_timeout=CONTENT_TIMEOUT)
        art.download()
        art.parse()

        title = (art.title or "").strip()
        content = (art.text or "").strip()

        if art.publish_date:
            try:
                pub_date = art.publish_date.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        if not pub_date and art.html:
            pub_date = extract_date_from_html(art.html, url)

        if title and len(content) >= 200:
            return title, content, pub_date

        html_text = art.html

    except Exception:
        pass

    t, c, d = fallback_get_content(url, html_text)
    if not pub_date:
        pub_date = d
    return (t or title), (c or content), pub_date


def fallback_get_content(
    url: str, cached_html: str = None
) -> tuple[str | None, str | None, str | None]:
    """BeautifulSoup fallback — trả về (title, content, published_at)."""
    try:
        html = cached_html or fetch_url(url, timeout=CONTENT_TIMEOUT)
        if not html:
            return None, None, None

        soup = BeautifulSoup(html, "html.parser")
        domain = _get_domain(url)

        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "aside",
                ".ads",
                ".advertisement",
                ".related",
            ]
        ):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else ""

        pub_date = extract_date_from_html(html, url)

        content_text = ""
        for d, sel in _DOMAIN_CONTENT_SELECTORS.items():
            if d in domain:
                container = soup.select_one(sel)
                if container:
                    content_text = container.get_text(separator=" ", strip=True)
                    break

        if len(content_text) < 200:
            paragraphs = soup.find_all("p")
            content_text = " ".join(
                p.get_text(separator=" ").strip() for p in paragraphs
            )

        content_text = " ".join(content_text.split())

        if len(content_text) >= 200:
            return title, content_text, pub_date

    except Exception:
        pass

    return None, None, _parse_date_from_url(url)


def get_contents_parallel(
    items: list[dict],
    max_workers: int = 8,
) -> list[dict]:
    """
    Fetch content cho nhiều URL song song.
    Mỗi item dict cần có 'url'. Hàm thêm vào: title, content, published_at.
    Nếu item đã có published_at thì giữ nguyên, chỉ override nếu HTML trả về chuẩn hơn.
    """

    def _fetch(item: dict) -> dict:
        url = item["url"]
        try:
            title, content, pub_from_html = get_content(url)
            item["title"] = title
            item["content"] = content
            if pub_from_html:
                item["published_at"] = pub_from_html
            elif not item.get("published_at"):
                item["published_at"] = _parse_date_from_url(url)
        except Exception as e:
            item["title"] = None
            item["content"] = None
        return item

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch, item): item for item in items}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                results.append(futures[future])

    return results
