FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV FORECAST_SERVICE_URL=http://localhost:8010
ENV REPORT_SERVICE_URL=http://report:8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]