from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .routers import auth
from .database import config as database_config

app = FastAPI(
    title="Auth Service API",
    description="API for user authentication and authorization",
    version="1.0.0"
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

@app.on_event("startup")
async def startup_event():
    print("Auth Service: Starting up...")
    await database_config.init_db()
    print("Auth Service: Database initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Auth Service: Shutting down.")
    await database_config.close_db()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for service and DB connectivity.
    """
    try:
        async with database_config.get_session() as session:
            await session.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "auth-service",
            "database": "connected"
        }
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {e}"
        )

@app.get("/")
async def read_root():
    return {"message": "Welcome to Auth Service"}
