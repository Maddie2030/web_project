# Template-service/app/main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.routers.template import router as template_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and terminate resources on startup/shutdown."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Template Service API",
    version="0.1.0",
    description="Microservice for managing templates.",
    lifespan=lifespan
)

# Mount static backgrounds
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.include_router(template_router)

@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    return {"message": "Template Service is up and running."}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Return service and database health status."""
    db = get_database()
    status_db = "disconnected"
    try:
        await db.command("ping")
        status_db = "connected"
    except Exception:
        status_db = "error"
    return {"status": "ok", "service": "template-service", "database": status_db}
