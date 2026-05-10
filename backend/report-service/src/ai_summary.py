try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from config import OPENAI_API_KEY, OPENAI_MODEL


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


def _build_fact_block(stats, start_date, end_date):
    disease_cases = stats.get("top_disease_cases", [])
    region_cases = stats.get("top_region_cases", [])
    dominant_risk = _format_risk_level(_dominant_risk(stats.get("risk_stats", {})))

    return "\n".join([
        f"Giai đoạn: {_format_date(start_date)} đến {_format_date(end_date)}",
        f"Tổng bài báo: {_format_number(stats.get('total_articles'))}",
        f"Tổng ca nhiễm: {_format_number(stats.get('total_cases'))}",
        f"Tổng ca tử vong: {_format_number(stats.get('total_dead'))}",
        f"Bệnh nổi bật theo số ca: {_format_ranked_items(disease_cases, 'ca')}",
        f"Khu vực nổi bật theo số ca: {_format_ranked_items(region_cases, 'ca')}",
        f"Mức rủi ro xuất hiện nhiều nhất: {dominant_risk}",
    ])


def _generate_with_gpt(stats, start_date, end_date):
    if not OPENAI_API_KEY or OpenAI is None:
        return None

    client = OpenAI(api_key=OPENAI_API_KEY, timeout=30)
    fact_block = _build_fact_block(stats, start_date, end_date)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên viên viết báo cáo giám sát dịch bệnh bằng tiếng Việt. "
                    "Chỉ được dùng đúng số liệu trong phần DỮ LIỆU ĐÃ XÁC THỰC. "
                    "Không được tự thêm bệnh, khu vực, số ca, tỷ lệ, nhận định định lượng "
                    "hoặc mốc thời gian không có trong dữ liệu."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Viết một đoạn tóm tắt báo cáo dịch bệnh chuyên nghiệp, 4-6 câu, "
                    "giọng văn hành chính rõ ràng. Không dùng gạch đầu dòng.\n\n"
                    "DỮ LIỆU ĐÃ XÁC THỰC:\n"
                    f"{fact_block}"
                ),
            },
        ],
    )

    return response.choices[0].message.content.strip()


def generate_ai_summary(stats, start_date, end_date):
    try:
        summary = _generate_with_gpt(stats, start_date, end_date)
        if summary:
            return summary
    except Exception as exc:
        print(f"⚠️ Không gọi được GPT để tóm tắt báo cáo: {exc}")

    return build_synced_summary(stats, start_date, end_date)
