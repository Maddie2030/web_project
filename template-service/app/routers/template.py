# Template-service/app/routers/template.py

import os
from json import loads
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorClient

from app.schemas.template import TemplateCreate, TemplateDB, TextBlock
from app.db.mongodb import get_database
from app.db.template import create_template, get_all_templates, get_template

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])

STATIC_DIR = "/app/static/backgrounds"
os.makedirs(STATIC_DIR, exist_ok=True)


def get_db() -> AsyncIOMotorClient:
    """Dependency to access MongoDB."""
    return get_database()


async def save_file(file: UploadFile, dest: str) -> str:
    """Save uploaded file and return its public path."""
    extension = file.filename.rsplit(".", 1)[-1]
    filename = f"{uuid4()}.{extension}"
    path = os.path.join(dest, filename)
    await file.seek(0)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return filename


@router.get("/", response_model=List[TemplateDB])
async def list_templates(db: AsyncIOMotorClient = Depends(get_db)):
    """List all templates."""
    return await get_all_templates(db)


@router.get("/{template_id}", response_model=TemplateDB)
async def fetch_template(template_id: str, db: AsyncIOMotorClient = Depends(get_db)):
    """Retrieve a template by its ID."""
    template = await get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.post("/upload", response_model=TemplateDB, status_code=status.HTTP_201_CREATED)
async def upload_template(
    name: str = Form(...),
    text_blocks_json: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_db),
):
    """Upload a new template with background image and text blocks."""
    if image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")

    # Save image
    try:
        filename = await save_file(image, STATIC_DIR)
        image_path = f"/static/backgrounds/{filename}"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File save error: {e}")

    # Parse text blocks
    try:
        text_blocks = [TextBlock(**tb) for tb in loads(text_blocks_json)]
    except Exception as e:
        os.remove(os.path.join(STATIC_DIR, filename))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid text_blocks JSON: {e}")

    # Create in DB
    try:
        new_template = await create_template(db, TemplateCreate(name=name, image_path=image_path, text_blocks=text_blocks))
        return new_template
    except Exception as e:
        os.remove(os.path.join(STATIC_DIR, filename))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")
