# Dockerfile for Render Service (FastAPI)
# WeasyPrint requires some system libraries for rendering.
# Add necessary system packages before Python packages.
FROM python:3.10-slim-bullseye

# Install system dependencies for WeasyPrint (Cairo, Pango, GDK-Pixbuf)
# and other fonts that might be useful.
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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]