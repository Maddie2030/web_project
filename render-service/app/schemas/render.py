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
    """Schema for the successful response after an image is generated."""
    image_url: str

# Schema for the response from the template-service (remains the same)
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