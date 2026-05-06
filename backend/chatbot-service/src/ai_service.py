import requests
from openai import OpenAI
from src.config import OPENAI_API_KEY, GATEWAY_URL

client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# CALL API GATEWAY
# =========================
def get_context(question):
    try:
        res = requests.get(
            GATEWAY_URL,
            params={"question": question},
            timeout=5
        )

        print("👉 CALL GATEWAY:", res.status_code)

        return res.json()

    except Exception as e:
        print("❌ Lỗi gọi gateway:", e)
        return []


# =========================
# INTENT
# =========================
def detect_intent(question):
    q = question.lower()

    if "ở đâu" in q or "thành phố" in q:
        return "LOCATION"
    if "bao nhiêu" in q or "số ca" in q:
        return "STATS"
    if "nguy hiểm" in q or "mức độ" in q:
        return "RISK"

    return "GENERAL"


# =========================
# EXTRACT DISEASE
# =========================
def extract_disease(question, rows):
    q = question.lower()

    for r in rows:
        name = (r.get("disease_name") or "").lower()
        if name and name in q:
            return name

    return None


# =========================
# HANDLE SIMPLE
# =========================
def handle_simple(question, rows):
    intent = detect_intent(question)
    disease = extract_disease(question, rows)

    if not disease:
        return None

    if intent == "LOCATION":
        locations = list(set([
            r.get("location") for r in rows if r.get("location")
        ]))
        return f"Dịch {disease} xuất hiện tại: {', '.join(locations)}"

    if intent == "STATS":
        infected = sum([r.get("cases_infected") or 0 for r in rows])
        dead = sum([r.get("cases_dead") or 0 for r in rows])
        recovered = sum([r.get("cases_recovered") or 0 for r in rows])

        return (
            f"Dịch {disease} có:\n"
            f"- Ca nhiễm: {infected}\n"
            f"- Tử vong: {dead}\n"
            f"- Hồi phục: {recovered}"
        )

    if intent == "RISK":
        risks = list(set([
            r.get("risk_level") for r in rows if r.get("risk_level")
        ]))
        return f"Mức độ rủi ro của {disease}: {', '.join(risks)}"

    return None


# =========================
# AI FALLBACK
# =========================
def build_context(rows):
    context = ""
    for i, r in enumerate(rows, 1):
        context += f"""
{i}. {r.get("title")}
- Dịch bệnh: {r.get("disease_name")}
- Khu vực: {r.get("location")}
- Ca nhiễm: {r.get("cases_infected")}
"""
    return context


def ask_ai(question, rows):
    context = build_context(rows)

    prompt = f"""
Dữ liệu:
{context}

Câu hỏi:
{question}

Yêu cầu:
- Trả lời đúng dữ liệu
- Không bịa
- Ngắn gọn
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Bạn là chatbot dịch bệnh."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return res.choices[0].message.content


def generate_answer(question):
    rows = get_context(question)

    # 1. Nếu có DB → xử lý
    if rows:
        simple = handle_simple(question, rows)
        if simple:
            return simple

        # fallback AI có context
        return ask_ai(question, rows)

    # 2. Nếu KHÔNG có DB → vẫn gọi AI (QUAN TRỌNG)
    return ask_ai_no_context(question)

def ask_ai_no_context(question):
    prompt = f"""
Câu hỏi: {question}

Yêu cầu:
- Trả lời bằng kiến thức chung
- Ngắn gọn, dễ hiểu
- Nếu là bệnh → mô tả triệu chứng + nguyên nhân
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Bạn là chuyên gia về dịch bệnh."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    return res.choices[0].message.content