FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY static ./static

# Cloud Run tells the app which port to listen on via $PORT.
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
