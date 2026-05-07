from pathlib import Path

from dotenv import load_dotenv


SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

load_dotenv(BASE_DIR / ".env")

from database import init_db
from report_generator import generate_weekly_report


def main():
    init_db()
    result = generate_weekly_report()

    if not result:
        print("Không có dữ liệu để tạo báo cáo.")
        return

    _, filename = result
    print(f"Đã tạo báo cáo: {filename}")


if __name__ == "__main__":
    main()
