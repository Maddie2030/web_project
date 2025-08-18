#worker-service/app/tasks.py
import os
import uuid
import requests
import logging
from pydantic import ValidationError
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from app.celery_app import celery_app
from app.schemas.render import ImageRenderRequest, TemplateServiceResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://template-service:8000")
STATIC_BACKGROUNDS_PATH = "/app/static/backgrounds"
STATIC_OUTPUTS_PATH = "/app/static/outputs"
DEFAULT_FONT_PATH = "/usr/share/fonts/dejavu/DejaVuSans.ttf"

# Font mapping for system fonts
SYSTEM_FONTS = {
    'Arial (system)': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'Roboto': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'Open Sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'Lato': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'Montserrat': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    'Verdana': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'Georgia': '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
    'Courier New': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    'Times New Roman': '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
    'Trebuchet MS': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
}

def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    """Enhanced font loading that handles system fonts and fallbacks."""
    if not font_path or font_path == "":
        try:
            return ImageFont.truetype(DEFAULT_FONT_PATH, size)
        except Exception:
            logger.warning(f"Could not load default font, using load_default()")
            return ImageFont.load_default()
    
    # Check if it's a system font name
    if font_path in SYSTEM_FONTS:
        font_path = SYSTEM_FONTS[font_path]
    
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        logger.warning(f"Could not load font at '{font_path}': {e}, using default.")
        try:
            return ImageFont.truetype(DEFAULT_FONT_PATH, size)
        except Exception:
            return ImageFont.load_default()

def _draw_text(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font, fill: str, bold: bool = False, italic: bool = False):
    """Draw text with bold simulation if needed."""
    if bold:
        # Simulate bold by multiple passes
        for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
            draw.text((x+dx, y+dy), text, font=font, fill=fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)

def _draw_wrapped_text(draw, x, y, text, font, fill, max_width: int, bold: bool, italic: bool):
    """Enhanced text wrapping that handles multi-line text and proper line breaks."""
    if not text or not text.strip():
        return
        
    # Handle escaped newlines from frontend
    text = text.replace('\\n', '\n')
    
    # If max_width is not set or very small, use a reasonable default
    if not max_width or max_width < 50:
        max_width = 300
    
    # Handle multi-line text (split by \n first)
    lines = text.split('\n')
    all_wrapped_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            all_wrapped_lines.append("")
            continue
        
        # Check if line fits in max_width
        try:
            line_width = draw.textlength(line, font=font)
        except AttributeError:
            line_width = draw.textsize(line, font=font)[0]
        
        if line_width <= max_width:
            # Line fits, add as is
            all_wrapped_lines.append(line)
        else:
            # Line needs wrapping
            words = line.split()
            if not words:
                all_wrapped_lines.append("")
                continue
            
            current_line = words[0]
            
            for word in words[1:]:
                test_line = f"{current_line} {word}"
                try:
                    test_width = draw.textlength(test_line, font=font)
                except AttributeError:
                    test_width = draw.textsize(test_line, font=font)[0]
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    all_wrapped_lines.append(current_line)
                    current_line = word
            
            all_wrapped_lines.append(current_line)
    
    # Calculate line height
    try:
        line_height = font.getbbox('Ag')[3] + 2  # Height of 'Ag' plus spacing
    except:
        line_height = int(font.size * 1.3)
    
    # Draw each line
    for i, line in enumerate(all_wrapped_lines):
        if line:  # Only draw non-empty lines
            line_y = y + (i * line_height)
            _draw_text(draw, x, line_y, line, font, fill, bold, italic)

def _process_block(ui_block_data: dict):
    """Process a single text block from the frontend data."""
    title = ui_block_data.get('title', 'unknown')
    user_text = ui_block_data.get('user_text', '')
    
    logger.info(f"Processing block: {title} with text length: {len(user_text)}")
    
    # Don't skip blocks with text - even if it looks empty, it might have content
    if not user_text:
        logger.warning(f"Block '{title}' has no text, skipping.")
        return None
    
    processed = {
        "title": title,
        "text": user_text.strip() if user_text else '',
        "x": max(0, ui_block_data.get("x", 0)),  # Ensure non-negative
        "y": max(0, ui_block_data.get("y", 0)),  # Ensure non-negative
        "width": max(10, ui_block_data.get("width", 100)),
        "height": max(10, ui_block_data.get("height", 50)),
        "font_size": max(8, min(72, ui_block_data.get("font_size", 16))),  # Clamp font size
        "color": ui_block_data.get("color", "#000000"),
        "font_path": ui_block_data.get("font_path"),
        "bold": bool(ui_block_data.get("bold", False)),
        "italic": bool(ui_block_data.get("italic", False)),
        "max_width": max(50, ui_block_data.get("max_width", ui_block_data.get("width", 400))),
        "type": ui_block_data.get("type", "TEXT")
    }
    
    logger.info(f"Processed block '{processed['title']}' at ({processed['x']}, {processed['y']}) - Font size: {processed['font_size']}px - Max width: {processed['max_width']}px")
    return processed

