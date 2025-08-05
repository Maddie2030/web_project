#render-service/app/routers/render.py

from pydantic import BaseModel
from typing import List
from uuid import UUID


class TextBlockRequest(BaseModel):
    """User-provided text for a single block."""
    user_text: str


class ImageRenderRequest(BaseModel):
    """Payload for image or PDF rendering requests."""
    template_id: UUID
    text_data: List[TextBlockRequest]


class ImageRenderResponse(BaseModel):
    """Response schema for generated image."""
    image_url: str


class PDFRenderResponse(BaseModel):
    """Response schema for generated PDF."""
    pdf_url: str


class TemplateServiceTextBlock(BaseModel):
    """Metadata for a template’s text block."""
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str


class TemplateServiceResponse(BaseModel):
    """Metadata for a template from the template-service."""
    id: UUID
    image_path: str
    text_blocks: List[TemplateServiceTextBlock]
