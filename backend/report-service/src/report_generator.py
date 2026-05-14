import os
from collections import Counter
from datetime import date, timedelta
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import String, Rect
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from config import *
import mysql.connector

REPORT_RANGE_DAYS = 30

# ========================
# FONT CONFIG (FIX WINDOWS + DEPLOY)
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_SERVICE_DIR = os.path.dirname(BASE_DIR)

FONT_PATH = os.path.join(REPORT_SERVICE_DIR, "fonts", "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(REPORT_SERVICE_DIR, "fonts", "DejaVuSans-Bold.ttf")

if not os.path.exists(FONT_PATH):
    raise Exception(f"Font not found: {FONT_PATH}")

if not os.path.exists(FONT_BOLD_PATH):
    raise Exception(f"Font not found: {FONT_BOLD_PATH}")

pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", FONT_BOLD_PATH))


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )


def init_db():
    conn = get_connection()
    if conn:
        conn.close()
        print("Report service DB connected")
    else:
        raise RuntimeError("Cannot connect DB")


# ========================
# COLOR PALETTE (match Word doc)
# ========================
COLOR_DARK_HEADER = colors.HexColor("#1F3864")  # dark navy – main title bg
COLOR_SECTION_BG = colors.HexColor("#2E74B5")  # blue – section heading bg
COLOR_TABLE_HEADER = colors.HexColor("#34495E")  # dark slate – table header bg
COLOR_TABLE_ROW_ALT = colors.HexColor("#EBF3FB")  # light blue – alternate rows
COLOR_HIGH_RISK = colors.HexColor("#C00000")  # red
COLOR_MED_RISK = colors.HexColor("#ED7D31")  # orange
COLOR_LOW_RISK = colors.HexColor("#70AD47")  # green
COLOR_BORDER = colors.HexColor("#ADB9CA")  # soft border


# ========================
# STYLES
# ========================
def build_styles():
    styles = getSampleStyleSheet()

    custom = {
        # ── Tiêu đề chính (banner trắng trên nền xanh đậm)
        "MainTitle": ParagraphStyle(
            "MainTitle",
            fontName="DejaVu-Bold",
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=0,
        ),
        # ── Dòng phụ dưới tiêu đề (in nghiêng, trắng)
        "SubTitle": ParagraphStyle(
            "SubTitle",
            fontName="DejaVu",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#BDD7EE"),
            spaceAfter=0,
        ),
        # ── Label metadata (Report ID, Period …)
        "MetaLabel": ParagraphStyle(
            "MetaLabel",
            fontName="DejaVu-Bold",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1F3864"),
        ),
        "MetaValue": ParagraphStyle(
            "MetaValue",
            fontName="DejaVu",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#333333"),
        ),
        # ── Section heading (chữ trắng nền xanh, như Word)
        "SectionHeading": ParagraphStyle(
            "SectionHeading",
            fontName="DejaVu-Bold",
            fontSize=11,
            leading=16,
            textColor=colors.white,
            spaceAfter=0,
        ),
        # ── Italic note dưới section heading
        "SectionNote": ParagraphStyle(
            "SectionNote",
            fontName="DejaVu",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#595959"),
            leftIndent=4,
        ),
        # ── Body text thông thường
        "Body": ParagraphStyle(
            "Body",
            fontName="DejaVu",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#222222"),
            alignment=TA_JUSTIFY,
        ),
        # ── Bullet point
        "Bullet": ParagraphStyle(
            "Bullet",
            fontName="DejaVu",
            fontSize=9.5,
            leading=14,
            leftIndent=14,
            bulletIndent=4,
            textColor=colors.HexColor("#222222"),
        ),
        # ── Footer
        "Footer": ParagraphStyle(
            "Footer",
            fontName="DejaVu",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#666666"),
        ),
        "FooterBold": ParagraphStyle(
            "FooterBold",
            fontName="DejaVu-Bold",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F3864"),
        ),
    }
    return custom


# ========================
# HELPER: section heading block (colored banner)
# ========================
def section_heading(text, styles):
    """Return a list of flowables: colored banner + bottom spacer."""
    # Wrap text in a Table cell so we can set background color easily
    tbl = Table([[Paragraph(text, styles["SectionHeading"])]], colWidths=["100%"])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_SECTION_BG),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return [Spacer(1, 12), tbl, Spacer(1, 6)]


# ========================
# HELPER: italic note line
# ========================
def italic_note(text, styles):
    return Paragraph(f"<i>{text}</i>", styles["SectionNote"])


def format_count(value):
    return f"{int(value or 0):,}".replace(",", ".")


