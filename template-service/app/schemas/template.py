# Template-service/app/schemas/template.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List
from uuid import UUID, uuid4

class TextBlock(BaseModel):
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str

class TemplateBase(BaseModel):
    name: str
    image_path: str
    text_blocks: List[TextBlock]

class TemplateCreate(TemplateBase):
    pass

class TemplateDB(TemplateBase):
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={UUID: str},
        validate_by_name=True
    )
    id: UUID = Field(alias="_id", default_factory=uuid4)
 

