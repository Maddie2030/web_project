# Dockerfile for Worker Service (FastAPI and Celery Worker)
FROM python:3.10-slim-bullseye

# Install system dependencies for WeasyPrint (same as render-service)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libxml2-dev \
    libxslt1-dev \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 # If worker-service also runs a FastAPI endpoint

# Default CMD for the FastAPI part of worker-service
# This will be overridden for the actual Celery worker process in docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]