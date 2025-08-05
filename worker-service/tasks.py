#worker-service/tasks.py

from celery import Celery
import requests
import os
import uuid
from PIL import Image, ImageDraw, ImageFont
from pydantic import ValidationError

from app.celery_app import celery_app
from app.schemas.render import TemplateServiceResponse, ImageRenderResponse

# Constants from the render-service
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://template-service:8000")
STATIC_OUTPUTS_PATH = "/app/static/outputs"
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

@celery_app.task(bind=True, name="render.tasks.generate_image_task")
def generate_image_task(self, template_id: str, text_data: list):
    """
    Generates a custom image from a template with user-provided text.
    This task runs in the background.
    """
    try:
        # 1. Make internal HTTP request to template-service
        response = requests.get(f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{template_id}")
        response.raise_for_status()
        template = TemplateServiceResponse(**response.json())
    except requests.exceptions.RequestException as e:
        self.update_state(state='FAILURE', meta={'reason': f"Failed to fetch template metadata: {e}"})
        raise
    except ValidationError:
        self.update_state(state='FAILURE', meta={'reason': "Invalid template data received from template-service."})
        raise
    
    # 2. Load background image from static/backgrounds
    background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
    if not os.path.exists(background_path):
        self.update_state(state='FAILURE', meta={'reason': f"Background image not found at {background_path}."})
        raise FileNotFoundError(f"Background image not found at {background_path}.")

    try:
        image = Image.open(background_path)
    except IOError as e:
        self.update_state(state='FAILURE', meta={'reason': f"Failed to load background image: {e}"})
        raise
    
    draw = ImageDraw.Draw(image)

    # 3. Iterate and draw text onto the image
    if len(template.text_blocks) != len(text_data):
        self.update_state(state='FAILURE', meta={'reason': "Mismatched number of text blocks."})
        raise ValueError("Number of text blocks in template does not match user data.")

    for template_block, user_text_block in zip(template.text_blocks, text_data):
        try:
            font = ImageFont.truetype(FONT_PATH, template_block.font_size)
        except IOError:
            font = ImageFont.load_default()
        
        draw.text(
            (template_block.x, template_block.y),
            user_text_block['user_text'],
            fill=template_block.color,
            font=font
        )
    
    # Ensure output directory exists
    os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)

    # 4. Save the generated image with a unique filename
    unique_filename = f"{uuid.uuid4()}.png"
    output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
    try:
        image.save(output_path)
    except Exception as e:
        self.update_state(state='FAILURE', meta={'reason': f"Failed to save generated image: {e}"})
        raise

    # 5. Return URL of the generated image
    image_url = f"/static/outputs/{unique_filename}"
    return image_url