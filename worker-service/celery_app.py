from celery import Celery

# Instantiate the Celery application
app = Celery('worker_service')

# Load the configuration from celeryconfig.py
app.config_from_object('celeryconfig')