## Render-service/app/routers/render.py
import os
import requests
import uuid
from fastapi import APIRouter, HTTPException, status
from PIL import Image, ImageDraw, ImageFont


from app.schemas.render import (
    ImageRenderRequest,
    ImageRenderResponse,
    TemplateServiceResponse,
    TextBlockRequest
)

router = APIRouter(prefix="/api/v1", tags=["render"])

# Environment variables are loaded at startup
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"

# A font path that is available in the Docker container's base image
FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf" 

@router.post("/generate-image", response_model=ImageRenderResponse, status_code=status.HTTP_201_CREATED)
async def generate_image(request: ImageRenderRequest):
    """
    Generates a customized image based on a template and user-provided text.
    """
    if not TEMPLATE_SERVICE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TEMPLATE_SERVICE_URL is not configured."
        )

    # 1. Make internal HTTP request to template-service
    try:
        template_url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{request.template_id}"
        response = requests.get(template_url)
        response.raise_for_status() # Raise an error for bad status codes
        template_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch template metadata from template-service: {e}"
        )
    
    # 2. Validate received template data using our Pydantic model
    try:
        template = TemplateServiceResponse(**template_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid template data received from template-service: {e}"
        )

    # Construct the full path to the background image
    background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
    
    if not os.path.exists(background_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Background image not found at path: {background_path}"
        )
    
    # 3. Load the background image using Pillow
    try:
        image = Image.open(background_path)
    except IOError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to load background image with Pillow."
        )

    draw = ImageDraw.Draw(image)

    # 4. Iterate and draw text onto the image
    for i, block_request in enumerate(request.text_data):
        if i >= len(template.text_blocks):
            break

        template_block = template.text_blocks[i]
        try:
            font = ImageFont.truetype(FONT_PATH, template_block.font_size)
        except IOError:
            font = ImageFont.load_default() # Fallback to a default font

        draw.text(
            (template_block.x, template_block.y),
            block_request.user_text,
            fill=template_block.color,
            font=font
        )
    
    # 5. Save the generated image with a unique filename
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

    # 6. Return the URL of the newly created image
    return ImageRenderResponse(image_url=f"/static/outputs/{unique_filename}")

@router.post("/generate-pdf", response_model=PDFRenderResponse, status_code=status.HTTP_201_CREATED)
async def generate_pdf(request: ImageRenderRequest):
    """Generates a customized PDF from a template, including a rendered image."""
    # 1. Fetch template and generate image internally
    image_path = render_image_from_template(request)

    # 2. Use WeasyPrint to convert to PDF
    try:
        # Create a simple HTML document with the generated image
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