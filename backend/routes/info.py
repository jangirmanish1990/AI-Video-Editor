"""GET /ops — the registered edit operations, for the UI reference panel."""
from fastapi import APIRouter

from backend.processing.registry import list_ops

router = APIRouter()


@router.get("/ops")
async def ops():
    return list_ops()
