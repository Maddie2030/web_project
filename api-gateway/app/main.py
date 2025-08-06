# api-gateway/app/main.py

import time
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
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

@app.on_event("startup")
async def startup():
    redis = Redis(host="redis", port=6379, db=0)
    await FastAPILimiter.init(redis)

@app.on_event("shutdown")
async def shutdown():
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

app.add_middleware(JWTAuthMiddleware, public_routes=settings.public_routes)  # or the explicit list

# -- Fix the render router prefix if render-service does not mount `/render`! --
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(render.router, prefix="/api/v1/render", tags=["Render"])

@app.get("/", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def root():
    return {"message": "Welcome to the API Gateway"}

@app.get("/health", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def health_check():
    return {"status": "ok"}
