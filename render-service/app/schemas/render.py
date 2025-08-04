from pydantic import BaseModel
from typing import List
from uuid import UUID

class TextBlockRequest(BaseModel):
    """Schema for the user-provided text in the request body."""
    user_text: str

class ImageRenderRequest(BaseModel):
    """The main schema for the incoming POST /generate-image request."""
    template_id: UUID
    text_data: List[TextBlockRequest]

class ImageRenderResponse(BaseModel):
    """The schema for the successful response, containing the URL of the new image."""
    image_url: str

class TemplateServiceTextBlock(BaseModel):
    """The schema for a text block received from the template-service."""
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    default_text: str

class TemplateServiceResponse(BaseModel):
    """The schema for the complete template object received from the template-service."""
    id: UUID
    image_path: str
    text_blocks: List[TemplateServiceTextBlock]