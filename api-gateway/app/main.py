# api-gateway/app/main.py

from fastapi import FastAPI
from .middleware import JWTAuthMiddleware
from .routers import auth, template, render

app = FastAPI(
    title="API Gateway",
    description="Gateway for all microservices.",
)

# Define public routes to be excluded from JWT validation
PUBLIC_ROUTES = [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/health",
    "/"
]

# Add the JWTAuthMiddleware to the application
app.add_middleware(JWTAuthMiddleware, public_routes=PUBLIC_ROUTES)

# Include routers for each microservice
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(template.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(render.router, prefix="/api/v1/render", tags=["Render"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the API Gateway"}

@app.get("/health")
def health_check():
    return {"status": "ok"}