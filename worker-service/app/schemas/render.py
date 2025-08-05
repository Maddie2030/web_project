# worker-service/app/schemas/render.py

from pydantic import BaseModel, Field, ConfigDict
from typing import List
from uuid import UUID

class TextBlockRequest(BaseModel):
    """The user-provided text for a single block."""
    user_text: str

class ImageRenderRequest(BaseModel):
    """The complete payload for the image rendering request."""
    template_id: UUID
    text_data: List[TextBlockRequest]

class ImageRenderResponse(BaseModel):
    """Schema for a successful response after image generation."""
    image_url: str

class PDFRenderResponse(BaseModel):
    pdf_url: str 

class TemplateServiceTextBlock(BaseModel):
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str

class TemplateServiceResponse(BaseModel):
    id: UUID = Field(alias="_id")
    image_path: str
    text_blocks: List[TemplateServiceTextBlock]

    model_config = ConfigDict(
        populate_by_name=True,
        allow_population_by_field_name=True,
        json_encoders={UUID: str}
    )