def format_date_vi(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def format_risk_level(value):
    labels = {
        "LOW": "Thấp",
        "MEDIUM": "Trung bình",
        "HIGH": "Cao",
        "CRITICAL": "Rất cao",
    }
    return labels.get(str(value or "").upper(), str(value or "Không xác định"))


# ========================
# HEADER BANNER
# ========================
def build_header_banner(report_id, period, gen_date, version, styles):
    """Dark-blue banner with title and metadata table."""
    title_cell = [
        Paragraph("HỆ THỐNG CLINICAL SENTINEL", styles["MainTitle"]),
        Paragraph("BÁO CÁO DỊCH BỆNH HẰNG THÁNG", styles["MainTitle"]),
        Spacer(1, 4),
        Paragraph("Hệ thống giám sát dịch bệnh tự động", styles["SubTitle"]),
    ]

    # Banner background table
    banner = Table([[title_cell]], colWidths=["100%"])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_DARK_HEADER),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
            ]
        )
    )

    # Metadata row (4 cells)
    meta_data = [
        [
            Paragraph("<b>Mã báo cáo:</b>", styles["MetaLabel"]),
            Paragraph(report_id, styles["MetaValue"]),
            Paragraph("<b>Ngày tạo:</b>", styles["MetaLabel"]),
            Paragraph(gen_date, styles["MetaValue"]),
        ],
        [
            Paragraph("<b>Giai đoạn:</b>", styles["MetaLabel"]),
            Paragraph(period, styles["MetaValue"]),
            Paragraph("<b>Phiên bản:</b>", styles["MetaLabel"]),
            Paragraph(version, styles["MetaValue"]),
        ],
    ]
    col_w = [2.5 * cm, 6 * cm, 2.5 * cm, 6 * cm]
    meta_tbl = Table(meta_data, colWidths=col_w)
    meta_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF3FB")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D0D0")),
            ]
        )
    )

    return [
        banner,
        Spacer(1, 6),
        meta_tbl,
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=1.5, color=COLOR_DARK_HEADER),
        Spacer(1, 8),
    ]


# ========================
# SECTION 1 – EXECUTIVE SUMMARY
# ========================
def build_section1(stats, styles):
    items = []
    items += section_heading("1. TÓM TẮT TỔNG QUAN", styles)
    items.append(
        italic_note(
            "Dữ liệu được tổng hợp tự động từ các nguồn tin tức và sự kiện dịch bệnh trong 30 ngày gần nhất.",
            styles,
        )
    )
    items.append(Spacer(1, 6))

    bullets = [
        (
            f"<b>Tổng số bài báo đã xử lý:</b> {format_count(stats.get('total_articles'))} bài viết"
        ),
        (f"<b>Tổng ca nhiễm:</b> {format_count(stats.get('total_cases'))}"),
        (f"<b>Tổng ca tử vong:</b> {format_count(stats.get('total_dead'))}"),
        (
            f"<b>Vùng ảnh hưởng trọng điểm:</b> Đông Nam Á (Việt Nam, Thái Lan), Tây Thái Bình Dương"
        ),
    ]
    for b in bullets:
        items.append(Paragraph(f"• {b}", styles["Bullet"]))

    return items


# ========================
# SECTION 2 – AI SUMMARY
# ========================
def build_section2(ai_text, styles):
    items = []
    items += section_heading("2. TÓM TẮT DỊCH BỆNH TỰ ĐỘNG", styles)
    items.append(
        italic_note(
            "Nội dung được tổng hợp tự động từ dữ liệu bài báo và sự kiện dịch bệnh:",
            styles,
        )
    )
    items.append(Spacer(1, 6))

    # Quoted block – light background
    quote_para = Paragraph(ai_text.strip(), styles["Body"])
    quote_tbl = Table([[quote_para]], colWidths=["100%"])
    quote_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F9FF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_SECTION_BG),
            ]
        )
    )
    items.append(quote_tbl)
    return items


# ========================
# SECTION 3 – STATISTICAL TABLE
# ========================
def build_section3(stats, styles):
    items = []
    items += section_heading("3. PHÂN TÍCH SỐ LIỆU THEO BỆNH", styles)

    chart_data = stats["top_disease_cases"] or stats["top_diseases"]
    metric_label = "Số ca" if stats["top_disease_cases"] else "Số bài"
    rows = [["Bệnh", metric_label]]

    for disease, value in chart_data:
        rows.append([disease, format_count(value)])

    table = build_data_table(rows)
    items.append(table)

    if chart_data:
        items.append(Spacer(1, 10))
        items.append(create_bar_chart(chart_data))

    return items


# ========================
# SECTION 4 – GEOGRAPHIC
# ========================
def build_section4(stats, styles):
    items = []
    items += section_heading("4. PHÂN BỐ ĐỊA LÝ", styles)

    chart_data = stats["top_region_cases"] or stats["top_regions"]
    metric_label = "Số ca" if stats["top_region_cases"] else "Số bài"
    rows = [["Khu vực", metric_label]]

    for region, value in chart_data:
        rows.append([region, format_count(value)])

    table = build_data_table(rows)
    items.append(table)

    if chart_data:
        items.append(Spacer(1, 10))
        items.append(create_bar_chart(chart_data))

    return items


# # ========================
# # SECTION 5 – ARTICLES
# # ========================
# def build_section5(stats, styles):
#     items = []
#     items += section_heading("5. BÀI VIẾT NỔI BẬT", styles)

#     for a in stats["articles"][:5]:
#         items.append(Paragraph(
#             f"• <b>{a['title']}</b> (Rủi ro: {format_risk_level(a['risk'])})",
#             styles["Bullet"]
#         ))

#     return items


# ========================
# SECTION 6 – RECOMMENDATIONS
# ========================
def build_section6(stats, styles):
    items = []
    items += section_heading("5. KHUYẾN NGHỊ HỆ THỐNG", styles)

    risk_stats = stats["risk_stats"]

    if not risk_stats:
        level = "LOW"
    else:
        level = max(risk_stats, key=risk_stats.get)

    items.append(
        Paragraph(
            f"• Mức rủi ro tổng quan: <b>{format_risk_level(level)}</b>",
            styles["Bullet"],
        )
    )

    return items


# ========================
# FOOTER
# ========================
def build_footer(styles):
    items = [
        Spacer(1, 16),
        HRFlowable(width="100%", thickness=1, color=COLOR_DARK_HEADER),
        Spacer(1, 6),
        Paragraph("[Chữ ký điện tử]", styles["FooterBold"]),
        Paragraph("Bộ tạo báo cáo EpiSense", styles["FooterBold"]),
        Paragraph(
            "Báo cáo được tạo tự động từ hệ thống phân tích dữ liệu", styles["Footer"]
        ),
    ]
    return items


# ========================
# CHARTS
# ========================
# ========================
# FIX: BAR CHART (QUAN TRỌNG)
# ========================
def build_data_table(rows):
    table = Table(rows, colWidths=[10 * cm, 5 * cm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, COLOR_TABLE_ROW_ALT],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def create_bar_chart(data_pairs):
    if not data_pairs:
        return Spacer(1, 1)

    drawing = Drawing(460, 200)

    labels = [str(k)[:12] for k, _ in data_pairs]
    data = [[float(v) for _, v in data_pairs]]  # 🔥 FIX Decimal

    bc = VerticalBarChart()
    bc.x = 60
    bc.y = 40
    bc.height = 130
    bc.width = 360

    bc.data = data
    bc.categoryAxis.categoryNames = labels

    bc.categoryAxis.labels.fontName = "DejaVu"
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle = 20

    bc.valueAxis.labels.fontName = "DejaVu"
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = 0

    max_val = max(data[0]) if data[0] else 0
    bc.valueAxis.valueMax = float(max_val) * 1.2 if max_val > 0 else 10

    bc.bars[0].fillColor = COLOR_SECTION_BG

    drawing.add(bc)
    return drawing


def create_pie_chart(risk_stats):
    if not risk_stats:
        return Spacer(1, 1)

    drawing = Drawing(460, 220)
    pie = Pie()
    pie.x = 180
    pie.y = 30
    pie.width = 140
    pie.height = 140
    pie.data = list(risk_stats.values())
    pie.labels = None
    pie.slices.strokeWidth = 0.5

    color_map = {
        "LOW": COLOR_LOW_RISK,
        "MEDIUM": COLOR_MED_RISK,
        "HIGH": COLOR_HIGH_RISK,
    }
    labels = list(risk_stats.keys())
    total = sum(pie.data)

    for i, key in enumerate(labels):
        pie.slices[i].fillColor = color_map.get(key, colors.grey)

    drawing.add(pie)

    y_pos = 170
    for i, key in enumerate(labels):
        value = list(risk_stats.values())[i]
        percent = (value / total * 100) if total else 0
        color = color_map.get(key, colors.grey)
        drawing.add(Rect(20, y_pos, 12, 12, fillColor=color, strokeWidth=0))
        drawing.add(
            String(
                40,
                y_pos,
                f"{format_risk_level(key)}: {value} ({percent:.1f}%)",
                fontName="DejaVu",
                fontSize=9,
            )
        )
        y_pos -= 22

    return drawing


# ========================
# HELPER: inline styles
# ========================
def _tbl_hdr_style():
    return ParagraphStyle(
        "_th",
        fontName="DejaVu-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=TA_CENTER,
    )


def _tbl_cell_style(align=TA_LEFT):
    return ParagraphStyle(
        "_td", fontName="DejaVu", fontSize=9, leading=12, alignment=align
    )


def _hex(color):
    """Convert reportlab Color to hex string (without #)."""
    r = int(color.red * 255)
    g = int(color.green * 255)
    b = int(color.blue * 255)
    return f"{r:02X}{g:02X}{b:02X}"


DISEASE_WEEKLY_CASE_CAPS = {
    "Sốt xuất huyết": 5000,
    "Sốt xuất huyết Dengue": 5000,
    "Tay chân miệng": 5000,
    "COVID-19": 10000,
    "Cúm A": 10000,
    "Cúm B": 10000,
    "Cúm mùa": 10000,
    "Sởi": 5000,
}

DEFAULT_WEEKLY_CASE_CAP = 10000


def sanitize_weekly_cases(disease, cases, title=""):
    cases = int(cases or 0)
    if cases <= 0:
        return 0

    cap = DISEASE_WEEKLY_CASE_CAPS.get(disease, DEFAULT_WEEKLY_CASE_CAP)
    if cases > cap:
        print(
            "Skip abnormal monthly case count: "
            f"{disease or 'unknown'} = {cases} | {title or ''}"
        )
        return 0

    return cases


# ========================
# ANALYZE DATA
# ========================
def analyze_data(rows):
    from collections import Counter, defaultdict

    disease_counter = Counter()
    disease_cases = Counter()
    disease_risk = {}

    region_counter = Counter()
    region_cases = Counter()

    risk_counter = Counter()

    total_cases = 0
    total_dead = 0
    article_ids = []
    articles = []

    for r in rows:
        article_ids.append(r["article_id"])

        disease = r.get("disease")
        region = r.get("location")

        cases = sanitize_weekly_cases(
            disease=r.get("disease"),
            cases=r.get("cases_infected"),
            title=r.get("title"),
        )
        dead = int(r.get("cases_dead") or 0)
        risk = (r.get("risk_level") or "LOW").upper()

        # 👉 lưu article
        articles.append({"title": r.get("title"), "risk": r.get("risk_level") or "LOW"})

        if disease:
            disease_counter[disease] += 1
            if cases > 0:
                disease_cases[disease] += cases
            disease_risk[disease] = risk

        if region:
            region_counter[region] += 1
            if cases > 0:
                region_cases[region] += cases

        risk_counter[risk] += 1

        total_cases += cases
        total_dead += dead

    return {
        "total_articles": len(rows),
        "total_cases": total_cases,
        "total_dead": total_dead,
        "top_diseases": disease_counter.most_common(5),
        "top_disease_cases": disease_cases.most_common(5),
        "disease_risk": disease_risk,
        "top_regions": region_counter.most_common(5),
        "top_region_cases": region_cases.most_common(5),
        "risk_stats": dict(risk_counter),
        "article_ids": article_ids,
        "articles": articles,
    }

    # =========================


# AGGREGATE QUERIES
# =========================


def get_disease_stats(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            d.name AS disease,
            COALESCE(SUM(s.cases_infected), 0) AS total_cases,
            MAX(de.risk_level) AS risk_level
        FROM DISEASE_EVENT de
        JOIN DISEASE d ON d.id = de.disease_id
        LEFT JOIN STATIC s ON s.event_id = de.id
        JOIN ARTICLE a ON a.id = de.article_id
        JOIN RAW_ARTICLE r ON r.id = a.raw_article_id
        WHERE DATE(COALESCE(de.event_date, r.published_at)) BETWEEN %s AND %s
        GROUP BY d.name
        ORDER BY total_cases DESC
        LIMIT 5
    """,
        (start_date, end_date),
    )

    rows = cursor.fetchall()
    for r in rows:
        r["total_cases"] = float(r["total_cases"] or 0)

    cursor.close()
    conn.close()
    return rows


def get_region_stats(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            rg.name AS region,
            COALESCE(SUM(s.cases_infected), 0) AS total_cases
        FROM DISEASE_EVENT de
        JOIN REGION rg ON rg.id = de.region_id
        LEFT JOIN STATIC s ON s.event_id = de.id
        JOIN ARTICLE a ON a.id = de.article_id
        JOIN RAW_ARTICLE r ON r.id = a.raw_article_id
        WHERE DATE(COALESCE(de.event_date, r.published_at)) BETWEEN %s AND %s
        GROUP BY rg.name
        ORDER BY total_cases DESC
        LIMIT 5
    """,
        (start_date, end_date),
    )

    rows = cursor.fetchall()
    for r in rows:
        r["total_cases"] = float(r["total_cases"] or 0)

    cursor.close()
    conn.close()
    return rows


def get_top_articles(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            r.title,
            de.risk_level
        FROM ARTICLE a
        JOIN RAW_ARTICLE r ON r.id = a.raw_article_id
        JOIN DISEASE_EVENT de ON de.article_id = a.id
        WHERE DATE(COALESCE(de.event_date, r.published_at)) BETWEEN %s AND %s
        ORDER BY COALESCE(de.event_date, DATE(r.published_at)) DESC
        LIMIT 5
    """,
        (start_date, end_date),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_risk_stats(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            de.risk_level,
            COUNT(*) AS total
        FROM DISEASE_EVENT de
        JOIN ARTICLE a ON a.id = de.article_id
        JOIN RAW_ARTICLE r ON r.id = a.raw_article_id
        WHERE DATE(COALESCE(de.event_date, r.published_at)) BETWEEN %s AND %s
        GROUP BY de.risk_level
    """,
        (start_date, end_date),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {r["risk_level"]: r["total"] for r in rows}


# ========================
# MAIN PDF GENERATOR
# ========================
def generate_pdf(
    ai_summary_text: str, stats: dict, start_date=None, end_date=None
) -> BytesIO:
    """
    Generate a styled PDF report matching the Word document template.

    Args:
        ai_summary_text: AI-generated paragraph summary.
        stats:           dict from analyze_data().
        start_date:      date object (defaults to the first day of the report range).
        end_date:        date object (defaults to today).

    Returns:
        BytesIO buffer containing the PDF.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=REPORT_RANGE_DAYS - 1)

    report_id = f"#EPI-{end_date.year}-{end_date.month:02d}-M1"
    period = f"{format_date_vi(start_date)} - {format_date_vi(end_date)}"
    gen_date = format_date_vi(end_date)
    version = "v2.5 (kiến trúc vi dịch vụ)"

    styles = build_styles()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = []

    # ── HEADER
    story += build_header_banner(report_id, period, gen_date, version, styles)

    # ── SECTION 1
    story += build_section1(stats, styles)

    # ── SECTION 2
    story += build_section2(ai_summary_text, styles)

    # ── SECTION 3
    story += build_section3(stats, styles)

    # ── SECTION 4
    story += build_section4(stats, styles)

    # # ── SECTION 5
    # story += build_section5(stats, styles)

    # ── SECTION 6
    story += build_section6(stats, styles)

    # ── FOOTER
    story += build_footer(styles)

    doc.build(story)
    buffer.seek(0)
    return buffer


# ========================
# ENTRY POINT
# ========================
def generate_monthly_report():
    """Wrapper that fetches DB data and calls generate_pdf."""
    from database import get_articles_in_range, save_weekly_report
    from ai_summary import generate_ai_summary

    today = date.today()
    end_date = today
    start_date = end_date - timedelta(days=REPORT_RANGE_DAYS - 1)

    rows = get_articles_in_range(start_date, end_date)
    if not rows:
        return None

    stats = analyze_data(rows)

    try:
        summary = generate_ai_summary(stats, start_date, end_date)
    except Exception:
        summary = (
            f"Báo cáo từ {format_date_vi(start_date)} đến {format_date_vi(end_date)}.\n"
            f"Tổng số bài viết: {format_count(stats['total_articles'])}. "
            f"Tổng ca nhiễm: {format_count(stats['total_cases'])}. "
            f"Tổng ca tử vong: {format_count(stats['total_dead'])}."
        )

    pdf_buffer = generate_pdf(summary, stats, start_date, end_date)
    filename = f"monthly_{start_date}_{end_date}.pdf"
    report_id = save_weekly_report(
        start_date=start_date,
        end_date=end_date,
        summary_text=summary,
        total_articles=stats["total_articles"],
        pdf_url=None,
        article_ids=stats["article_ids"],
    )
    print(f"Saved WEEKLY_REPORT: {report_id}")

    pdf_buffer.seek(0)
    return pdf_buffer, filename


def generate_weekly_report():
    return generate_monthly_report()
