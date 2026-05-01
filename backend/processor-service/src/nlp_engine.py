import re

# ========================
# NORMALIZE TEXT
# ========================
def normalize(text):
    if not text:
        return ""
    return text.lower()


# ========================
# KEYWORDS
# ========================
KEYWORDS_LIST = [
    "dịch", "dịch bệnh", "ổ dịch", "ca nhiễm",
    "lây nhiễm", "bùng phát", "truyền nhiễm",
    "virus", "vi khuẩn",
    "dịch hại", "sâu bệnh", "bệnh hại"
]


def detect_keywords(text):
    text = normalize(text)
    return list(set([k for k in KEYWORDS_LIST if k in text]))


# ========================
# DISEASE DETECTION (semi-flexible)
# ========================
def detect_disease(text):
    text = normalize(text)

    # pattern chung
    patterns = [
        r"(dịch\s+[a-zà-ỹ\s]+)",
        r"(bệnh\s+[a-zà-ỹ\s]+)",
        r"(virus\s+[a-z0-9\-\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            disease = match.group(1).strip()

            # lọc noise
            if len(disease) > 5:
                return disease

    return "Không xác định"


# ========================
# LOCATION DETECTION (improved)
# ========================
LOCATIONS = [
    "hà nội", "tp hcm", "thành phố hồ chí minh",
    "đà nẵng", "cần thơ", "hải phòng",
    "quảng nam", "nghệ an", "thanh hóa",
    "đồng nai", "bình dương"
]


def detect_location(text):
    text = normalize(text)

    for loc in LOCATIONS:
        if loc in text:
            return loc.title()

    return "Không xác định"


# ========================
# EXTRACT CASE NUMBERS
# ========================
def extract_cases(text):
    text = normalize(text)

    # ví dụ: 120 ca, 200 người mắc
    match = re.search(r"(\d+)\s*(ca|người mắc|trường hợp)", text)
    if match:
        return int(match.group(1))

    return 0


# ========================
# CLASSIFY GROUP
# ========================
def classify_group(text):
    text = normalize(text)

    if any(k in text for k in ["lợn", "gà", "bò", "gia súc", "gia cầm"]):
        return "animal"

    if any(k in text for k in ["lúa", "cây", "sâu bệnh", "cây trồng"]):
        return "plant"

    return "human"


# ========================
# MAIN EXTRACT
# ========================
def extract_info(title, content):
    full_text = f"{title or ''}. {content or ''}"

    return {
        "keywords": detect_keywords(full_text),
        "disease_name": detect_disease(full_text),
        "location": detect_location(full_text),
        "cases": extract_cases(full_text),
        "group": classify_group(full_text)
    }