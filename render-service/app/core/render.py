#render-service/app/render.py

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


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    # Fallback to default if missing
    path = font_path or DEFAULT_FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        logger.warning(f"Could not load font at '{path}', using default.")
        return ImageFont.load_default()

def _hex_or_tuple(color: str | None, default: str = "#000000"):
    return color if color else default

def _draw_text(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font, fill: str, bold: bool = False, italic: bool = False):
    # Simulate bold by multiple passes (simple, works broadly)
    if bold:
        for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
            draw.text((x+dx, y+dy), text, font=font, fill=fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)

def _draw_wrapped_text(draw, x, y, text, font, fill, max_width: int | None, bold: bool, italic: bool):
    if not max_width:
        _draw_text(draw, x, y, text, font, fill, bold, italic)
        return

    # Simple word wrapping by measuring line width
    words = text.split()
    if not words:
        return

    lines = []
    current = words[0]
    for w in words[1:]:
        w_test = f"{current} {w}"
        w_px = draw.textlength(w_test, font=font)
        if w_px <= max_width:
            current = w_test
        else:
            lines.append(current)
            current = w
    lines.append(current)

    line_height = font.size + int(font.size * 0.35)
    for i, line in enumerate(lines):
        _draw_text(draw, x, y + i * line_height, line, font, fill, bold, italic)


class RenderingCore:
    def __init__(self, request: ImageRenderRequest):
        self.request = request
        self.template = self._fetch_template()

    def _fetch_template(self) -> TemplateServiceResponse:
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

    def _merge_block(self, ui_block: TextBlockRequest):
        # find matching default by title
        defaults_map = {b.title.lower(): b for b in self.template.text_blocks}
        default = defaults_map.get(ui_block.title.lower())
        if not default:
            logger.warning(f"No template block for title '{ui_block.title}', skipping.")
            return None

        # choose user override or fallback
        merged = {
            "title": ui_block.title,
            "text": ui_block.user_text if ui_block.user_text is not None else default.default_text,
            "x": ui_block.x if ui_block.x is not None else default.x,
            "y": ui_block.y if ui_block.y is not None else default.y,
            "width": ui_block.width if ui_block.width is not None else default.width,
            "height": ui_block.height if ui_block.height is not None else default.height,
            "font_size": ui_block.font_size if ui_block.font_size is not None else default.font_size,
            "color": _hex_or_tuple(ui_block.color, default.color),
            "font_path": ui_block.font_path if ui_block.font_path is not None else default.font_path,
            "bold": default.bold if ui_block.bold is None else ui_block.bold,
            "italic": default.italic if ui_block.italic is None else ui_block.italic,
            "max_width": ui_block.max_width if ui_block.max_width is not None else default.max_width,
        }
        return merged

    def _render_text_on_image(self, image: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(image)

        for ui_block in self.request.text_data:
            merged = self._merge_block(ui_block)
            if not merged:
                continue

            font = _load_font(merged["font_path"], merged["font_size"])
            _draw_wrapped_text(
                draw=draw,
                x=merged["x"],
                y=merged["y"],
                text=merged["text"],
                font=font,
                fill=merged["color"],
                max_width=merged["max_width"] or merged["width"],
                bold=merged["bold"],
                italic=merged["italic"],
            )

        return image

    def generate_image(self) -> str:
        logger.info(f"Starting image generation for template ID: {self.template.id}")

        background_path = os.path.join(STATIC_BACKGROUNDS_PATH, os.path.basename(self.template.image_path))
        if not os.path.exists(background_path):
            logger.error(f"Background image not found at {background_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Background image not found at path: {background_path}"
            )
        try:
            image = Image.open(background_path).convert("RGBA")
            image = self._render_text_on_image(image)
            os.makedirs(STATIC_OUTPUTS_PATH, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}.png"
            output_path = os.path.join(STATIC_OUTPUTS_PATH, unique_filename)
            image.save(output_path, format="PNG")
            logger.info(f"Image saved successfully at {output_path}")
            return output_path
        except IOError as e:
            logger.error(f"File I/O error during image generation: {e}")
            raise HTTPException(status_code=500, detail="Failed to load or save image file.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during image generation: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate image: {e}")

    def generate_pdf(self) -> str:
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
