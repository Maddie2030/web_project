#api-gateway/app/routers/template.py

# api-gateway/app/routers/template.py
from fastapi import APIRouter, Request, HTTPException, Response, status
import httpx
from ..settings import settings

router = APIRouter()
client = httpx.AsyncClient()

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_template_request(path: str, request: Request):
    """Forwards requests to the Template service."""
    url = f"{settings.TEMPLATE_SERVICE_URL}{request.url.path}"

    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=await request.body(),
        )

        filtered_headers = {
            k: v for k, v in response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
        }

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=filtered_headers,
            media_type=response.headers.get("content-type"),
        )
    except httpx.ConnectError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Template Service is unavailable: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )