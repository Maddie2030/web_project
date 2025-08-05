#worker-service/app/tasks.py
# worker-service/app/tasks.py

import os
import uuid
import requests
from pydantic import ValidationError
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML
from celery import chain

from app.celery_app import celery_app
from app.schemas.render import ImageRenderRequest, TemplateServiceResponse

TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://template-service:8000")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"
FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf"

@celery_app.task(bind=True, name="render.tasks.generate_image_task")
def generate_image_task(self, request_data: dict) -> str:
    """Generates an image from a template and returns its absolute file path."""
    try:
        request = ImageRenderRequest(**request_data)
        response = requests.get(f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{request.template_id}")
        response.raise_for_status()
        template = TemplateServiceResponse(**response.json())

        background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"Background image not found at path: {background_path}")

        image = Image.open(background_path)
        draw = ImageDraw.Draw(image)

        for idx, block_meta in enumerate(template.text_blocks):
            user_text = request.text_data[idx].user_text if idx < len(request.text_data) else block_meta.default_text
            try:
                font = ImageFont.truetype(FONT_PATH, block_meta.font_size)
            except IOError:
                font = ImageFont.load_default()
            draw.text((block_meta.x, block_meta.y), user_text, fill=block_meta.color, font=font)

        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(STATIC_OUTPUTS_PATH, filename)
        image.save(output_path)
        
        return output_path

    except (requests.exceptions.RequestException, ValidationError, FileNotFoundError, Exception) as e:
        error_message = f"Task failed: {type(e).__name__} - {e}"
        self.update_state(state='FAILURE', meta={'reason': error_message})
        print(f"Error in generate_image_task: {error_message}")
        raise Exception(error_message)

@celery_app.task(bind=True, name="render.tasks.generate_pdf_from_image_task")
def generate_pdf_from_image_task(self, image_path: str) -> str:
    """Generates a PDF from an image path provided by a previous task."""
    try:
        html = HTML(string=f"""
            <!DOCTYPE html>
            <html><body style="margin:0;padding:0">
            <img src="file://{image_path}" style="width:100%;height:auto" />
            </body></html>
        """, base_url=".")
        
        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(STATIC_OUTPUTS_PATH, pdf_filename)
        
        html.write_pdf(pdf_path)
        return f"/static/outputs/{pdf_filename}"

    except Exception as e:
        error_message = f"PDF generation failed: {type(e).__name__} - {e}"
        self.update_state(state='FAILURE', meta={'reason': error_message})
        print(f"Error in generate_pdf_from_image_task: {error_message}")
        raise Exception(error_message)