# app/services/session_manager.py
from pathlib import Path
from typing import Optional, List, Dict
import json
import random
import asyncio
from datetime import datetime

class SessionManager:
    def __init__(self, cookie_file: str = "cookies.json", refresh_interval_min: int = 8, refresh_interval_max: int = 10):
        self.cookie_file = Path(cookie_file)
        self.refresh_interval = random.randint(refresh_interval_min, refresh_interval_max)
        self.run_count = 0
        self.cookies: Optional[List[Dict]] = None
        self.lock = asyncio.Lock()
        self.last_refresh = datetime.now()

    async def load_cookies(self) -> Optional[List[Dict]]:
        """Load cookies from file asynchronously."""
        async with self.lock:
            if self.cookie_file.exists():
                try:
                    with open(self.cookie_file, "r") as f:
                        self.cookies = json.load(f)
                    print(f"[SessionManager] Loaded {len(self.cookies)} cookies from {self.cookie_file}")
                    return self.cookies
                except Exception as e:
                    print(f"[SessionManager] Error loading cookies: {str(e)}")
            return None

    async def save_cookies(self, cookies: List[Dict]) -> None:
        """Save cookies to file asynchronously."""
        async with self.lock:
            try:
                with open(self.cookie_file, "w") as f:
                    json.dump(cookies, f, indent=4)
                print(f"[SessionManager] Saved {len(cookies)} cookies to {self.cookie_file}")
            except Exception as e:
                print(f"[SessionManager] Error saving cookies: {str(e)}")

    async def should_refresh(self) -> bool:
        """Check if session should be refreshed based on run count."""
        async with self.lock:
            self.run_count += 1
            if self.run_count >= self.refresh_interval:
                self.run_count = 0
                self.refresh_interval = random.randint(8, 10)  # Randomize for next cycle
                self.last_refresh = datetime.now()
                print(f"[SessionManager] Refresh triggered after {self.refresh_interval} runs")
                return True
            return False

# Global instance
session_manager = SessionManager()