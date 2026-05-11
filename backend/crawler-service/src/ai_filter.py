import json
import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
    shared_env = Path(__file__).resolve().parents[2] / "report-service" / ".env"
    if shared_env.exists():
        load_dotenv(shared_env, override=False)
except Exception:
    pass

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MIN_CONFIDENCE = float(os.getenv("AI_FILTER_MIN_CONFIDENCE", "0.7"))


DISEASE_TERMS = [
    "dịch bệnh", "ổ dịch", "bùng phát", "ca nhiễm", "ca mắc", "ca tử vong",
    "truyền nhiễm", "lây nhiễm", "virus", "vi khuẩn", "vi rút",
    "sốt xuất huyết", "tay chân miệng", "sởi", "cúm", "covid-19",
    "dịch tả", "bệnh dại", "đậu mùa khỉ", "bạch hầu", "ho gà",
    "dịch tả lợn", "cúm gia cầm", "lở mồm long móng", "tai xanh",
    "dịch hại", "sâu bệnh", "bệnh hại", "rầy nâu", "đạo ôn",
]

ECONOMY_TERMS = [
    "kinh tế", "thị trường", "giá cả", "giá heo", "giá lợn", "giá gạo",
    "chứng khoán", "cổ phiếu", "doanh nghiệp", "lợi nhuận", "doanh thu",
    "xuất khẩu", "nhập khẩu", "thương mại", "đầu tư", "du lịch",
    "bất động sản", "ngân hàng", "lãi suất", "tăng trưởng",
]


def get_filter_status() -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "keyword_fallback: chưa có OPENAI_API_KEY"
    if OpenAI is None:
        return "openai_error: thiếu package openai"
    return f"openai: model={AI_MODEL}, min_confidence={MIN_CONFIDENCE}"


def _normalize(text: str) -> str:
    text = (text or "").lower()
    return re.sub(r"\s+", " ", text).strip()


def _has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _fallback_classify(title: str, content: str) -> dict:
    text = _normalize(f"{title}. {content}")
    has_disease = _has_any(text, DISEASE_TERMS)
    has_economy = _has_any(text, ECONOMY_TERMS)

    is_relevant = has_disease and not (has_economy and text.find("dịch") > text.find("kinh tế"))
    return {
        "is_relevant": is_relevant,
        "confidence": 0.75 if is_relevant else 0.8,
        "primary_topic": "dịch bệnh" if is_relevant else "không phù hợp",
        "category": "fallback",
        "method": "keyword_fallback",
        "reason": "Lọc dự phòng bằng từ khóa vì chưa cấu hình OpenAI.",
    }


def _openai_error_result(reason: str) -> dict:
    return {
        "is_relevant": False,
        "confidence": 0,
        "primary_topic": "không xác định",
        "category": "irrelevant",
        "method": "openai_error",
        "reason": reason,
    }


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text or "", flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def classify_article(title: str, content: str) -> dict:
    """
    Trả về kết quả lọc bài báo.
    is_relevant=True chỉ khi chủ đề chính là dịch bệnh/sự kiện bệnh truyền nhiễm
    ở người, vật nuôi hoặc cây trồng; loại các bài kinh tế/thị trường là trọng tâm.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_classify(title, content)

    if OpenAI is None:
        return _openai_error_result(
            "OPENAI_API_KEY đã có nhưng chưa cài package openai. "
            "Chạy lại pip install -r requirements.txt hoặc rebuild container crawler."
        )

    text = re.sub(r"\s+", " ", f"{title or ''}\n{content or ''}").strip()[:7000]
    client = OpenAI(api_key=api_key, timeout=25)

    system_prompt = (
        "Bạn là bộ lọc dữ liệu báo chí cho hệ thống giám sát dịch bệnh tại Việt Nam. "
        "Chỉ chọn bài có chủ đề chính là dịch bệnh, ổ dịch, bệnh truyền nhiễm ở người, "
        "dịch bệnh vật nuôi, hoặc dịch hại/bệnh hại cây trồng. "
        "Loại bỏ bài có chủ đề chính là kinh tế, thị trường, giá cả, chứng khoán, "
        "doanh nghiệp, xuất nhập khẩu, du lịch, hoặc tác động kinh tế, dù bài có nhắc đến dịch bệnh. "
        "Loại bỏ bệnh không truyền nhiễm như ung thư, tim mạch, tiểu đường nếu không có ổ dịch."
    )
    user_prompt = (
        "Phân loại bài báo sau. Trả về JSON hợp lệ với các trường: "
        "is_relevant boolean, confidence number từ 0 đến 1, primary_topic string, "
        "category một trong human/animal/plant/irrelevant, reason string ngắn.\n\n"
        f"Tiêu đề: {title or ''}\n"
        f"Nội dung: {text}"
    )

    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = _extract_json(response.choices[0].message.content)
        confidence = float(data.get("confidence") or 0)
        is_relevant = bool(data.get("is_relevant")) and confidence >= MIN_CONFIDENCE
        return {
            "is_relevant": is_relevant,
            "confidence": confidence,
            "primary_topic": data.get("primary_topic", ""),
            "category": data.get("category", "irrelevant"),
            "method": "openai",
            "reason": data.get("reason", ""),
        }
    except Exception as exc:
        return _openai_error_result(f"Lỗi gọi OpenAI: {exc}")
