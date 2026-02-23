# app/services/service_factory.py
from typing import Optional, Dict, Any
import logging
from app.utils.config import settings
from app.services.interfaces import InstagramScrapingService, JobScrapingService
from app.services.proxy_manager import proxy_manager, AdvancedProxyManager
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)

class ServiceFactory:
    """Factory for creating and managing services"""
    
    _instagram_services = {}
    _job_services = {}
    
    @classmethod
    def create_instagram_scraper(
        cls, 
        service_type: str = "apify", 
        fallback: bool = True
    ) -> Optional[InstagramScrapingService]:
        """Create Instagram scraping service with fallback support"""
        
        if service_type == "apify":
            return cls._create_apify_scraper(fallback)
        elif service_type == "playwright":
            return cls._create_playwright_instagram_scraper()
        else:
            logger.error(f"Unknown Instagram service type: {service_type}")
            return None
    
    @classmethod
    def _create_apify_scraper(cls, fallback: bool = True) -> Optional[InstagramScrapingService]:
        """Create Apify scraper with optional fallback"""
        try:
            if not settings.APIFY_API_TOKEN:
                logger.warning("APIFY_API_TOKEN not set - Apify scraper unavailable")
                if fallback:
                    return cls._create_playwright_instagram_scraper()
                return None
            
            from app.services.apify_scraper import ApifyScraper
            return ApifyScraper()
        except Exception as e:
            logger.error(f"Failed to create Apify scraper: {e}")
            if fallback:
                return cls._create_playwright_instagram_scraper()
            return None
    
    @classmethod
    def _create_playwright_instagram_scraper(cls) -> Optional[InstagramScrapingService]:
        """Create Playwright Instagram scraper"""
        try:
            from app.services.instagram_playwright_scraper import InstagramPlaywrightScraper
            return InstagramPlaywrightScraper()
        except Exception as e:
            logger.error(f"Failed to create Playwright Instagram scraper: {e}")
            return None
    
    @classmethod
    def create_job_scraper(cls, service_type: str = "playwright") -> Optional[JobScrapingService]:
        """Create job scraping service"""
        
        if service_type == "playwright":
            return cls._create_playwright_job_scraper()
        else:
            logger.error(f"Unknown job service type: {service_type}")
            return None
    
    @classmethod
    def _create_playwright_job_scraper(cls) -> Optional[JobScrapingService]:
        """Create Playwright job scraper"""
        try:
            from app.services.playwright_job_scraper import PlaywrightJobScraper
            return PlaywrightJobScraper()
        except Exception as e:
            logger.error(f"Failed to create Playwright job scraper: {e}")
            return None

    @classmethod
    def get_available_services(cls) -> Dict[str, Dict[str, bool]]:
        """Get status of available services"""
        return {
            "instagram": {
                "apify": bool(settings.APIFY_API_TOKEN),
                "playwright": True  # Always available
            },
            "jobs": {
                "playwright": True  # Always available
            },
            "proxy": proxy_manager.is_enabled() if hasattr(proxy_manager, 'is_enabled') else False
        }