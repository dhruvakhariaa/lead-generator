# app/main.py
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Database services (both Instagram and Jobs)
from app.services.database import db_service
from app.services.job_database import job_db_service
from app.services.service_factory import ServiceFactory

# Routers
from app.routers.scraper import router as scraper_router
from app.routers.job_scraper import router as job_scraper_router
from app.routers.monitoring import router as monitoring_router
from app.routers.export import router as export_router

from app.utils.config import settings
from bson import ObjectId
import json
import os
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for Playwright on Windows
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Lead Generator API...")
    
    # Connect to databases with error handling
    try:
        await db_service.connect()
        logger.info("✅ Instagram database connected")
    except Exception as e:
        logger.error(f"❌ Instagram database connection failed: {e}")
        if not settings.DEVELOPMENT_MODE:
            raise
    
    try:
        await job_db_service.connect()
        logger.info("✅ Jobs database connected")
    except Exception as e:
        logger.error(f"❌ Jobs database connection failed: {e}")
        if not settings.DEVELOPMENT_MODE:
            raise
    
    # Log service availability
    services = ServiceFactory.get_available_services()
    logger.info(f"📊 Service availability: {services}")
    
    yield
    
    # Cleanup
    logger.info("🧹 Shutting down Lead Generator API...")
    try:
        await db_service.disconnect()
        await job_db_service.disconnect()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"⚠️ Error during shutdown: {e}")

app = FastAPI(
    title="Lead Generator API - Instagram & Jobs",
    version="2.1.0",
    description="AI-powered lead generation with robust service separation",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper_router, prefix="/api")
app.include_router(job_scraper_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with service status"""
    services = ServiceFactory.get_available_services()
    
    return {
        "message": "Lead Generator API - Instagram & Jobs",
        "version": "2.1.0",
        "status": "running",
        "development_mode": settings.DEVELOPMENT_MODE,
        "features": [
            "Instagram user scraping (Apify + Playwright)",
            "Multi-platform job scraping (Indeed, Glassdoor, Google Jobs)",
            "Remote work & contract job focus",
            "Advanced filtering and search",
            "JSON export capabilities",
            "Robust service separation",
            "Graceful service degradation"
        ],
        "services": services,
        "documentation": "Visit /docs for API documentation",
        "health_check": "Visit /health to check database connectivity"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check with service status"""
    health_status = {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "databases": {},
        "services": ServiceFactory.get_available_services(),
        "development_mode": settings.DEVELOPMENT_MODE
    }
    
    # Test Instagram database
    try:
        await db_service.db.command("ping")
        health_status["databases"]["instagram"] = "connected"
    except Exception as e:
        health_status["databases"]["instagram"] = f"disconnected: {str(e)}"
        if not settings.DEVELOPMENT_MODE:
            health_status["status"] = "unhealthy"
    
    # Test Jobs database
    try:
        await job_db_service.db.command("ping")
        health_status["databases"]["jobs"] = "connected"
    except Exception as e:
        health_status["databases"]["jobs"] = f"disconnected: {str(e)}"
        if not settings.DEVELOPMENT_MODE:
            health_status["status"] = "unhealthy"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)