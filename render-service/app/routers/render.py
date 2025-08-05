# render-service/app/routers/render.py

import os
from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel
from celery import chain
from app.celery_app import celery_app
from app.schemas.render import ImageRenderRequest, ImageRenderResponse, PDFRenderResponse

# Schemas for the asynchronous response
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None

class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str

router = APIRouter(prefix="/api/v1", tags=["render"])

@router.post(
    "/generate-image",
    response_model=TaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_image_endpoint(request: ImageRenderRequest):
    """
    Sends a request to generate a custom image to the worker service.
    """
    task = celery_app.send_task(
        'render.tasks.generate_image_task',
        args=[request.model_dump()],
        queue='render_queue'
    )
    return TaskQueuedResponse(
        task_id=task.id,
        status="Task queued. Use GET /api/v1/tasks/{task_id} to check status."
    )

@router.post(
    "/generate-pdf",
    response_model=TaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_pdf_endpoint(request: ImageRenderRequest):
    """
    Sends a request to generate a PDF to the worker service using a task chain.
    """
    # Create a task chain: generate image first, then generate PDF from that image.
    task_chain = chain(
        celery_app.signature('render.tasks.generate_image_task', args=[request.model_dump()]),
        celery_app.signature('render.tasks.generate_pdf_from_image_task')
    )
    
    task_result = task_chain.apply_async(queue='render_queue')
    
    return TaskQueuedResponse(
        task_id=task_result.id,
        status="Task queued. Use GET /api/v1/tasks/{task_id} to check status."
    )