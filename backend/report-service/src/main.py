from pathlib import Path

from dotenv import load_dotenv


SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

load_dotenv(BASE_DIR / ".env")

from database import init_db
from report_generator import generate_monthly_report


def main():
    init_db()
    result = generate_monthly_report()

    if not result:
        print("No data available to create report.")
        return

    _, filename = result
    print(f"Created report: {filename}")


if __name__ == "__main__":
    main()
