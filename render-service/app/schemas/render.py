#render-service/app/schemas/render.py

from pydantic import BaseModel
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

class TemplateServiceTextBlock(BaseModel):
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str

class TemplateServiceResponse(BaseModel):
    id: UUID
    image_path: str
    text_blocks: List[TemplateServiceTextBlock]

