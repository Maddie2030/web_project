#worker-service/celery_app.py

import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Define Celery instance
celery_app = Celery('worker-service')

# Use the configuration file for settings
celery_app.config_from_object('celeryconfig')

# Autodiscover tasks from a tasks module (if you had one)
celery_app.autodiscover_tasks(['worker-service.celery_app'])
