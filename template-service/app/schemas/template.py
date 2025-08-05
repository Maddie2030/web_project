# Template-service/app/schemas/template.py

from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class TextBlock(BaseModel):
    """Layout metadata for a single text block."""
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str


class TemplateCreate(BaseModel):
    """Payload for creating a new template."""
    name: str
    image_path: str
    text_blocks: List[TextBlock]


class TemplateDB(TemplateCreate):
    """Template model as stored in the database."""
    id: UUID = Field(..., alias="_id")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {UUID: lambda u: str(u)}
