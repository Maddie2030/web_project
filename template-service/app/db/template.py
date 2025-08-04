# Template-service/app/db/template.py
from uuid import UUID, uuid4
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from ..schemas.template import TemplateDB, TemplateCreate

TEMPLATES_COLLECTION = "templates"

async def create_template(db: AsyncIOMotorClient, template: TemplateCreate) -> TemplateDB:
    try:
        template_with_id = TemplateDB(
            id=uuid4(),
            name=template.name,
            image_path=template.image_path,
            text_blocks=template.text_blocks
        )
        
        template_dict = template_with_id.model_dump(by_alias=True)
        template_dict['_id'] = str(template_dict['_id'])

        result = await db[TEMPLATES_COLLECTION].insert_one(template_dict)
        
        if not result.acknowledged:
            raise RuntimeError("Failed to insert document into database.")

        new_template = await db[TEMPLATES_COLLECTION].find_one({"_id": result.inserted_id})

        if not new_template:
            raise ValueError("Failed to retrieve newly created template.")

        return TemplateDB(**new_template)
    except Exception as e:
        print(f"Error during create_template: {e}")
        raise RuntimeError(f"Database operation failed: {e}")

async def get_template(db: AsyncIOMotorClient, template_id: UUID) -> Optional[TemplateDB]:
    template = await db[TEMPLATES_COLLECTION].find_one({"_id": str(template_id)})
    if template:
        return TemplateDB(**template)
    return None

async def get_all_templates(db: AsyncIOMotorClient) -> List[TemplateDB]:
    templates = await db[TEMPLATES_COLLECTION].find().to_list(1000)
    return [TemplateDB(**template) for template in templates]