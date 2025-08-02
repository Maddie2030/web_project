# app/main.py
from fastapi import FastAPI
from app.routers.render import router as render_router

app = FastAPI(
    title="Render Service API",
    description="A microservice for generating rendered documents and images from templates."
)

app.include_router(render_router)

@app.get("/")
def read_root():
    return {"message": "Hello, World! Render Service is up and running."}