"""FastAPI application entrypoint.

Run locally:  uvicorn backend.main:app --reload
Run on Railway: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes import batch, edit, info, jobs, upload

app = FastAPI(title="AI Video Editor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(upload.router)
app.include_router(edit.router)
app.include_router(jobs.router)
app.include_router(info.router)
app.include_router(batch.router)
