#render-service/app/core/render.py

import os
import requests
import uuid
import logging
from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML
from textwrap import wrap

from app.schemas.render import TemplateServiceResponse, ImageRenderRequest, TextBlockRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL")
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
        # Use default system font
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
            logger.warning(f"Could not load default font, using load_default()")
            return ImageFont.load_default()

def _hex_or_tuple(color: str | None, default: str = "#000000"):
    """Convert hex color or return default."""
    return color if color else default

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

class RenderingCore:
    def __init__(self, request: ImageRenderRequest):
        self.request = request
        self.template = self._fetch_template()

    def _fetch_template(self) -> TemplateServiceResponse:
        """Fetch template metadata from template service."""
        logger.info(f"Fetching template metadata for ID: {self.request.template_id}")
        if not TEMPLATE_SERVICE_URL:
            raise HTTPException(status_code=500, detail="TEMPLATE_SERVICE_URL is not configured.")

        try:
            template_url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{self.request.template_id}"
            response = requests.get(template_url)
            response.raise_for_status()
            return TemplateServiceResponse(**response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch template from template-service: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch template metadata: {e}")
        except Exception as e:
            logger.error(f"Invalid template data received: {e}")
            raise HTTPException(status_code=500, detail=f"Invalid template data received: {e}")

    def _process_block(self, ui_block: TextBlockRequest):
        """
        Process a single text block from the frontend.
        Since frontend provides all necessary data, we use it directly.
        """
        logger.info(f"Processing block: {ui_block.title} with text length: {len(ui_block.user_text) if ui_block.user_text else 0}")
        
        # Don't skip blocks with text - even if it looks empty, it might have content
        if not ui_block.user_text:
            logger.warning(f"Block '{ui_block.title}' has no text, skipping.")
            return None
        
        # Use the data directly from frontend since it's complete
        processed = {
            "title": ui_block.title,
            "text": ui_block.user_text.strip() if ui_block.user_text else '',
            "x": max(0, ui_block.x),  # Ensure non-negative
            "y": max(0, ui_block.y),  # Ensure non-negative
            "width": max(10, ui_block.width),
            "height": max(10, ui_block.height),
            "font_size": max(8, min(72, ui_block.font_size)),  # Clamp font size
            "color": _hex_or_tuple(ui_block.color, "#000000"),
            "font_path": ui_block.font_path,
            "bold": ui_block.bold,
            "italic": ui_block.italic,
            "max_width": max(50, ui_block.max_width if ui_block.max_width else ui_block.width),
            "type": ui_block.type
        }
        
        logger.info(f"Processed block '{processed['title']}' at ({processed['x']}, {processed['y']}) - Font: {processed['font_size']}px - Max width: {processed['max_width']}px")
        return processed

    def _render_text_on_image(self, image: Image.Image) -> Image.Image:
        """Render all text blocks on the image."""
        draw = ImageDraw.Draw(image)
        
        logger.info(f"Rendering {len(self.request.text_data)} text blocks on image")
        
        processed_count = 0
        skipped_count = 0

        for i, ui_block in enumerate(self.request.text_data):
            logger.info(f"Processing block {i+1}/{len(self.request.text_data)}: {ui_block.title}")
            
            processed = self._process_block(ui_block)
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
        return image

    def generate_image(self) -> str:
        """Generate the final image with all text overlays."""
        logger.info(f"Starting image generation for template ID: {self.template.id}")

        # Construct background image path
        background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(self.template.image_path))
        if not os.path.exists(background_path):
            logger.error(f"Background image not found at {background_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Background image not found at path: {background_path}"
            )
        
        try:
            # Load and process the background image
            image = Image.open(background_path).convert("RGBA")
            logger.info(f"Loaded background image: {image.size[0]}x{image.size[1]}")
            
            # Render text on the image
            image = self._render_text_on_image(image)
            
            # Ensure output directory exists
            os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
            
            # Generate unique filename and save
            unique_filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
            image.save(output_path, format="PNG", quality=95)
            
            logger.info(f"Image saved successfully at {output_path}")
            return output_path
            
        except IOError as e:
            logger.error(f"File I/O error during image generation: {e}")
            raise HTTPException(status_code=500, detail="Failed to load or save image file.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during image generation: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate image: {e}")

    def generate_pdf(self) -> str:
        """Generate PDF from the generated image."""
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
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
