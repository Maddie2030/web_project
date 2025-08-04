# The broker and backend connection URLs, pointing to your Redis container
# 'redis' is the service name from your docker-compose.yml file
broker_url = 'redis://redis:6379/0'
result_backend = 'redis://redis:6379/0'

# List of modules to import when the Celery worker starts.
# This is where your task definitions are located.
imports = ('tasks',)

# Task routing to define which tasks go to which queue
task_routes = {
    'tasks.add': {'queue': 'render_queue'},
}

# Define the task queue
task_queues = {
    'render_queue': {
        'exchange': 'render_queue',
        'binding_key': 'render_queue',
    }
}

# Optional: Configure logging for the worker
worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"