# app/services/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Protocol
from datetime import datetime

class ScrapingService(Protocol):
    """Protocol for scraping services"""
    
    async def __aenter__(self):
        """Async context manager entry"""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        ...

class InstagramScrapingService(ScrapingService):
    """Interface for Instagram scraping services"""
    
    @abstractmethod
    async def scrape_users(
        self, 
        niche: str, 
        min_followers: int, 
        max_results: int = 100, 
        target_count: int = 10
    ) -> List[Dict]:
        """Scrape Instagram users by niche"""
        pass
    
    @abstractmethod
    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """Scrape detailed profile information"""
        pass

class JobScrapingService(ScrapingService):
    """Interface for job scraping services"""
    
    @abstractmethod
    async def scrape_jobs(
        self,
        keywords: str,
        location: str = "remote",
        job_type: str = "contract",
        max_results: int = 10,
        platforms: List[str] = ["indeed", "glassdoor", "google"]
    ) -> List[Dict]:
        """Scrape jobs from various platforms"""
        pass

class ProxyService(ABC):
    """Interface for proxy management"""
    
    @abstractmethod
    def get_proxy(self) -> Optional[str]:
        """Get next available proxy"""
        pass
    
    @abstractmethod
    def report_failure(self, proxy: str) -> None:
        """Report proxy failure"""
        pass

class SessionService(ABC):
    """Interface for session management"""
    
    @abstractmethod
    async def load_cookies(self) -> Optional[List[Dict]]:
        """Load session cookies"""
        pass
    
    @abstractmethod
    async def save_cookies(self, cookies: List[Dict]) -> None:
        """Save session cookies"""
        pass