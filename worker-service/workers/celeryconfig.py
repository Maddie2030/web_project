import os
from dotenv import load_dotenv

load_dotenv()

# Get Redis URI from environment variables with a fallback
REDIS_URI = os.getenv("REDIS_URI", "redis://redis:6379/0")

# Use Redis as the broker to send and receive messages
broker_url = REDIS_URI

# Use Redis as the result backend to store task results
result_backend = REDIS_URI

# Define the default queue name
task_default_queue = 'render_queue'

# Route tasks to a specific queue
# This ensures that tasks from 'worker.tasks' go to the 'render_queue'
task_routes = {
    'tasks.*': {'queue': 'render_queue'}
}

# Ensure the worker can reconnect to the broker on startup
broker_connection_retry_on_startup = True

# Increase logging detail for debugging
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s[%(task_id)s]: %(message)s"