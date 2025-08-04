import os
import requests
import uuid
from fastapi import APIRouter, HTTPException, status
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from app.schemas.render import (
    ImageRenderRequest,
    ImageRenderResponse,
    PDFRenderResponse,
    TemplateServiceResponse,
    TextBlockRequest
)

router = APIRouter(prefix="/api/v1", tags=["render"])

TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"
FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf" 

def render_image_from_template(request: ImageRenderRequest):
    """
    Helper function to render an image and save it to the outputs directory.
    Returns the path to the saved image file.
    """
    if not TEMPLATE_SERVICE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TEMPLATE_SERVICE_URL is not configured."
        )

    try:
        template_url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{request.template_id}"
        response = requests.get(template_url)
        response.raise_for_status()
        template = TemplateServiceResponse(**response.json())
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch template metadata: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid template data received: {e}"
        )

    background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
    if not os.path.exists(background_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Background image not found at path: {background_path}"
        )
    
    try:
        image = Image.open(background_path)
    except IOError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to load background image with Pillow."
        )

    draw = ImageDraw.Draw(image)
    for i, block_request in enumerate(request.text_data):
        if i >= len(template.text_blocks):
            break
        template_block = template.text_blocks[i]
        try:
            font = ImageFont.truetype(FONT_PATH, template_block.font_size)
        except IOError:
            font = ImageFont.load_default()
        draw.text(
            (template_block.x, template_block.y),
            block_request.user_text,
            fill=template_block.color,
            font=font
        )
    
    os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
    try:
        image.save(output_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to save generated image: {e}"
        )
    return output_path

@router.post("/generate-image", response_model=ImageRenderResponse, status_code=status.HTTP_201_CREATED)
async def generate_image_endpoint(request: ImageRenderRequest):
    """Generates a customized image based on a template and user-provided text."""
    image_path = render_image_from_template(request)
    unique_filename = os.path.basename(image_path)
    return ImageRenderResponse(image_url=f"/static/outputs/{unique_filename}")

@router.post("/generate-pdf", response_model=PDFRenderResponse, status_code=status.HTTP_201_CREATED)
async def generate_pdf_endpoint(request: ImageRenderRequest):
    """Generates a customized PDF from a template, including a rendered image."""
    # 1. Fetch template and generate image internally
    image_path = render_image_from_template(request)

    # 2. Use WeasyPrint to convert to PDF
    try:
        image_url_for_html = f"file://{image_path}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Generated PDF</title>
            <style>
                body {{ margin: 0; padding: 0; }}
                img {{ max-width: 100%; height: auto; display: block; }}
            </style>
        </head>
        <body>
            <img src="{image_url_for_html}" />
        </body>
        </html>
        """
        html = HTML(string=html_content, base_url=".")

        # 3. Save the generated PDF
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(STATIC_OUTPUTS_PATH, pdf_filename)
        html.write_pdf(pdf_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {e}"
        )

    # 4. Return URL of the generated PDF
    return PDFRenderResponse(pdf_url=f"/static/outputs/{pdf_filename}")