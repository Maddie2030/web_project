#api-gateway/app/routers/template.py

from fastapi import APIRouter, Request, HTTPException
import httpx
import os

router = APIRouter()
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://template-service:8000")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_template_request(path: str, request: Request):
    """Forwards requests to the Template service."""
    async with httpx.AsyncClient() as client:
        url = f"{TEMPLATE_SERVICE_URL}/api/v1/templates/{path}"

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