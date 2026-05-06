import os
from collections import Counter
from datetime import date, timedelta

from ai_summary import generate_ai_summary

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String, Rect


from database import get_articles_in_range, save_weekly_report


# ========================
# CONFIG
# ========================
REPORT_FOLDER = "reports"

FONT_PATH = "fonts/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))

styles = getSampleStyleSheet()

for s in styles.byName.values():
    s.fontName = "DejaVu"

styles.add(ParagraphStyle(
    name="TitleCenter",
    parent=styles["Title"],
    alignment=1,
    fontSize=18,
    spaceAfter=10
))

styles.add(ParagraphStyle(
    name="SectionTitle",
    parent=styles["Heading2"],
    textColor=colors.HexColor("#2c3e50"),
    spaceAfter=8
))

styles.add(ParagraphStyle(
    name="NormalCustom",
    parent=styles["Normal"],
    fontSize=10,
    leading=14
))


# ========================
# CHARTS
# ========================
def create_bar_chart(data_pairs):
    if not data_pairs:
        return Paragraph("Không có dữ liệu", styles["NormalCustom"])

    drawing = Drawing(450, 240)

    labels = [str(k)[:10] for k, _ in data_pairs]
    data = [[v for _, v in data_pairs]]

    bc = VerticalBarChart()
    bc.x = 60
    bc.y = 50
    bc.height = 140
    bc.width = 330

    bc.data = data
    bc.categoryAxis.categoryNames = labels

    bc.categoryAxis.labels.fontName = "DejaVu"
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle = 30

    bc.valueAxis.labels.fontName = "DejaVu"
    bc.valueAxis.labels.fontSize = 8

    bc.valueAxis.valueMin = 0

    bc.bars[0].fillColor = colors.HexColor("#3498db")

    drawing.add(bc)
    return drawing

from reportlab.graphics.shapes import Drawing, String

def create_pie_chart(risk_stats):
    if not risk_stats:
        return Paragraph("Không có dữ liệu", styles["NormalCustom"])

    drawing = Drawing(450, 220)

    pie = Pie()
    pie.x = 200
    pie.y = 40

    data = list(risk_stats.values())
    labels = list(risk_stats.keys())

    pie.data = data
    pie.labels = None

    pie.slices.strokeWidth = 0.5

    color_map = {
        "LOW": colors.HexColor("#2ecc71"),     # xanh đẹp
        "MEDIUM": colors.HexColor("#f39c12"),  # vàng cam
        "HIGH": colors.HexColor("#e74c3c")     # đỏ
    }

    total = sum(data)

    for i, key in enumerate(labels):
        pie.slices[i].fillColor = color_map.get(key, colors.grey)

    drawing.add(pie)

    # legend đẹp
    y_pos = 170
    for i, key in enumerate(labels):
        value = data[i]
        percent = (value / total * 100) if total else 0
        color = color_map.get(key, colors.grey)

        drawing.add(Rect(30, y_pos, 12, 12, fillColor=color, strokeWidth=0))

        text = f"{key}: {value} ({percent:.1f}%)"

        drawing.add(String(
            50, y_pos,
            text,
            fontName="DejaVu",
            fontSize=10
        ))

        y_pos -= 20

    return drawing

# ========================
# ANALYZE DATA
# ========================
def analyze_data(rows):
    disease_counter = Counter()
    disease_cases = Counter()

    region_counter = Counter()
    region_cases = Counter()

    risk_counter = Counter()

    total_cases = 0
    total_dead = 0
    article_ids = []

    for r in rows:
        article_ids.append(r["article_id"])

        disease = r.get("disease")
        region = r.get("location")

        cases = r.get("cases_infected") or 0
        dead = r.get("cases_dead") or 0
        risk = r.get("risk_level") or "LOW"

        if disease:
            disease_counter[disease] += 1
            disease_cases[disease] += cases

        if region:
            region_counter[region] += 1
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
        "top_regions": region_counter.most_common(5),
        "top_region_cases": region_cases.most_common(5),
        "risk_stats": risk_counter,
        "article_ids": article_ids
    }


# ========================
# SUMMARY
# ========================
def build_summary(stats, start_date, end_date):
    return f"""
Báo cáo từ {start_date} đến {end_date}

Tổng số bài viết: {stats['total_articles']}
Tổng ca nhiễm: {stats['total_cases']}
Tổng ca tử vong: {stats['total_dead']}
"""


# ========================
# TABLE
# ========================
def create_table(data):
    table = Table(data, hAlign="CENTER")

    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("ALIGN", (1, 1), (-1, -1), "CENTER"),

        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))

    return table


# ========================
# PDF
# ========================
def generate_pdf(summary_text, stats, filename):
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)

    path = os.path.join(REPORT_FOLDER, filename)

    doc = SimpleDocTemplate(
        path,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    story = []

    # TITLE
    story.append(Paragraph("BÁO CÁO DỊCH BỆNH TUẦN", styles["TitleCenter"]))
    story.append(Spacer(1, 15))

    # SUMMARY BOX
    story.append(Paragraph("TÓM TẮT", styles["SectionTitle"]))

    for line in summary_text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), styles["NormalCustom"]))
            story.append(Spacer(1, 5))

    story.append(Spacer(1, 15))

    # 🔥 RISK
    story.append(Paragraph("PHÂN BỐ RỦI RO", styles["SectionTitle"]))

    risk_data = [["Mức độ", "Số bài"]]
    for k, v in stats["risk_stats"].items():
        risk_data.append([k, str(v)])

    story.append(create_table(risk_data))
    story.append(Spacer(1, 10))
    story.append(create_pie_chart(stats["risk_stats"]))
    story.append(Spacer(1, 20))

    # 🔥 DISEASE
    story.append(Paragraph("TOP BỆNH", styles["SectionTitle"]))

    data = [["Bệnh", "Số bài"]]
    for d, c in stats["top_diseases"]:
        data.append([d, str(c)])

    story.append(create_table(data))
    story.append(Spacer(1, 10))
    story.append(create_bar_chart(stats["top_diseases"]))
    story.append(Spacer(1, 20))

    # 🔥 REGION
    story.append(Paragraph("TOP KHU VỰC", styles["SectionTitle"]))

    data = [["Khu vực", "Số bài"]]
    for r, c in stats["top_regions"]:
        data.append([r, str(c)])

    story.append(create_table(data))
    story.append(Spacer(1, 10))
    story.append(create_bar_chart(stats["top_regions"]))
    story.append(Spacer(1, 20))

    # FOOTER
    story.append(Paragraph(
        "Báo cáo được tạo tự động từ hệ thống phân tích dữ liệu.",
        styles["Italic"]
    ))

    doc.build(story)
    return path


# ========================
# MAIN
# ========================
def generate_weekly_report():
    today = date.today()
    start_date = today - timedelta(days=7)
    end_date = today

    rows = get_articles_in_range(start_date, end_date)

    if not rows:
        return None

    stats = analyze_data(rows)

    try:
        summary = generate_ai_summary(stats, start_date, end_date)
    except Exception:
        summary = build_summary(stats, start_date, end_date)

    filename = f"weekly_{start_date}_{end_date}.pdf"
    pdf_path = generate_pdf(summary, stats, filename)

    save_weekly_report(
        start_date,
        end_date,
        summary,
        stats["total_articles"],
        pdf_path,
        stats["article_ids"]
    )

    return pdf_path, filename