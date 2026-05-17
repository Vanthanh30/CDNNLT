"""
nlp_engine.py - Trích xuất thông tin từ bài báo dịch bệnh Việt Nam
Chiến lược: STRICT WHITELIST-ONLY
- Region: chỉ chấp nhận đúng 63 tỉnh/thành trong PROVINCE_MAP, KHÔNG có fallback regex
- Disease: chỉ chấp nhận tên bệnh có trong KNOWN_DISEASE_MAP, regex fallback bị loại bỏ
- Cả hai field đều phải pass is_valid_* trước khi lưu DB
"""

import re
import unicodedata


def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return text.lower().strip()


def _wm(keyword: str, text: str) -> bool:
    """
    Word-boundary match cho tiếng Việt.
    Dùng lookahead/lookbehind để tránh match một phần từ.
    VD: "an giang" không match trong "an toàn giang hồ" nếu có space boundary.
    """
    escaped = re.escape(keyword)
    pattern = (
        r"(?:^|[\s,.\-/\(\)\[\]:;\"'])" + escaped + r"(?=$|[\s,.\-/\(\)\[\]:;\"'])"
    )
    return bool(re.search(pattern, text))


PROVINCE_MAP: dict[str, str] = {
    "hà nội": "Hà Nội",
    "hải phòng": "Hải Phòng",
    "quảng ninh": "Quảng Ninh",
    "hải dương": "Hải Dương",
    "hưng yên": "Hưng Yên",
    "thái bình": "Thái Bình",
    "nam định": "Nam Định",
    "ninh bình": "Ninh Bình",
    "hà nam": "Hà Nam",
    "vĩnh phúc": "Vĩnh Phúc",
    "bắc ninh": "Bắc Ninh",
    "bắc giang": "Bắc Giang",
    "lạng sơn": "Lạng Sơn",
    "cao bằng": "Cao Bằng",
    "bắc kạn": "Bắc Kạn",
    "thái nguyên": "Thái Nguyên",
    "tuyên quang": "Tuyên Quang",
    "hà giang": "Hà Giang",
    "lào cai": "Lào Cai",
    "yên bái": "Yên Bái",
    "phú thọ": "Phú Thọ",
    "sơn la": "Sơn La",
    "điện biên": "Điện Biên",
    "lai châu": "Lai Châu",
    "hòa bình": "Hòa Bình",
    "thanh hóa": "Thanh Hóa",
    "nghệ an": "Nghệ An",
    "hà tĩnh": "Hà Tĩnh",
    "quảng bình": "Quảng Bình",
    "quảng trị": "Quảng Trị",
    "thừa thiên huế": "Thừa Thiên Huế",
    "thừa thiên - huế": "Thừa Thiên Huế",
    "tỉnh thừa thiên huế": "Thừa Thiên Huế",
    "tt-huế": "Thừa Thiên Huế",
    "đà nẵng": "Đà Nẵng",
    "quảng nam": "Quảng Nam",
    "quảng ngãi": "Quảng Ngãi",
    "bình định": "Bình Định",
    "phú yên": "Phú Yên",
    "khánh hòa": "Khánh Hòa",
    "ninh thuận": "Ninh Thuận",
    "bình thuận": "Bình Thuận",
    "kon tum": "Kon Tum",
    "gia lai": "Gia Lai",
    "đắk lắk": "Đắk Lắk",
    "đắk nông": "Đắk Nông",
    "lâm đồng": "Lâm Đồng",
    "tp hcm": "TP. Hồ Chí Minh",
    "tp.hcm": "TP. Hồ Chí Minh",
    "tphcm": "TP. Hồ Chí Minh",
    "thành phố hồ chí minh": "TP. Hồ Chí Minh",
    "hồ chí minh": "TP. Hồ Chí Minh",
    "bình dương": "Bình Dương",
    "đồng nai": "Đồng Nai",
    "bà rịa vũng tàu": "Bà Rịa - Vũng Tàu",
    "bà rịa - vũng tàu": "Bà Rịa - Vũng Tàu",
    "bình phước": "Bình Phước",
    "tây ninh": "Tây Ninh",
    "long an": "Long An",
    "tiền giang": "Tiền Giang",
    "bến tre": "Bến Tre",
    "trà vinh": "Trà Vinh",
    "vĩnh long": "Vĩnh Long",
    "đồng tháp": "Đồng Tháp",
    "an giang": "An Giang",
    "kiên giang": "Kiên Giang",
    "cần thơ": "Cần Thơ",
    "hậu giang": "Hậu Giang",
    "sóc trăng": "Sóc Trăng",
    "bạc liêu": "Bạc Liêu",
    "cà mau": "Cà Mau",
}

