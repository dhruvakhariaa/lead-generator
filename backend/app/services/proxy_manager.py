# app/services/proxy_manager.py
import logging
import threading
import time
import random
import requests
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ProxyMetrics:
    """Track proxy performance metrics"""
    failures: int = 0
    successes: int = 0
    response_times: List[float] = None
    last_used: float = 0
    is_quarantined: bool = False
    quarantine_end: float = 0
    reliability_score: float = 1.0
    total_requests: int = 0
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

class ProxyProvider(ABC):
    """Abstract base class for proxy providers"""
    
    @abstractmethod
    async def fetch_proxies(self) -> List[str]:
        """Fetch proxies from this provider"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name"""
        pass

class FreeProxyProvider(ProxyProvider):
    """Free proxy list provider"""
    
    def __init__(self, urls: List[str]):
        self.urls = urls
    
    async def fetch_proxies(self) -> List[str]:
        all_proxies = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for url in self.urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            text = await response.text()
                            proxies = [p.strip() for p in text.strip().split('\n') if p.strip()]
                            all_proxies.extend(proxies)
                            logger.info(f"[Proxy] Fetched {len(proxies)} proxies from {url}")
                except Exception as e:
                    logger.warning(f"[Proxy] Failed to fetch from {url}: {e}")
        return list(set(all_proxies))  # Remove duplicates
    
    def get_name(self) -> str:
        return "FreeProxyProvider"

