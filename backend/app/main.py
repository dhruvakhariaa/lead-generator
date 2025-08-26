from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.services.database import db_service
from app.routers.scraper import router as scraper_router
from app.routers.monitoring import router as monitoring_router 
from app.utils.config import settings
from bson import ObjectId
import json
import os
import asyncio

# Fix for Playwright on Windows: Use SelectorEventLoopPolicy to support subprocesses
if os.name == 'nt':  # Check if running on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_service.connect()
    yield
    await db_service.disconnect()

app = FastAPI(
    title="Instagram Lead Generator API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper_router, prefix="/api")
app.include_router(monitoring_router, prefix="/metrics")

@app.get("/")
async def root():
    """Root endpoint for basic API info"""
    return {
        "message": "Instagram Lead Generator API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "Visit /docs for API documentation",
        "health_check": "Visit /health to check database connectivity"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity verification"""
    try:
        # Test database connection by performing a simple operation
        await db_service.db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "version": "1.0.0",
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)