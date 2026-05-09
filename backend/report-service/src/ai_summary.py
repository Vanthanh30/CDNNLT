def _format_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _format_number(value):
    return f"{int(value or 0):,}".replace(",", ".")


def _format_ranked_items(items, unit):
    if not items:
        return "chưa có dữ liệu"

    parts = []
    for name, value in items[:5]:
        parts.append(f"{name} {_format_number(value)} {unit}")

    if len(parts) == 1:
        return parts[0]

    return ", ".join(parts[:-1]) + " và " + parts[-1]


def _dominant_risk(risk_stats):
    if not risk_stats:
        return "LOW"
    return max(risk_stats, key=risk_stats.get)


def _format_risk_level(value):
    labels = {
        "LOW": "thấp",
        "MEDIUM": "trung bình",
        "HIGH": "cao",
        "CRITICAL": "rất cao",
    }
    return labels.get(str(value or "").upper(), str(value or "không xác định"))


def build_synced_summary(stats, start_date, end_date):
    disease_cases = stats.get("top_disease_cases", [])
    region_cases = stats.get("top_region_cases", [])
    dominant_risk = _format_risk_level(_dominant_risk(stats.get("risk_stats", {})))

    disease_text = _format_ranked_items(disease_cases, "ca")
    region_text = _format_ranked_items(region_cases, "ca")

    return (
        f"Trong tuần từ ngày {_format_date(start_date)} đến {_format_date(end_date)}, "
        f"hệ thống ghi nhận {_format_number(stats.get('total_cases'))} ca nhiễm "
        f"trên tổng số {_format_number(stats.get('total_articles'))} bài báo cáo, "
        f"với {_format_number(stats.get('total_dead'))} ca tử vong. "
        f"Các bệnh dịch nổi bật theo số ca gồm {disease_text}. "
        f"Các khu vực ghi nhận số ca cao nhất gồm {region_text}. "
        f"Mức rủi ro xuất hiện nhiều nhất trong dữ liệu tuần này là {dominant_risk}, "
        f"vì vậy cần ưu tiên theo dõi các nhóm bệnh và địa bàn có số ca cao nhất trong bảng thống kê."
    )


def generate_ai_summary(stats, start_date, end_date):
    return build_synced_summary(stats, start_date, end_date)
