from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def is_epidemic_question(question: str) -> bool:
    q = question.lower()

    epidemic_words = [
        "dịch",
        "dịch bệnh",
        "virus",
        "vi khuẩn",
        "ca nhiễm",
        "sốt xuất huyết",
        "cúm",
        "covid",
        "sởi",
        "dịch tả lợn",
        "cúm gia cầm",
        "lở mồm long móng",
        "sâu bệnh",
        "dịch hại",
        "bệnh cây trồng",
    ]

    return any(word in q for word in epidemic_words)


def build_context(rows):
    if not rows:
        return "Không có dữ liệu nội bộ phù hợp."

    context = ""

    for i, r in enumerate(rows, 1):
        context += f"""
{i}. {r.get("title")}
- Link: {r.get("url")}
- Dịch bệnh: {r.get("disease_name")}
- Khu vực: {r.get("location")}
- Ngày sự kiện: {r.get("event_date")}
- Mức độ rủi ro: {r.get("risk_level")}
- Ca nhiễm: {r.get("cases_infected")}
- Tử vong: {r.get("cases_dead")}
- Hồi phục: {r.get("cases_recovered")}
"""

    return context


def ask_ai(question: str, rows):
    if client is None:
        return "Chatbot chưa được cấu hình OPENAI_API_KEY hoặc CHATBOT_OPENAI_API_KEY."

    context = build_context(rows)
    epidemic = is_epidemic_question(question)

    if epidemic:
        system_prompt = """
Bạn là chatbot hỗ trợ hệ thống giám sát dịch bệnh.
Bạn được phép dùng dữ liệu nội bộ được cung cấp và kiến thức chung.
Nếu dữ liệu nội bộ có thông tin phù hợp, hãy ưu tiên dữ liệu nội bộ.
Nếu dữ liệu nội bộ không đủ, hãy bổ sung kiến thức chung.
Không bịa số liệu. Nếu không có số liệu thì nói chưa có số liệu trong hệ thống.
Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu.
"""
        user_prompt = f"""
Dữ liệu nội bộ:
{context}

Câu hỏi người dùng:
{question}

Yêu cầu:
- Trả lời liên quan dịch bệnh.
- Nếu có dữ liệu nội bộ thì nêu rõ bệnh, khu vực, mức độ rủi ro, số ca nếu có.
- Nếu hỏi kiến thức chung như "dịch tả lợn là gì" thì giải thích thêm bằng kiến thức chung.
"""
    else:
        system_prompt = """
Bạn là trợ lý AI thân thiện.
Bạn có thể trả lời câu hỏi thông thường, chào hỏi, giải thích kiến thức phổ thông.
Nếu câu hỏi không liên quan dịch bệnh thì trả lời bình thường.
Trả lời bằng tiếng Việt, ngắn gọn.
"""
        user_prompt = question

    res = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )

    return res.choices[0].message.content


def generate_answer(question: str, rows=None):
    rows = rows or []
    return ask_ai(question, rows)
