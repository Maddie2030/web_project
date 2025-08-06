#api-gateway/app/routers/render.py

from fastapi import APIRouter, Request, HTTPException
import httpx
import os

router = APIRouter()
RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "http://render-service:8000")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_render_request(path: str, request: Request):
    """Forwards requests to the Render service."""
    async with httpx.AsyncClient() as client:
        url = f"{RENDER_SERVICE_URL}/{path}"
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=request.headers,
                params=request.query_params,
                content=await request.body()
            )
            return response.json()
        except httpx.ConnectError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")