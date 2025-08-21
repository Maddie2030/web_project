# Dockerfile for Auth Service (FastAPI)
# Stage 1: Build dependencies
# -------------------------------
FROM python:3.10-slim-bullseye AS builder

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
COPY . .


# Stage 2: Production image
# -------------------------------
FROM python:3.10-slim-bullseye

WORKDIR /app

# Copy only the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Expose the port on which the API will run
EXPOSE 8000

# Set dynamic environment variables for Gunicorn workers
ENV WORKERS=2
ENV TIMEOUT=120

# Start the application with Gunicorn using Uvicorn workers
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "$WORKERS", \
     "--timeout", "$TIMEOUT"]