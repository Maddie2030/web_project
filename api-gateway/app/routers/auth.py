# api-gateway/app/routers/auth.py

from fastapi import APIRouter, Request, HTTPException, Response, status
import httpx
import os

router = APIRouter()

# Create a global httpx.AsyncClient to be reused (manage lifecycle separately if possible)
client = httpx.AsyncClient()

# Get the downstream auth service URL from environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

# List of hop-by-hop headers that should NOT be forwarded to the client
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

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def forward_auth_request(path: str, request: Request):
    # Preserve the full original path to properly forward prefix /api/v1/auth and subpaths
    url = f"{AUTH_SERVICE_URL}{request.url.path}"

    # Copy and make headers mutable
    headers = dict(request.headers)
    # Remove Host header to avoid issues forwarding to downstream service
    headers.pop("host", None)

    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=await request.body(),
        )

        # Filter out hop-by-hop headers before returning response
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
            detail=f"Auth Service is unavailable: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )
