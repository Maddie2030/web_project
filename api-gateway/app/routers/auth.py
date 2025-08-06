# api-gateway/app/routers/auth.py

from fastapi import APIRouter, Request, HTTPException, Response, status
import httpx
import os

router = APIRouter()

# Instantiate a single httpx.AsyncClient for reuse
# This is more efficient as it manages the connection pool.
client = httpx.AsyncClient()

# Get the downstream service URL from environment variables
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_auth_request(path: str, request: Request):
    """Forwards all requests to the Authentication service."""
    url = f"{AUTH_SERVICE_URL}/{path}"

    try:
        # Forward the request, including headers, body, and query parameters
        # Note: We create a copy of the headers and remove the host header
        # to prevent routing issues with the downstream service.
        headers = request.headers.mutablecopy()
        if "host" in headers:
            del headers["host"]
            
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=await request.body()
        )
        
        # Return the response as is, preserving headers and status code
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers
        )
    except httpx.ConnectError as e:
        # Handle cases where the downstream service is unreachable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth Service is unavailable: {e}"
        )
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )