#render-service/app/render.py

import os
import uuid
import logging
import requests
from fastapi import HTTPException, status
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from app.schemas.render import (
    ImageRenderRequest,
    TemplateServiceResponse,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"
FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf"


class RenderingCore:
    """Core logic for rendering images and PDFs from templates."""

    def __init__(self, request: ImageRenderRequest):
        self.request = request
        self.template = self._fetch_template()

    def _fetch_template(self) -> TemplateServiceResponse:
        """Fetch and validate template metadata."""
        if not TEMPLATE_SERVICE_URL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TEMPLATE_SERVICE_URL is not configured."
            )

        url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{self.request.template_id}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            return TemplateServiceResponse(**resp.json())
        except requests.RequestException as e:
            logger.error("Template fetch error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch template: {e}"
            )
        except Exception as e:
            logger.error("Template validation error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid template data: {e}"
            )

    def _load_background(self) -> Image.Image:
        """Load the background image from disk."""
        path = os.path.join(
            STATIC_BACKGROUNDS_PATH,
            os.path.basename(self.template.image_path)
        )
        if not os.path.exists(path):
            logger.error("Background not found: %s", path)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Background image not found at {path}"
            )

        try:
            return Image.open(path)
        except IOError as e:
            logger.error("Pillow load error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load background image."
            )

    def _render_text(self, image: Image.Image) -> Image.Image:
        """Draw user text onto image using template metadata."""
        draw = ImageDraw.Draw(image)
        for idx, block_meta in enumerate(self.template.text_blocks):
            user_text = (
                self.request.text_data[idx].user_text
                if idx < len(self.request.text_data)
                else block_meta.default_text
            )
            try:
                font = ImageFont.truetype(FONT_PATH, block_meta.font_size)
            except IOError:
                font = ImageFont.load_default()

            draw.text(
                (block_meta.x, block_meta.y),
                user_text,
                fill=block_meta.color,
                font=font
            )
        return image

    def _save_file(self, image: Image.Image, ext: str) -> str:
        """Save an image or PDF and return its path."""
        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(STATIC_OUTPUTS_PATH, filename)
        try:
            if ext.lower() == "png":
                image.save(path)
            else:
                # For PDF, image is HTML rendered via WeasyPrint
                pass
            return path
        except Exception as e:
            logger.error("Save file error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {e}"
            )

    def generate_image(self) -> str:
        """Generate and save a PNG image; return its filesystem path."""
        img = self._load_background()
        img = self._render_text(img)
        return self._save_file(img, "png")

    def generate_pdf(self) -> str:
        """Generate and save a PDF; return its filesystem path."""
        image_path = self.generate_image()
        html = HTML(string=f"""
            <!DOCTYPE html>
            <html><body style="margin:0;padding:0">
            <img src="file://{image_path}" style="width:100%;height:auto" />
            </body></html>
        """, base_url=".")
        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(STATIC_OUTPUTS_PATH, pdf_filename)
        try:
            html.write_pdf(pdf_path)
            return pdf_path
        except Exception as e:
            logger.error("PDF generation error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {e}"
            )
