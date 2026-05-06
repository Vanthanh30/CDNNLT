from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_summary(stats, start_date, end_date):
    prompt = f"""
Bạn là chuyên gia dịch tễ học.

Dữ liệu tuần:
- Thời gian: {start_date} → {end_date}
- Tổng bài: {stats['total_articles']}
- Ca nhiễm: {stats['total_cases']}
- Tử vong: {stats['total_dead']}

Top bệnh:
{stats['top_diseases']}

Top khu vực:
{stats['top_regions']}

Risk:
{stats['risk_stats']}

Yêu cầu:
1. Viết tóm tắt chuyên nghiệp (5-7 dòng)
2. Nhận định xu hướng dịch
3. Đưa ra cảnh báo (nếu có)
4. Viết bằng tiếng Việt, giọng báo cáo

KHÔNG liệt kê, viết dạng đoạn văn.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content

print("API KEY:", OPENAI_API_KEY)