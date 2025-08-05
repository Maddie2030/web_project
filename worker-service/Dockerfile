# Use a Python 3.10 slim image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the default command to run the Celery worker
# The -A option specifies the Celery application, -Q specifies the queue
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "-Q", "render_queue"]