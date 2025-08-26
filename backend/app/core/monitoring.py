# app/services/monitoring.py
from fastapi import APIRouter
from typing import Dict, Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/metrics", tags=["monitoring"])

# In-memory metrics (expand to DB if needed)
_metrics: Dict = {
    "total_runs": 0,
    "total_yields": 0,
    "total_errors": 0,
    "last_run_time": None,
    "last_yield_count": 0,
    "last_error": None
}

async def send_alert(message: str):
    """Simple alert (expand to email/Slack)."""
    print(f"[ALERT] {datetime.now().isoformat()}: {message}")

@router.get("/")
async def get_metrics() -> Dict:
    """Endpoint to fetch scraping metrics."""
    return _metrics

def record_run(yield_count: int, error: Optional[str] = None):
    """Log a scrape run, alert if low yields or error."""
    _metrics["total_runs"] += 1
    _metrics["last_run_time"] = datetime.now().isoformat()
    if error:
        _metrics["total_errors"] += 1
        _metrics["last_error"] = error
        asyncio.create_task(send_alert(f"Scrape error: {error}"))
    else:
        _metrics["total_yields"] += yield_count
        _metrics["last_yield_count"] = yield_count
        if yield_count < 5:  # Alert threshold
            asyncio.create_task(send_alert(f"Low yield: only {yield_count} users scraped"))