CITY_ALIAS_MAP: dict[str, str] = {
    "nha trang": "Khánh Hòa",
    "phan thiết": "Bình Thuận",
    "pleiku": "Gia Lai",
    "buôn ma thuột": "Đắk Lắk",
    "đà lạt": "Lâm Đồng",
    "biên hòa": "Đồng Nai",
    "vũng tàu": "Bà Rịa - Vũng Tàu",
    "mỹ tho": "Tiền Giang",
    "rạch giá": "Kiên Giang",
    "phú quốc": "Kiên Giang",
    "long xuyên": "An Giang",
    "châu đốc": "An Giang",
    "tỉnh huế": "Thừa Thiên Huế",
    "thành phố huế": "Thừa Thiên Huế",
    "tp huế": "Thừa Thiên Huế",
    "sài gòn": "TP. Hồ Chí Minh",
}
_ALL_LOCATION_KEYS = sorted(
    list(PROVINCE_MAP.keys()) + list(CITY_ALIAS_MAP.keys()), key=len, reverse=True
)

VALID_LOCATIONS: set[str] = set(PROVINCE_MAP.values()) | set(CITY_ALIAS_MAP.values())

_LOCATION_BLACKLIST_PATTERNS = [
    r"bộ y tế",
    r"bộ nông nghiệp",
    r"bộ công thương",
    r"cục thú y",
    r"cục bảo vệ thực vật",
    r"chi cục thú y",
    r"chi cục bảo vệ",
    r"trung quốc",
    r"trung tâm y tế",
    r"bệnh viện",
    r"vùng biên giới",
    r"biên giới",
    r"nước ngoài",
    r"các tỉnh",
    r"nhiều tỉnh",
    r"toàn quốc",
    r"cả nước",
]
_BLACKLIST_RE = re.compile("|".join(_LOCATION_BLACKLIST_PATTERNS))


def _is_blacklisted_location(candidate: str) -> bool:
    return bool(_BLACKLIST_RE.search(normalize(candidate)))


def _lookup_location(key: str) -> str | None:
    """Trả về tên chuẩn từ PROVINCE_MAP hoặc CITY_ALIAS_MAP."""
    if key in PROVINCE_MAP:
        return PROVINCE_MAP[key]
    if key in CITY_ALIAS_MAP:
        return CITY_ALIAS_MAP[key]
    return None


def detect_location(text: str) -> str:
    """Trả về tỉnh/thành đầu tiên tìm thấy, hoặc 'Không xác định'."""
    t = normalize(text)
    for key in _ALL_LOCATION_KEYS:
        if _wm(key, t):
            result = _lookup_location(key)
            if result and not _is_blacklisted_location(result):
                return result
    return "Không xác định"


def detect_all_locations(text: str) -> list[str]:
    """Trả về tất cả tỉnh/thành hợp lệ, không trùng."""
    t = normalize(text)
    seen: set[str] = set()
    found: list[str] = []
    for key in _ALL_LOCATION_KEYS:
        if _wm(key, t):
            result = _lookup_location(key)
            if result and result not in seen and not _is_blacklisted_location(result):
                seen.add(result)
                found.append(result)
    return found


def is_valid_location(name: str) -> bool:
    return (
        bool(name)
        and name != "Không xác định"
        and name in VALID_LOCATIONS
        and not _is_blacklisted_location(name)
    )


KNOWN_DISEASE_MAP: dict[str, str] = {
    "covid-19": "COVID-19",
    "covid": "COVID-19",
    "sars-cov-2": "COVID-19",
    "sars": "SARS",
    "mers": "MERS",
    "cúm a/h5n1": "Cúm A/H5N1",
    "cúm h5n1": "Cúm A/H5N1",
    "h5n1": "Cúm A/H5N1",
    "cúm a/h1n1": "Cúm A/H1N1",
    "cúm h1n1": "Cúm A/H1N1",
    "cúm a/h3n2": "Cúm A/H3N2",
    "cúm h3n2": "Cúm A/H3N2",
    "cúm a": "Cúm A",
    "cúm b": "Cúm B",
    "cúm mùa": "Cúm mùa",
    "sốt xuất huyết": "Sốt xuất huyết",
    "dengue": "Sốt xuất huyết Dengue",
    "tay chân miệng": "Tay chân miệng",
    "sởi": "Sởi",
    "rubella": "Rubella",
    "thủy đậu": "Thủy đậu",
    "viêm não nhật bản": "Viêm não Nhật Bản",
    "bệnh dại": "Bệnh dại",
    "dại": "Bệnh dại",
    "bạch hầu": "Bạch hầu",
    "ho gà": "Ho gà",
    "uốn ván": "Uốn ván",
    "bại liệt": "Bại liệt",
    "lao phổi": "Lao phổi",
    "bệnh lao": "Lao",
    "viêm gan a": "Viêm gan A",
    "viêm gan b": "Viêm gan B",
    "viêm gan c": "Viêm gan C",
    "hiv/aids": "HIV/AIDS",
    "hiv": "HIV/AIDS",
    "aids": "HIV/AIDS",
    "ebola": "Ebola",
    "zika": "Zika",
    "đậu mùa khỉ": "Đậu mùa khỉ (Mpox)",
    "mpox": "Đậu mùa khỉ (Mpox)",
    "đậu mùa": "Đậu mùa",
    "liên cầu lợn": "Liên cầu lợn",
    "whitmore": "Whitmore (Melioidosis)",
    "melioidosis": "Whitmore (Melioidosis)",
    "adenovirus": "Adenovirus",
    "dịch tả": "Tả",
    "bệnh tả": "Tả",
    "tiêu chảy cấp": "Tiêu chảy cấp",
    "thương hàn": "Thương hàn",
    "kiết lỵ": "Kiết lỵ",
    "sốt rét": "Sốt rét",
    "sốt mò": "Sốt mò",
    "viêm phổi cộng đồng": "Viêm phổi cộng đồng",
    "viêm màng não mô cầu": "Viêm màng não mô cầu",
    "não mô cầu": "Viêm màng não mô cầu",
    "rotavirus": "Rotavirus",
    "norovirus": "Norovirus",
    "enterovirus 71": "Enterovirus 71 (EV71)",
    "ev71": "Enterovirus 71 (EV71)",
    "đau mắt đỏ": "Đau mắt đỏ",
    "viêm kết mạc": "Viêm kết mạc",
    "sán lá gan": "Sán lá gan",
    "giun sán": "Giun sán",
    "dịch tả lợn châu phi": "Dịch tả lợn Châu Phi (ASF)",
    "dịch tả lợn": "Dịch tả lợn Châu Phi (ASF)",
    "asf": "Dịch tả lợn Châu Phi (ASF)",
    "cúm gia cầm": "Cúm gia cầm",
    "lở mồm long móng": "Lở mồm long móng (FMD)",
    "fmd": "Lở mồm long móng (FMD)",
    "tai xanh": "Tai xanh (PRRS)",
    "prrs": "Tai xanh (PRRS)",
    "tụ huyết trùng": "Tụ huyết trùng",
    "newcastle": "Newcastle",
    "gumboro": "Gumboro",
    "nhiệt thán": "Nhiệt thán",
    "leptospirosis": "Leptospirosis",
    "brucellosis": "Brucella",
    "brucella": "Brucella",
    "dịch hạch": "Dịch hạch",
    "bệnh đạo ôn": "Bệnh đạo ôn (lúa)",
    "đạo ôn": "Bệnh đạo ôn (lúa)",
    "bệnh bạc lá": "Bệnh bạc lá (lúa)",
    "bạc lá lúa": "Bệnh bạc lá (lúa)",
    "bệnh khô vằn": "Bệnh khô vằn (lúa)",
    "khô vằn": "Bệnh khô vằn (lúa)",
    "vàng lùn lùn xoắn lá": "Bệnh vàng lùn - lùn xoắn lá",
    "vàng lùn": "Bệnh vàng lùn - lùn xoắn lá",
    "lùn xoắn lá": "Bệnh vàng lùn - lùn xoắn lá",
    "rầy nâu": "Rầy nâu",
    "rầy lưng trắng": "Rầy lưng trắng",
    "sâu cuốn lá": "Sâu cuốn lá nhỏ",
    "sâu đục thân": "Sâu đục thân",
    "sâu keo mùa thu": "Sâu keo mùa thu",
    "bọ trĩ": "Bọ trĩ",
    "nhện đỏ": "Nhện đỏ",
    "rệp sáp": "Rệp sáp",
    "bệnh thán thư": "Bệnh thán thư",
    "thán thư": "Bệnh thán thư",
    "bệnh héo xanh": "Bệnh héo xanh vi khuẩn",
    "héo xanh vi khuẩn": "Bệnh héo xanh vi khuẩn",
    "bệnh héo vàng": "Bệnh héo vàng Fusarium",
    "héo vàng fusarium": "Bệnh héo vàng Fusarium",
    "bệnh chổi rồng": "Bệnh chổi rồng",
    "chổi rồng": "Bệnh chổi rồng",
    "greening": "Bệnh Greening (cam quýt)",
    "huanglongbing": "Bệnh Greening (cam quýt)",
    "bệnh thối gốc": "Bệnh thối gốc rễ",
    "thối gốc rễ": "Bệnh thối gốc rễ",
    "nấm hồng": "Bệnh nấm hồng",
}

