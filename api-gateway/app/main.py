# api-gateway/app/main.py

import time
import logging

from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

from .middleware import JWTAuthMiddleware
from .routers import auth, template, render
from .settings import settings

from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
from fastapi_limiter.depends import RateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(
    title="API Gateway",
    description="Gateway for all microservices.",
)

# Create a global httpx client for forwarding requests
client = httpx.AsyncClient()


@app.on_event("startup")
async def startup():
    redis = Redis(host="redis", port=6379, db=0)
    await FastAPILimiter.init(redis)


@app.on_event("shutdown")
async def shutdown():
    # Close all global clients gracefully
    await client.aclose()
    await FastAPILimiter.close()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


settings.public_routes = [
    "/",
    "/health",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/docs",
    "/openapi.json",
    # Add the static files path to the public routes
    "/static/{path:path}" 
]


app.add_middleware(JWTAuthMiddleware, public_routes=settings.public_routes)


# --- NEW: Router for Static Files ---
@app.api_route("/static/{path:path}", methods=["GET"])
async def forward_static_files(path: str, request: Request):
    """
    Forwards requests for static files to the Template Service.
    This handles both backgrounds and rendered outputs.
    """
    template_service_url = settings.TEMPLATE_SERVICE_URL
    url = f"{template_service_url}/static/{path}"

    try:
        response = await client.request(
            method="GET",
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"}
        )
        response.raise_for_status()

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={
                "Content-Type": response.headers.get("content-type"),
                "Content-Length": response.headers.get("content-length"),
            },
            media_type=response.headers.get("content-type")
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error forwarding static file: {e.response.text}")
    except httpx.ConnectError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Template Service is unavailable")


# --- Your existing routers ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(render.router, prefix="/api/v1/render", tags=["Render"])


@app.get("/", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def root():
    return {"message": "Welcome to the API Gateway"}


@app.get("/health", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def health_check():
    return {"status": "ok"}