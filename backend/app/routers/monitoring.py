from fastapi import APIRouter
from app.core.monitoring import get_metrics

router = APIRouter(prefix="/metrics", tags=["monitoring"])

@router.get("/")
async def metrics():
    return get_metrics()