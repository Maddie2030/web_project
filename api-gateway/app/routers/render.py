#api-gateway/app/routers/render.py

from fastapi import APIRouter, Request, HTTPException, Response
import httpx
import os

router = APIRouter()
RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "http://render-service:8003")

# Headers that should NOT be forwarded per HTTP spec (hop-by-hop headers)
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade"
}

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def forward_render_request(path: str, request: Request):
    """Forwards requests to the Render service with full status/header/content propagation."""
    url = f"{RENDER_SERVICE_URL}{request.url.path}"
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove 'host' header

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
        # Only propagate safe headers, not hop-by-hop (per HTTP spec)
        filtered_headers = {k: v for k, v in response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=filtered_headers,
            media_type=response.headers.get("content-type"),
        )
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
