# app/services/proxy_manager.py
import requests
from typing import Optional, Dict, List
from threading import Lock

class ProxyManager:
    def __init__(self, proxy_count: int = 7, max_failures: int = 3):
        self.proxies: List[str] = []
        self.index = 0
        self.lock = Lock()
        self.proxy_count = proxy_count
        self.failure_counts: Dict[str, int] = {}
        self.max_failures = max_failures
        self.fetch_proxies()  # Initial fetch

    def fetch_proxies(self) -> None:
        """Fetch free HTTP proxies from a public source."""
        try:
            response = requests.get("https://www.proxy-list.download/api/v1/get?type=http")
            if response.status_code == 200:
                proxies_raw = response.text.strip().split("\r\n")
                self.proxies = [p.strip() for p in proxies_raw if p.strip()][:self.proxy_count]
                self.failure_counts = {p: 0 for p in self.proxies}
                print(f"[ProxyManager] Fetched {len(self.proxies)} free proxies.")
            else:
                print(f"[ProxyManager] Failed to fetch proxies: status {response.status_code}")
        except Exception as e:
            print(f"[ProxyManager] Error fetching proxies: {str(e)}")

    def get_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation, thread-safe."""
        with self.lock:
            if not self.proxies:
                self.fetch_proxies()
                if not self.proxies:
                    return None
            proxy = self.proxies[self.index]
            self.index = (self.index + 1) % len(self.proxies)
            return proxy

    def report_failure(self, proxy: str) -> None:
        """Report a proxy failure and remove if it exceeds max_failures."""
        with self.lock:
            if proxy in self.failure_counts:
                self.failure_counts[proxy] += 1
                if self.failure_counts[proxy] >= self.max_failures:
                    print(f"[ProxyManager] Removing failed proxy: {proxy}")
                    self.proxies.remove(proxy)
                    del self.failure_counts[proxy]
                    if self.index >= len(self.proxies):
                        self.index = 0
                    if len(self.proxies) < self.proxy_count:
                        self.fetch_proxies()  # Refill if low

# Global instance for use in other services
proxy_manager = ProxyManager()