# worker-service/Dockerfile

# worker-service/Dockerfile

# Use a Python 3.10 slim image as the base
FROM python:3.11-slim-bookworm

# Install system dependencies needed for Pillow and WeasyPrint
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev \
    fonts-dejavu-core \
    libxml2-dev libxslt1-dev libcairo2-dev libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    gcc python3-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code, including the 'app' directory
COPY . .

# Correctly reference the Celery application using its module path
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-Q", "render_queue"]