# Danh sách từ khóa mục tiêu
KEYWORDS_LIST = ["dịch", "virus", "covid", "sốt xuất huyết", "cúm", "ca nhiễm", "lây nhiễm"]

def detect_keyword(content):
    """
    Hàm phân tích văn bản thô để tìm các từ khóa liên quan đến dịch bệnh.
    """
    if not content:
        return []
        
    found = []
    content_lower = content.lower()

    for k in KEYWORDS_LIST:
        if k in content_lower:
            found.append(k)

    return list(set(found)) # Trả về danh sách không trùng lặp