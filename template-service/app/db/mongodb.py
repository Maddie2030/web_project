# Template-service/app/db/mongodb.py

import os
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "template_service_db")

db_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection."""
    global db_client
    db_client = AsyncIOMotorClient(MONGO_URI)
    # Validate connection
    await db_client[MONGO_DB_NAME].command("ping")


async def close_mongo_connection() -> None:
    """Close MongoDB connection."""
    global db_client
    if db_client:
        db_client.close()


def get_database() -> AsyncIOMotorClient:
    """Retrieve the MongoDB database instance."""
    if not db_client:
        raise RuntimeError("Database client is not initialized.")
    return db_client[MONGO_DB_NAME]