_DISEASE_KEYS_SORTED = sorted(KNOWN_DISEASE_MAP.keys(), key=len, reverse=True)

VALID_DISEASES: set[str] = set(KNOWN_DISEASE_MAP.values())

_DISEASE_BLACKLIST = {
    "không xác định",
    "truyền nhiễm",
    "dịch bệnh",
    "bệnh dịch",
    "phòng chống",
    "kiểm soát dịch",
    "phòng ngừa",
    "vaccine",
    "vắc xin",
    "tiêm chủng",
    "tiêm phòng",
    "ung thư",
    "tim mạch",
    "huyết áp",
    "tiểu đường",
    "béo phì",
    "suy dinh dưỡng",
}


def detect_disease(text: str) -> str:
    """
    Chỉ dùng WHITELIST. Không có regex fallback.
    Trả về tên bệnh chuẩn hoặc 'Không xác định'.
    """
    t = normalize(text)

    for key in _DISEASE_KEYS_SORTED:
        if _wm(key, t):
            return KNOWN_DISEASE_MAP[key]

    return "Không xác định"


def is_valid_disease(name: str) -> bool:
    return bool(name) and name != "Không xác định" and name in VALID_DISEASES


KEYWORDS_LIST = [
    "dịch bệnh",
    "ổ dịch",
    "ca nhiễm",
    "ca mắc",
    "ca tử vong",
    "lây nhiễm",
    "bùng phát",
    "truyền nhiễm",
    "cách ly",
    "virus",
    "vi khuẩn",
    "vi rút",
    "phòng dịch",
    "dịch tả lợn",
    "cúm gia cầm",
    "lở mồm long móng",
    "tai xanh",
    "dịch bệnh gia súc",
    "dịch bệnh gia cầm",
    "tiêu hủy đàn",
    "dịch hại",
    "sâu bệnh",
    "bệnh hại",
    "rầy nâu",
    "đạo ôn",
]


def detect_keywords(text: str) -> list[str]:
    t = normalize(text)
    return list(set(k for k in KEYWORDS_LIST if k in t))


CASE_PATTERNS = [
    r"(\d[\d\.]*)\s*ca\s+(?:nhiễm|mắc|dương tính|bệnh)",
    r"(\d[\d\.]*)\s*người\s+(?:nhiễm|mắc|bị bệnh)",
    r"(\d[\d\.]*)\s*trường hợp\s+(?:nhiễm|mắc|bệnh)",
    r"ghi nhận\s+(\d[\d\.]*)\s*ca",
    r"phát hiện\s+(\d[\d\.]*)\s*ca",
    r"có\s+(\d[\d\.]*)\s*ca\s+(?:mới|nhiễm|mắc)",
]
DEAD_PATTERNS = [
    r"(\d[\d\.]*)\s*ca\s+tử vong",
    r"(\d[\d\.]*)\s*người\s+(?:tử vong|chết|thiệt mạng)",
    r"(\d[\d\.]*)\s*trường hợp\s+tử vong",
]
RECOVERED_PATTERNS = [
    r"(\d[\d\.]*)\s*(?:ca\s+)?(?:khỏi bệnh|bình phục|xuất viện|hồi phục)",
]

CASE_CUMULATIVE_CONTEXT = [
    "lũy kế",
    "cộng dồn",
    "từ đầu năm",
    "từ đầu mùa",
    "từ đầu dịch",
    "trong năm",
    "năm nay",
    "cả năm",
    "hằng năm",
    "mỗi năm",
    "so với cùng kỳ",
    "cùng kỳ",
    "toàn quốc",
    "cả nước",
]

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

GROUP_WEEKLY_CASE_CAPS = {
    "human": 10000,
    "animal": 100000,
    "plant": 100000,
}


def _parse_num(s: str) -> int:
    try:
        return int(s.replace(".", "").replace(",", ""))
    except Exception:
        return 0


def _has_cumulative_context(text: str, match) -> bool:
    start = max(0, match.start() - 100)
    end = min(len(text), match.end() + 100)
    context = text[start:end]
    return any(term in context for term in CASE_CUMULATIVE_CONTEXT)


