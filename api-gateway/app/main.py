# api-gateway/app/main.py

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .middleware import JWTAuthMiddleware
from .routers import auth, template, render
from .settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(
    title="API Gateway",
    description="Gateway for all microservices.",
)

# --- Middleware ---

# 1. Logging Middleware: Logs every incoming request and its response time.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Outgoing Response: {response.status_code} processed in {process_time:.4f}s")
    return response

# 2. CORS Middleware: Allows cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    # Use the allow_origins from your settings object for production.
    # For development, you can set it to ["*"].
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. JWT Auth Middleware: Protects routes and validates tokens.
app.add_middleware(JWTAuthMiddleware, public_routes=settings.public_routes)

# --- Routers ---

# Include routers for each microservice with correct, non-overlapping prefixes.
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(render.router, prefix="/api/v1/render", tags=["Render"])

# --- Root Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the API Gateway"}

@app.get("/health")
def health_check():
    return {"status": "ok"}