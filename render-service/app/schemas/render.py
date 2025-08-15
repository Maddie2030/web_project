#render-service/app/schemas/render.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID

# What the frontend sends (one entry per title)
class TextBlockRequest(BaseModel):
    title: str
    user_text: str

    # User overrides (required on frontend after drag/resize)
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Styling overrides
    font_size: Optional[int] = None
    color: Optional[str] = None
    font_path: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None

    # Optional wrapping width (pixels)
    max_width: Optional[int] = None

class ImageRenderRequest(BaseModel):
    template_id: UUID
    text_data: List[TextBlockRequest]

class ImageRenderResponse(BaseModel):
    image_url: str

class PDFRenderResponse(BaseModel):
    pdf_url: str

# What we receive from the template-service
class TemplateServiceTextBlock(BaseModel):
    title: str
    x: int
    y: int
    width: int
    height: int
    font_size: int
    color: str
    font_path: Optional[str] = None
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    max_width: Optional[int] = None
    default_text: str = ""

class TemplateServiceResponse(BaseModel):
    id: UUID = Field(alias="_id")
    image_path: str
    text_blocks: List[TemplateServiceTextBlock]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_by_name=True,
        json_encoders={UUID: str}
    )
