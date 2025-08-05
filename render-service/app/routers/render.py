#render-service/app/routers/render.py

import os
import uuid
from fastapi import APIRouter, HTTPException, status
from app.schemas.render import (
    ImageRenderRequest,
    ImageRenderResponse,
    PDFRenderResponse,
)
from app.core.render import RenderingCore

router = APIRouter(prefix="/api/v1", tags=["render"])


@router.post(
    "/generate-image",
    response_model=ImageRenderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_image_endpoint(request: ImageRenderRequest):
    """
    Generate a PNG image from a template with user-provided text.
    """
    try:
        path = RenderingCore(request).generate_image()
    except HTTPException as e:
        raise e
    filename = os.path.basename(path)
    return ImageRenderResponse(image_url=f"/static/outputs/{filename}")


@router.post(
    "/generate-pdf",
    response_model=PDFRenderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_pdf_endpoint(request: ImageRenderRequest):
    """
    Generate a PDF from a template, embedding the rendered image.
    """
    try:
        path = RenderingCore(request).generate_pdf()
    except HTTPException as e:
        raise e
    filename = os.path.basename(path)
    return PDFRenderResponse(pdf_url=f"/static/outputs/{filename}")