def _case_cap_for(disease_name: str, group: str) -> int:
    if disease_name in DISEASE_WEEKLY_CASE_CAPS:
        return DISEASE_WEEKLY_CASE_CAPS[disease_name]
    return GROUP_WEEKLY_CASE_CAPS.get(group or "human", 10000)


def extract_cases(
    text: str, disease_name: str = "Không xác định", group: str = "human"
) -> int:
    t = normalize(text)
    cap = _case_cap_for(disease_name, group)

    for p in CASE_PATTERNS:
        m = re.search(p, t)
        if m:
            if _has_cumulative_context(t, m):
                continue
            v = _parse_num(m.group(1))
            if 0 < v <= cap:
                return v
    return 0


def extract_dead(text: str) -> int:
    t = normalize(text)
    for p in DEAD_PATTERNS:
        m = re.search(p, t)
        if m:
            v = _parse_num(m.group(1))
            if 0 < v < 1_000_000:
                return v
    return 0


def extract_recovered(text: str) -> int:
    t = normalize(text)
    for p in RECOVERED_PATTERNS:
        m = re.search(p, t)
        if m:
            v = _parse_num(m.group(1))
            if 0 < v < 10_000_000:
                return v
    return 0


ANIMAL_KEYWORDS = [
    "lợn",
    "heo",
    "gà",
    "vịt",
    "ngan",
    "bò",
    "trâu",
    "dê",
    "cừu",
    "gia súc",
    "gia cầm",
    "thủy cầm",
    "thú nuôi",
    "chăn nuôi",
    "đàn vật nuôi",
    "trang trại chăn nuôi",
    "cúm gia cầm",
    "dịch tả lợn",
    "lở mồm long móng",
    "thú y",
    "chi cục thú y",
    "tiêu hủy đàn",
]
PLANT_KEYWORDS = [
    "lúa",
    "cây trồng",
    "sâu bệnh",
    "dịch hại",
    "bệnh hại",
    "rầy nâu",
    "đạo ôn",
    "vườn cây",
    "hoa màu",
    "cây ăn trái",
    "cây ăn quả",
    "rau màu",
    "thuốc trừ sâu",
    "bảo vệ thực vật",
    "phun thuốc bảo vệ",
    "xoài",
    "cam",
    "bưởi",
    "nhãn",
    "vải thiều",
    "hồ tiêu",
    "cà phê",
    "cao su",
    "sầu riêng",
    "cục bảo vệ thực vật",
    "chi cục bảo vệ thực vật",
]


def classify_group(text: str) -> str:
    t = normalize(text)
    animal_score = sum(1 for k in ANIMAL_KEYWORDS if _wm(k, t))
    plant_score = sum(1 for k in PLANT_KEYWORDS if _wm(k, t))
    if animal_score == 0 and plant_score == 0:
        return "human"
    if animal_score >= plant_score:
        return "animal"
    return "plant"


HIGH_RISK_KEYWORDS = [
    "bùng phát mạnh",
    "khẩn cấp",
    "đại dịch",
    "pandemic",
    "lây lan nhanh",
    "phong tỏa",
    "tử vong hàng loạt",
]
MEDIUM_RISK_KEYWORDS = [
    "bùng phát",
    "gia tăng",
    "lây lan",
    "cảnh báo",
    "nguy cơ",
    "xuất hiện ổ dịch",
    "phòng chống dịch",
]


def classify_risk(text: str, cases: int = 0, dead: int = 0) -> str:
    t = normalize(text)
    if any(k in t for k in HIGH_RISK_KEYWORDS) or dead >= 5 or cases >= 500:
        return "HIGH"
    if any(k in t for k in MEDIUM_RISK_KEYWORDS) or dead >= 1 or cases >= 50:
        return "MEDIUM"
    return "LOW"


def extract_info(title: str, content: str) -> dict:
    full_text = f"{title or ''}. {content or ''}"
    group = classify_group(full_text)
    disease = detect_disease(full_text)
    cases = extract_cases(full_text, disease, group)
    dead = extract_dead(full_text)
    recovered = extract_recovered(full_text)
    risk = classify_risk(full_text, cases, dead)
    location = detect_location(full_text)
    all_locs = detect_all_locations(full_text)

    return {
        "keywords": detect_keywords(full_text),
        "disease_name": disease,
        "disease_valid": is_valid_disease(disease),
        "location": location,
        "location_valid": is_valid_location(location),
        "all_locations": all_locs,
        "cases": cases,
        "cases_dead": dead,
        "cases_recovered": recovered,
        "group": group,
        "risk_level": risk,
    }
