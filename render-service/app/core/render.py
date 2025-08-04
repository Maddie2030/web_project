import os
import requests
import uuid
import logging
from fastapi import HTTPException, status
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from app.schemas.render import TemplateServiceResponse, ImageRenderRequest

# Set up logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"
FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf" 

class RenderingCore:
    """
    Encapsulates all core rendering logic, including API calls, image manipulation,
    and PDF generation, with comprehensive error handling and logging.
    """

    def __init__(self, request: ImageRenderRequest):
        self.request = request
        self.template = self._fetch_template()

    def _fetch_template(self) -> TemplateServiceResponse:
        """Fetches template metadata from the template-service."""
        logger.info(f"Fetching template metadata for ID: {self.request.template_id}")
        if not TEMPLATE_SERVICE_URL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TEMPLATE_SERVICE_URL is not configured."
            )
        try:
            template_url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{self.request.template_id}"
            response = requests.get(template_url)
            response.raise_for_status()
            template_data = response.json()
            return TemplateServiceResponse(**template_data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch template from template-service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch template metadata: {e}"
            )
        except Exception as e:
            logger.error(f"Invalid template data received: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid template data received: {e}"
            )

    def _render_text_on_image(self, image: Image.Image) -> Image.Image:
        """Draws user text onto a provided PIL image."""
        draw = ImageDraw.Draw(image)
        for i, block_request in enumerate(self.request.text_data):
            if i >= len(self.template.text_blocks):
                logger.warning(f"Too much text data provided for template {self.template.id}. Ignoring extra.")
                break
            template_block = self.template.text_blocks[i]
            try:
                font = ImageFont.truetype(FONT_PATH, template_block.font_size)
            except IOError:
                logger.warning(f"Font not found at {FONT_PATH}. Using default font.")
                font = ImageFont.load_default()
            
            draw.text(
                (template_block.x, template_block.y),
                block_request.user_text,
                fill=template_block.color,
                font=font
            )
        return image

    def generate_image(self) -> str:
        """Generates a customized image and returns its saved path."""
        logger.info(f"Starting image generation for template ID: {self.template.id}")
        background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(self.template.image_path))
        if not os.path.exists(background_path):
            logger.error(f"Background image not found at {background_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Background image not found at path: {background_path}"
            )
        try:
            image = Image.open(background_path)
            image = self._render_text_on_image(image)
            
            os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
            image.save(output_path)
            logger.info(f"Image saved successfully at {output_path}")
            return output_path
        except IOError as e:
            logger.error(f"File I/O error during image generation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to load or save image file."
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred during image generation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to generate image: {e}"
            )

    def generate_pdf(self) -> str:
        """Generates a customized PDF and returns its saved path."""
        logger.info(f"Starting PDF generation for template ID: {self.template.id}")
        image_path = self.generate_image()
        try:
            image_url_for_html = f"file://{image_path}"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
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
            pdf_filename = f"{uuid.uuid4()}.pdf"
            pdf_path = os.path.join(STATIC_OUTPUTS_PATH, pdf_filename)
            html.write_pdf(pdf_path)
            logger.info(f"PDF saved successfully at {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Failed to generate PDF with WeasyPrint: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {e}"
            )