class PaidProxyProvider(ProxyProvider):
    """Paid proxy service provider"""
    
    def __init__(self, api_url: str, api_key: str, format_type: str = "txt"):
        self.api_url = api_url
        self.api_key = api_key
        self.format_type = format_type
    
    async def fetch_proxies(self) -> List[str]:
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(self.api_url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        proxies = [p.strip() for p in text.strip().split('\n') if p.strip()]
                        logger.info(f"[Proxy] Fetched {len(proxies)} paid proxies")
                        return proxies
        except Exception as e:
            logger.error(f"[Proxy] Failed to fetch paid proxies: {e}")
        return []
    
    def get_name(self) -> str:
        return f"PaidProxyProvider({self.api_url})"

class AdvancedProxyManager:
    """Advanced proxy manager with multiple sources, validation, and intelligent rotation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.proxies: Dict[str, ProxyMetrics] = {}
        self.providers: List[ProxyProvider] = []
        self.lock = threading.RLock()  # Reentrant lock for complex operations
        self.rotation_pool: List[str] = []
        self.weighted_pool: List[Tuple[str, float]] = []
        self.last_fetch_time = 0
        self.fetch_interval = config.get('fetch_interval', 300)  # 5 minutes
        self.min_pool_size = config.get('min_pool_size', 10)
        self.max_failures = config.get('max_failures', 3)
        self.quarantine_duration = config.get('quarantine_duration', 600)  # 10 minutes
        self.validation_timeout = config.get('validation_timeout', 5)
        self.max_response_time_history = config.get('max_response_time_history', 50)
        
        # Initialize providers
        self._initialize_providers()
        
        # User agents for stealth
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def _initialize_providers(self):
        """Initialize proxy providers from config"""
        # Free providers
        free_sources = self.config.get('free_sources', [])
        if free_sources:
            self.providers.append(FreeProxyProvider(free_sources))
        
        # Paid providers
        paid_providers = self.config.get('paid_providers', [])
        for provider_config in paid_providers:
            self.providers.append(PaidProxyProvider(
                provider_config['api_url'],
                provider_config['api_key'],
                provider_config.get('format', 'txt')
            ))
    
    async def validate_proxy(self, proxy: str, test_urls: List[str] = None) -> Tuple[bool, float]:
        """Validate proxy with multiple test URLs and return success + response time"""
        if test_urls is None:
            test_urls = ['http://httpbin.org/ip', 'http://icanhazip.com', 'https://api.ipify.org']
        
        proxy_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        for test_url in test_urls:
            start_time = time.time()
            try:
                connector = aiohttp.TCPConnector()
                timeout = aiohttp.ClientTimeout(total=self.validation_timeout)
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={'User-Agent': random.choice(self.user_agents)}
                ) as session:
                    proxy_url = f'http://{proxy}'
                    async with session.get(test_url, proxy=proxy_url) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            logger.debug(f"[Proxy] Validated {proxy} - {response_time:.2f}s")
                            return True, response_time
            except Exception as e:
                logger.debug(f"[Proxy] Validation failed for {proxy} on {test_url}: {e}")
                continue
        
        return False, float('inf')
    
    async def fetch_and_validate_proxies(self) -> int:
        """Fetch proxies from all providers and validate them"""
        logger.info("[Proxy] Starting proxy fetch and validation")
        new_proxies = []
        
        # Fetch from all providers
        for provider in self.providers:
            try:
                provider_proxies = await provider.fetch_proxies()
                new_proxies.extend(provider_proxies)
                logger.info(f"[Proxy] {provider.get_name()} provided {len(provider_proxies)} proxies")
            except Exception as e:
                logger.error(f"[Proxy] Error fetching from {provider.get_name()}: {e}")
        
        # Remove duplicates
        unique_proxies = list(set(new_proxies))
        logger.info(f"[Proxy] Total unique proxies to validate: {len(unique_proxies)}")
        
        # Validate proxies in batches
        batch_size = 20
        valid_count = 0
        
        for i in range(0, len(unique_proxies), batch_size):
            batch = unique_proxies[i:i + batch_size]
            validation_tasks = [self.validate_proxy(proxy) for proxy in batch]
            
            try:
                results = await asyncio.gather(*validation_tasks, return_exceptions=True)
                
                for proxy, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.debug(f"[Proxy] Validation exception for {proxy}: {result}")
                        continue
                    
                    is_valid, response_time = result
                    if is_valid:
                        with self.lock:
                            if proxy not in self.proxies:
                                self.proxies[proxy] = ProxyMetrics()
                            # Update initial response time
                            self.proxies[proxy].response_times.append(response_time)
                            valid_count += 1
                        logger.debug(f"[Proxy] Added valid proxy: {proxy}")
            
            except Exception as e:
                logger.error(f"[Proxy] Batch validation error: {e}")
        
        logger.info(f"[Proxy] Validated {valid_count} proxies successfully")
        return valid_count
    
    def _calculate_reliability_score(self, metrics: ProxyMetrics) -> float:
        """Calculate proxy reliability score based on performance"""
        if metrics.total_requests == 0:
            return 1.0
        
        success_rate = metrics.successes / metrics.total_requests
        avg_response_time = sum(metrics.response_times) / len(metrics.response_times) if metrics.response_times else float('inf')
        
        # Normalize response time (consider anything under 2s as good)
        time_score = max(0, 1 - (avg_response_time - 2) / 10) if avg_response_time != float('inf') else 0
        
        # Combine success rate and response time
        reliability = 0.7 * success_rate + 0.3 * time_score
        return max(0.1, min(1.0, reliability))  # Keep between 0.1 and 1.0
    
    def _update_rotation_pool(self):
        """Update rotation pool with weighted random selection"""
        with self.lock:
            current_time = time.time()
            available_proxies = []
            
            for proxy, metrics in self.proxies.items():
                # Check if proxy is quarantined
                if metrics.is_quarantined:
                    if current_time > metrics.quarantine_end:
                        metrics.is_quarantined = False
                        metrics.failures = 0
                        logger.info(f"[Proxy] Released {proxy} from quarantine")
                    else:
                        continue
                
                # Update reliability score
                metrics.reliability_score = self._calculate_reliability_score(metrics)
                available_proxies.append((proxy, metrics.reliability_score))
            
            if not available_proxies:
                logger.warning("[Proxy] No available proxies in pool")
                self.rotation_pool = []
                self.weighted_pool = []
                return
            
            # Sort by reliability score (descending)
            available_proxies.sort(key=lambda x: x[1], reverse=True)
            
            # Create weighted pool with randomization
            total_weight = sum(score for _, score in available_proxies)
            if total_weight > 0:
                normalized_weights = [(proxy, score / total_weight) for proxy, score in available_proxies]
            else:
                normalized_weights = [(proxy, 1.0 / len(available_proxies)) for proxy, _ in available_proxies]
            
            # Shuffle to break patterns while maintaining weights
            random.shuffle(normalized_weights)
            
            self.rotation_pool = [proxy for proxy, _ in normalized_weights]
            self.weighted_pool = normalized_weights
            
            logger.info(f"[Proxy] Updated rotation pool with {len(self.rotation_pool)} proxies")
            
            # Alert if pool is low
            if len(self.rotation_pool) < self.min_pool_size:
                logger.warning(f"[Proxy] Proxy pool below minimum size: {len(self.rotation_pool)}/{self.min_pool_size}")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy using weighted random selection"""
        with self.lock:
            if not self.weighted_pool:
                logger.warning("[Proxy] No proxies available in rotation pool")
                return None
            
            # Weighted random selection
            rand_val = random.random()
            cumulative_weight = 0
            
            for proxy, weight in self.weighted_pool:
                cumulative_weight += weight
                if rand_val <= cumulative_weight:
                    self.proxies[proxy].last_used = time.time()
                    return proxy
            
            # Fallback to last proxy if weights don't add up perfectly
            proxy = self.weighted_pool[-1][0]
            self.proxies[proxy].last_used = time.time()
            return proxy
    
    def report_success(self, proxy: str, response_time: float):
        """Report successful proxy usage"""
        with self.lock:
            if proxy in self.proxies:
                metrics = self.proxies[proxy]
                metrics.successes += 1
                metrics.total_requests += 1
                metrics.response_times.append(response_time)
                
                # Keep response time history bounded
                if len(metrics.response_times) > self.max_response_time_history:
                    metrics.response_times.pop(0)
                
                # Reduce failure count on success
                metrics.failures = max(0, metrics.failures - 1)
                
                # Remove from quarantine if applicable
                if metrics.is_quarantined:
                    metrics.is_quarantined = False
                    logger.info(f"[Proxy] Removed {proxy} from quarantine due to success")
    
    def report_failure(self, proxy: str, error_type: str = "unknown"):
        """Report proxy failure with quarantine logic"""
        with self.lock:
            if proxy in self.proxies:
                metrics = self.proxies[proxy]
                metrics.failures += 1
                metrics.total_requests += 1
                
                logger.debug(f"[Proxy] Failure reported for {proxy}: {error_type} (total failures: {metrics.failures})")
                
                # Quarantine logic
                if metrics.failures >= self.max_failures:
                    metrics.is_quarantined = True
                    metrics.quarantine_end = time.time() + self.quarantine_duration
                    logger.warning(f"[Proxy] Quarantined {proxy} for {self.quarantine_duration/60:.1f} minutes")
                    
                    # Update rotation pool to exclude quarantined proxy
                    self._update_rotation_pool()
    
    async def refresh_proxies_if_needed(self):
        """Refresh proxy pool if needed"""
        current_time = time.time()
        
        if current_time - self.last_fetch_time > self.fetch_interval:
            logger.info("[Proxy] Refreshing proxy pool")
            
            try:
                valid_count = await self.fetch_and_validate_proxies()
                if valid_count > 0:
                    self.last_fetch_time = current_time
                    self._update_rotation_pool()
                    logger.info(f"[Proxy] Refresh complete: {valid_count} valid proxies")
                else:
                    logger.warning("[Proxy] No valid proxies found during refresh")
            except Exception as e:
                logger.error(f"[Proxy] Error during proxy refresh: {e}")
    
    def get_proxy_stats(self) -> Dict:
        """Get current proxy statistics"""
        with self.lock:
            total_proxies = len(self.proxies)
            available_proxies = len([p for p in self.proxies.values() if not p.is_quarantined])
            quarantined_proxies = total_proxies - available_proxies
            
            avg_response_time = 0
            if self.proxies:
                all_times = []
                for metrics in self.proxies.values():
                    all_times.extend(metrics.response_times)
                if all_times:
                    avg_response_time = sum(all_times) / len(all_times)
            
            return {
                "total_proxies": total_proxies,
                "available_proxies": available_proxies,
                "quarantined_proxies": quarantined_proxies,
                "rotation_pool_size": len(self.rotation_pool),
                "avg_response_time": round(avg_response_time, 3),
                "last_refresh": self.last_fetch_time
            }
    
    def get_random_user_agent(self) -> str:
        """Get random user agent for stealth"""
        return random.choice(self.user_agents)
    
    def is_enabled(self) -> bool:
        """Check if proxy manager has available proxies"""
        return len(self.rotation_pool) > 0

# Configuration template
PROXY_CONFIG = {
    'free_sources': [
        'https://proxy-list.download/api/v1/get?type=http',
        'https://proxy-list.download/api/v1/get?type=https',
        'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
    ],
    'paid_providers': [
        # Example paid provider configuration
        # {
        #     'api_url': 'https://rotating-residential.proxymesh.com:31280',
        #     'api_key': 'your-api-key',
        #     'format': 'txt'
        # }
    ],
    'fetch_interval': 300,  # 5 minutes
    'min_pool_size': 10,
    'max_failures': 3,
    'quarantine_duration': 600,  # 10 minutes
    'validation_timeout': 5,
    'max_response_time_history': 50
}

# Global instance
proxy_manager = AdvancedProxyManager(PROXY_CONFIG)