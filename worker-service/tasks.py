from celery_app import app

@app.task
def add(x, y):
    """Simple task to demonstrate a worker executing a function."""
    return x + y