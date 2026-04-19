# Sử dụng Python image chính thức
FROM python:3.10-slim

# Thiết kế thư mục làm việc trong container
WORKDIR /app

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

ENV PYTHONPATH=/app/src

# Dùng uvicorn để chạy ứng dụng FastAPI, mở cổng 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]