@celery_app.task(bind=True, name="render.tasks.generate_image_task")
def generate_image_task(self, request_data: dict) -> str:
    """Generates an image from a template and returns its absolute file path."""
    try:
        logger.info(f"Starting image generation task")
        
        # Validate request data
        request = ImageRenderRequest(**request_data)
        logger.info(f"Processing {len(request.text_data)} text blocks")
        
        # Fetch template metadata
        response = requests.get(f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{request.template_id}")
        response.raise_for_status()
        template = TemplateServiceResponse(**response.json())
        
        logger.info(f"Fetched template: {template.name} (ID: {template.id})")

        # Load background image
        background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(template.image_path))
        if not os.path.exists(background_path):
            raise FileNotFoundError(f"Background image not found at path: {background_path}")

        image = Image.open(background_path).convert("RGBA")
        logger.info(f"Loaded background image: {image.size[0]}x{image.size[1]}")
        draw = ImageDraw.Draw(image)

        # Process each text block
        processed_count = 0
        skipped_count = 0
        
        for i, block_data in enumerate(request.text_data):
            logger.info(f"Processing block {i+1}/{len(request.text_data)}")
            
            # Convert Pydantic model to dict for processing
            if hasattr(block_data, 'dict'):
                block_dict = block_data.dict()
            else:
                block_dict = block_data
                
            processed = _process_block(block_dict)
            if not processed:
                skipped_count += 1
                continue

            try:
                font = _load_font(processed["font_path"], processed["font_size"])
                
                # Ensure coordinates are within image bounds but don't be too restrictive
                x = max(0, min(processed["x"], image.width - 50))
                y = max(0, min(processed["y"], image.height - 50))
                
                _draw_wrapped_text(
                    draw=draw,
                    x=x,
                    y=y,
                    text=processed["text"],
                    font=font,
                    fill=processed["color"],
                    max_width=processed["max_width"],
                    bold=processed["bold"],
                    italic=processed["italic"],
                )
                
                processed_count += 1
                logger.info(f"✅ Successfully rendered block '{processed['title']}'")
                
            except Exception as e:
                logger.error(f"❌ Failed to render block '{processed['title']}': {e}")
                skipped_count += 1
                continue

        logger.info(f"Rendering complete: {processed_count} successful, {skipped_count} skipped")

        # Save the generated image
        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        filename = f"{uuid.uuid4()}.png"
        output_path = os.path.join(STATIC_OUTPUTS_PATH, filename)
        image.save(output_path, format="PNG", quality=95)
        
        logger.info(f"Image saved successfully at {output_path}")
        return output_path

    except Exception as e:
        error_message = f"Task failed: {type(e).__name__} - {str(e)}"
        logger.error(f"Error in generate_image_task: {error_message}")
        raise e

@celery_app.task(bind=True, name="render.tasks.generate_pdf_from_image_task")
def generate_pdf_from_image_task(self, image_path: str) -> str:
    """Generates a PDF from an image path provided by a previous task."""
    try:
        logger.info(f"Starting PDF generation from image: {image_path}")
        
        html = HTML(string=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ margin: 0; padding: 0; }}
                    img {{ max-width: 100%; height: auto; display: block; }}
                </style>
            </head>
            <body>
                <img src="file://{image_path}" style="width:100%;height:auto" />
            </body>
            </html>
        """, base_url=".")
        
        os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = os.path.join(STATIC_OUTPUTS_PATH, pdf_filename)
        
        html.write_pdf(pdf_path)
        logger.info(f"PDF saved successfully at {pdf_path}")
        
        # Clean up temporary image file
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"Cleaned up temporary image file: {image_path}")

        return f"/static/outputs/{pdf_filename}"

    except Exception as e:
        error_message = f"PDF generation failed: {type(e).__name__} - {str(e)}"
        logger.error(f"Error in generate_pdf_from_image_task: {error_message}")
        raise e
