from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
import requests
import uuid
import os

from app.schemas.render import ImageRenderRequest, ImageRenderResponse, TemplateServiceResponse

router = APIRouter(prefix="/api/v1", tags=["render"])

# Constants
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
STATIC_OUTPUTS_PATH = "/app/static/outputs"
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # A standard font in many Linux distros

@router.post("/generate-image", response_model=ImageRenderResponse)
async def generate_image(request: ImageRenderRequest):
    """
    Generates a custom image from a template with user-provided text.
    """
    # 1. Make internal HTTP request to template-service
    if not TEMPLATE_SERVICE_URL:
        raise HTTPException(status_code=500, detail="TEMPLATE_SERVICE_URL is not configured.")

    try:
        response = requests.get(f"{TEMPLATE_SERVICE_URL}/templates/{request.template_id}")
        response.raise_for_status()
        template_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch template metadata: {e}")

    # 2. Validate received template data
    try:
        template = TemplateServiceResponse(**template_data)
    except ValidationError:
        raise HTTPException(status_code=500, detail="Invalid template data received from template-service.")
    
    # Check if a background image path exists
    if not template.image_path:
        raise HTTPException(status_code=404, detail="Template does not have a background image path.")

    # 3. Load background image from static/backgrounds
    background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
    if not os.path.exists(background_path):
        raise HTTPException(status_code=404, detail=f"Background image not found at {background_path}.")

    try:
        image = Image.open(background_path)
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to load background image.")
    
    draw = ImageDraw.Draw(image)

    # 4. Iterate and draw text onto the image
    for block_data in request.text_data:
        try:
            font = ImageFont.truetype(FONT_PATH, block_data.font_size)
        except IOError:
            # Fallback to a default font if specified font is not found
            font = ImageFont.load_default()

        draw.text(
            (block_data.x, block_data.y),
            block_data.user_text,
            fill=block_data.color,
            font=font
        )
    
    # Ensure output directory exists
    os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)

    # 5. Save the generated image with a unique filename
    unique_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
    try:
        image.save(output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save generated image: {e}")

    # 6. Return URL of the generated image
    return ImageRenderResponse(image_url=f"/static/outputs/{unique_filename}")