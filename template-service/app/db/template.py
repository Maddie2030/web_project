# Template-service/app/db/template.py

from uuid import uuid4, UUID
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from app.schemas.template import TemplateDB, TemplateCreate

COLLECTION = "templates"


async def create_template(db: AsyncIOMotorClient, data: TemplateCreate) -> TemplateDB:
    """Insert and return a new template document."""
    template = TemplateDB(_id=uuid4(), **data.dict())
    doc = template.model_dump(by_alias=True)
    result = await db[COLLECTION].insert_one(doc)
    if not result.acknowledged:
        raise RuntimeError("Insert operation failed.")
    saved = await db[COLLECTION].find_one({"_id": doc["_id"]})
    return TemplateDB(**saved)


async def get_all_templates(db: AsyncIOMotorClient) -> List[TemplateDB]:
    """Retrieve all templates."""
    docs = await db[COLLECTION].find().to_list(length=1000)
    return [TemplateDB(**doc) for doc in docs]


async def get_template(db: AsyncIOMotorClient, template_id: UUID) -> Optional[TemplateDB]:
    """Retrieve a single template by its UUID."""
    doc = await db[COLLECTION].find_one({"_id": template_id})
    return TemplateDB(**doc) if doc else None
