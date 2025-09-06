# app/services/proxy_manager.py
import requests
from typing import Optional, Dict, List
from threading import Lock
import logging
from app.services.interfaces import ProxyService

logger = logging.getLogger(__name__)

class RobustProxyManager(ProxyService):
    def __init__(self, proxy_count: int = 7, max_failures: int = 3, auto_fetch: bool = True):
        self.proxies: List[str] = []
        self.index = 0
        self.lock = Lock()
        self.proxy_count = proxy_count
        self.failure_counts: Dict[str, int] = {}
        self.max_failures = max_failures
        self.enabled = False
        
        if auto_fetch:
            self.enabled = self._safe_fetch_proxies()

    def _safe_fetch_proxies(self) -> bool:
        """Safely fetch proxies without blocking startup"""
        try:
            response = requests.get(
                "https://www.proxy-list.download/api/v1/get?type=http", 
                timeout=10
            )
            if response.status_code == 200:
                proxies_raw = response.text.strip().split("\r\n")
                self.proxies = [p.strip() for p in proxies_raw if p.strip()][:self.proxy_count]
                self.failure_counts = {p: 0 for p in self.proxies}
                logger.info(f"[ProxyManager] Fetched {len(self.proxies)} free proxies.")
                return True
            else:
                logger.warning(f"[ProxyManager] Failed to fetch proxies: status {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"[ProxyManager] Error fetching proxies: {str(e)} - continuing without proxies")
            return False

    def get_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation, thread-safe."""
        if not self.enabled or not self.proxies:
            return None
            
        with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.index]
            self.index = (self.index + 1) % len(self.proxies)
            return proxy

    def report_failure(self, proxy: str) -> None:
        """Report a proxy failure and remove if it exceeds max_failures."""
        if not self.enabled:
            return
            
        with self.lock:
            if proxy in self.failure_counts:
                self.failure_counts[proxy] += 1
                if self.failure_counts[proxy] >= self.max_failures:
                    logger.info(f"[ProxyManager] Removing failed proxy: {proxy}")
                    self.proxies.remove(proxy)
                    del self.failure_counts[proxy]
                    if self.index >= len(self.proxies):
                        self.index = 0

    def is_enabled(self) -> bool:
        """Check if proxy service is enabled"""
        return self.enabled

# Fail-safe proxy manager
class NullProxyManager(ProxyService):
    """Null object pattern for when proxies are disabled"""
    
    def get_proxy(self) -> Optional[str]:
        return None
    
    def report_failure(self, proxy: str) -> None:
        pass

# Global instance with safe initialization
try:
    proxy_manager = RobustProxyManager()
    logger.info("✅ Proxy manager initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Proxy manager initialization failed: {e} - using null manager")
    proxy_manager = NullProxyManager()
