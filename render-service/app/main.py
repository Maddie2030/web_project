
# render-service/app/main.py

from fastapi import FastAPI
from app.routers.render import router as render_router

app = FastAPI(
    title="Render Service API",
    description="Generate images and PDFs from templates."
)

app.include_router(render_router)


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Render Service is up and running."}
