# app/services/apify_scraper.py
# app/services/apify_scraper.py

from apify_client import ApifyClient
from app.utils.config import settings
from app.utils.helpers import parse_follower_count, clean_username
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio
import re
import random
import traceback
import uuid
import itertools
import math
from random import shuffle

# monitoring helper (your monitoring module)
from app.core.monitoring import record_run

class ApifyScraper:
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_API_TOKEN)
        # actor IDs
        self.HASHTAG_SCRAPER_ID = "apify/instagram-hashtag-scraper"
        self.PROFILE_SCRAPER_ID = "apify/instagram-profile-scraper"
        self.POST_SCRAPER_ID = "apify/instagram-post-scraper"
        self.SEARCH_SCRAPER_ID = "apify/instagram-search-scraper"

    async def __aenter__(self):
        """Async entry for context manager: No additional setup needed beyond __init__."""
        if not self.client:
            raise ValueError("ApifyClient not initialized in __init__")
        print("[ApifyScraper] Entering async context")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit for context manager: Cleanup (no-op for ApifyClient, but log if error occurred)."""
        print("[ApifyScraper] Exiting async context")
        if exc_type:
            print(f"[ApifyScraper] Context exited with error: {exc_type.__name__} - {exc_val}")
        return False # Let exceptions propagate for caller handling

    def _uniq_run_label(self, prefix: str) -> str:
        return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

    # -------------------- utility wrappers to avoid blocking the event loop --------------------
    async def _call_actor(self, actor_id: str, run_input: dict) -> dict:
        """Run Apify actor in a thread to avoid blocking asyncio loop, forcing a fresh run."""
        # Strong cache busters
        run_input = {
            **run_input,
            "maxRequestRetries": 0, # fail fast, no hidden retries that can reuse state
            "maxConcurrency": 8, # a bit of parallelism
            "proxyConfiguration": run_input.get("proxyConfiguration") or {"useApifyProxy": True},
        }

        # Set unique meta to ensure a new run and dataset
        run_meta = {
            "build": "latest",
            "memory_mbytes": 1024,
            "timeout_secs": 1800,
        }

        unique_tag = self._uniq_run_label("run")

        def call():
            actor = self.client.actor(actor_id)
            # Use .start() for a guaranteed new run (not reusing a previous finished run)
            run = actor.start(run_input=run_input, **run_meta)
            # Wait for finish explicitly so we can read dataset right after
            run = self.client.run(run["id"]).wait_for_finish()
            return run

        return await asyncio.to_thread(call)

    async def _collect_dataset_items(self, dataset_id: str) -> List[Dict]:
        """Collect dataset items (iterate_items is blocking) in a thread."""
        def collect():
            items = []
            try:
                for itm in self.client.dataset(dataset_id).iterate_items():
                    items.append(itm)
            except Exception:
                # swallow; return what we have
                pass
            return items
        return await asyncio.to_thread(collect)

    async def get_actor_run_info(self, run_id: str) -> Dict:
        try:
            def get_run():
                return self.client.run(run_id).get()
            return await asyncio.to_thread(get_run)
        except Exception:
            return {}

    # -------------------- public scraping functions --------------------
    async def scrape_users(
        self,
        niche: str,
        min_followers: int,
        max_results: int = 100,
        target_count: int = 10,
        max_attempts: int = 5,
    ) -> List[Dict]:
        """
        Collect users whose follower_count >= min_followers using Apify actors.
        FIXED: Now returns partial results instead of empty array when under target.
        """
        try:
            print(f"🔍 Apify: Starting user scraping for #{niche} (target {target_count})")
            filtered_users = []
            seen_usernames = set()
            base_limit = 50
            modes_cycle = itertools.cycle(["top", "recent", "top", "recent"])

            for attempt in range(1, max_attempts + 1):
                if len(filtered_users) >= target_count:
                    break

                # Randomize mode and limit each time
                mode = next(modes_cycle)
                jitter = random.randint(-10, 40)
                limit = max(40, min(500, base_limit + jitter))

                print(f"🔄 Attempt {attempt}/{max_attempts} – mode {mode} – limit {limit}")

                # slight jitter before actor call
                await asyncio.sleep(random.uniform(1.0, 3.0))

                # fetch usernames via hashtag actor (non-blocking wrapper)
                try:
                    all_usernames, run_id = await self._get_usernames_from_hashtag(niche, limit)
                except Exception as e:
                    print(f"❌ Apify hashtag call failed: {e}")
                    all_usernames, run_id = [], ""

                print(f"📊 Actor returned {len(all_usernames)} raw usernames")

                # if low yield, try search actor as a fallback
                if len(all_usernames) < 20:
                    print("🔁 Low yield from hashtag actor — trying search actor fallback")
                    try:
                        search_names, search_run = await self._get_usernames_from_search(niche, limit, mode=mode)
                        if search_names:
                            # merge unique
                            merged = list(set(all_usernames) | set(search_names))
                            all_usernames = merged
                            run_id = search_run or run_id
                            print(f"📊 Search actor returned additional {len(search_names)} usernames")
                    except Exception:
                        pass

                # check run info for potential errors/speed throttling
                try:
                    run_info = await asyncio.to_thread(lambda: self.client.run(run_id).get() if run_id else {})
                    if run_info and run_info.get("status") != "SUCCEEDED":
                        print(f"⚠️ Actor run status: {run_info.get('status')}")
                except Exception:
                    pass

                # dedupe against seen
                new_usernames = [u for u in all_usernames if u not in seen_usernames]
                seen_usernames.update(new_usernames)

                print(f"📊 {len(new_usernames)} new usernames after de-dupe")

                if not new_usernames:
                    print("⚠️ No new usernames — expanding limit for next attempt")
                    base_limit = min(base_limit + 50, 500)
                    await asyncio.sleep(2 + random.random() * 3)
                    continue

                # fetch basic profile info in batches and filter by follower count
                batch_users = await self._get_users_batch_info(new_usernames)
                print(f"📊 Got {len(batch_users)} profile results")

                for u in batch_users:
                    if not u:
                        continue
                    if u.get("follower_count", 0) >= min_followers:
                        u.update(niche=niche, scraped_at=datetime.utcnow().isoformat())
                        filtered_users.append(u)
                        print(f"✅ @{u['username']} ({u['follower_count']:,}) added")

                        if len(filtered_users) >= target_count:
                            break

                # backoff jitter
                if len(filtered_users) < target_count:
                    delay = 5 * (attempt ** 1.5) + random.uniform(1, 3)
                    print(f"⏳ Sleeping {delay:.1f}s before next attempt")
                    await asyncio.sleep(delay)

                    if len(new_usernames) < 20:
                        base_limit = min(base_limit + 50, 500)
                        print(f"📈 Increasing base_limit to {base_limit}")

            filtered_users = filtered_users[:max_results]

            # FIXED: Return partial results instead of empty array
            if len(filtered_users) < target_count:
                print(f"⚠️ Apify collected {len(filtered_users)}/{target_count} users — will allow Playwright to add more")
            else:
                print(f"✅ Apify reached target with {len(filtered_users)} valid users")

            record_run(len(filtered_users), error=None)
            return filtered_users  # FIXED: Always return what we have

        except Exception as exc:
            print("❌ Unexpected error in Apify.scrape_users:", exc)
            traceback.print_exc()
            record_run(0, error=str(exc))
            return []

    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """Detailed profile via Apify profile actor, plus posts and engagement metrics"""
        try:
            print(f"👤 Apify: Scraping detailed profile for @{username}")
            profile = await self._get_detailed_profile(username)
            if not profile:
                print(f"⚠️ Apify did not return profile for @{username}")
                return None
            if not profile.get("is_private", True):
                posts = await self._get_user_posts(username, limit=12)
                profile["recent_posts"] = posts
                profile["engagement_rate"] = self._calculate_engagement_rate(posts, profile.get("follower_count", 0))
                profile["top_hashtags"] = self._extract_top_hashtags(posts)
            else:
                profile["recent_posts"] = []
                profile["engagement_rate"] = 0.0
                profile["top_hashtags"] = []
            profile["scraped_at"] = datetime.utcnow().isoformat()
            return profile
        except Exception as e:
            print(f"❌ scrape_profile error: {e}")
            return None

    # -------------------- internal actor helpers --------------------
    async def _get_usernames_from_hashtag(self, niche: str, limit: int = 200) -> Tuple[List[str], str]:
        """Run hashtag actor and collect usernames (owner and mentions)."""
        try:
            run_input = {
                "hashtags": [niche],
                "resultsLimit": limit,
                "addParentData": False,
                "searchLimit": 1,
                "proxyConfiguration": {"useApifyProxy": True}
            }
            run = await self._call_actor(self.HASHTAG_SCRAPER_ID, run_input)
            ds_id = run.get("defaultDatasetId")
            items = await self._collect_dataset_items(ds_id) if ds_id else []
            names = set()
            for itm in items:
                owner = itm.get("ownerUsername") or itm.get("owner", {}).get("username")
                if owner:
                    c = clean_username(owner)
                    if c:
                        names.add(c)
                caption = itm.get("caption", "") or ""
                if caption:
                    for mention in re.findall(r'@([a-zA-Z0-9._]{1,30})', caption):
                        c = clean_username(mention)
                        if c:
                            names.add(c)
            return list(names), run.get("id", "")
        except Exception as e:
            print(f"❌ hashtag actor error: {e}")
            return [], ""

    async def _get_usernames_from_search(self, niche: str, limit: int = 200, mode: str = "recent") -> Tuple[List[str], str]:
        """Run search actor (fallback)"""
        try:
            run_input = {
                "search": f"#{niche}",
                "resultsLimit": limit,
                "searchType": "hashtag",
                "mode": mode,
                "proxyConfiguration": {"useApifyProxy": True}
            }
            run = await self._call_actor(self.SEARCH_SCRAPER_ID, run_input)
            ds_id = run.get("defaultDatasetId")
            items = await self._collect_dataset_items(ds_id) if ds_id else []
            names = set()
            for itm in items:
                owner = itm.get("ownerUsername")
                if owner:
                    c = clean_username(owner)
                    if c:
                        names.add(c)
                caption = itm.get("caption", "") or ""
                for mention in re.findall(r'@([a-zA-Z0-9._]{1,30})', caption):
                    c = clean_username(mention)
                    if c:
                        names.add(c)
            return list(names), run.get("id", "")
        except Exception as e:
            print(f"❌ search actor error: {e}")
            return [], ""

    async def _get_users_batch_info(self, usernames: List[str]) -> List[Dict]:
        """Call profile actor to get batch info for many usernames."""
        if not usernames:
            return []
        try:
            run_input = {"usernames": usernames, "resultsLimit": len(usernames)}
            run = await self._call_actor(self.PROFILE_SCRAPER_ID, run_input)
            ds_id = run.get("defaultDatasetId")
            items = await self._collect_dataset_items(ds_id) if ds_id else []
            users = []
            for itm in items:
                try:
                    u = self._process_basic_profile_data(itm)
                    if u:
                        users.append(u)
                except Exception:
                    continue
            return users
        except Exception as e:
            print(f"❌ profile batch error: {e}")
            return []

    async def _get_detailed_profile(self, username: str) -> Optional[Dict]:
        try:
            run_input = {"usernames": [username], "resultsLimit": 1, "addParentData": True}
            run = await self._call_actor(self.PROFILE_SCRAPER_ID, run_input)
            ds_id = run.get("defaultDatasetId")
            items = await self._collect_dataset_items(ds_id) if ds_id else []
            for itm in items:
                if itm.get("username") == username:
                    return self._process_detailed_profile_data(itm)
            return None
        except Exception as e:
            print(f"❌ detailed profile error: {e}")
            return None

    async def _get_user_posts(self, username: str, limit: int = 12) -> List[Dict]:
        try:
            run_input = {"usernames": [username], "resultsLimit": limit}
            run = await self._call_actor(self.POST_SCRAPER_ID, run_input)
            ds_id = run.get("defaultDatasetId")
            items = await self._collect_dataset_items(ds_id) if ds_id else []
            posts = [self._process_post_data(itm) for itm in items if itm]
            return [p for p in posts if p]
        except Exception as e:
            print(f"❌ post actor error: {e}")
            return []

    # -------------------- processing helpers --------------------
    def _process_basic_profile_data(self, raw_data: Dict) -> Optional[Dict]:
        try:
            if not raw_data.get('username'):
                return None
            return {
                'username': clean_username(raw_data.get('username', '')),
                'full_name': raw_data.get('fullName', ''),
                'follower_count': self._safe_parse_count(raw_data.get('followersCount', 0)),
                'following_count': self._safe_parse_count(raw_data.get('followingCount', 0)),
                'posts_count': int(raw_data.get('postsCount', 0)) if raw_data.get('postsCount') else 0,
                'is_verified': bool(raw_data.get('verified', False)),
                'is_private': bool(raw_data.get('private', False)),
                'is_business': bool(raw_data.get('businessAccount', False)),
                'profile_pic_url': raw_data.get('profilePicUrl', ''),
                'external_url': raw_data.get('externalUrl', '')
            }
        except Exception:
            return None

    def _process_detailed_profile_data(self, raw_data: Dict) -> Dict:
        try:
            bio = raw_data.get('biography', '') or ''
            return {
                'username': clean_username(raw_data.get('username', '')),
                'full_name': raw_data.get('fullName', ''),
                'bio': bio,
                'follower_count': self._safe_parse_count(raw_data.get('followersCount', 0)),
                'following_count': self._safe_parse_count(raw_data.get('followingCount', 0)),
                'posts_count': int(raw_data.get('postsCount', 0)) if raw_data.get('postsCount') else 0,
                'is_verified': bool(raw_data.get('verified', False)),
                'is_private': bool(raw_data.get('private', False)),
                'is_business': bool(raw_data.get('businessAccount', False)),
                'profile_pic_url': raw_data.get('profilePicUrl', ''),
                'external_url': raw_data.get('externalUrl', ''),
                'email': self._extract_email_from_bio(bio),
                'phone': self._extract_phone_from_bio(bio),
                'category': raw_data.get('category', ''),
                'address': raw_data.get('businessAddress', ''),
                'website': raw_data.get('website', '')
            }
        except Exception as e:
            return {'username': raw_data.get('username', ''), 'error': str(e)}

    def _process_post_data(self, raw_data: Dict) -> Optional[Dict]:
        try:
            caption = raw_data.get('caption', '') or ''
            hashtags = re.findall(r'#(\w+)', caption) if caption else []
            mentions = re.findall(r'@(\w+)', caption) if caption else []
            post_type = 'photo'
            if raw_data.get('videoUrl'):
                post_type = 'video'
            elif raw_data.get('images') and len(raw_data.get('images', [])) > 1:
                post_type = 'carousel'
            return {
                'post_id': raw_data.get('id', ''),
                'post_url': raw_data.get('url', ''),
                'caption': caption,
                'image_urls': raw_data.get('images') or ([raw_data.get('displayUrl')] if raw_data.get('displayUrl') else []),
                'video_url': raw_data.get('videoUrl', ''),
                'likes_count': int(raw_data.get('likesCount', 0)),
                'comments_count': int(raw_data.get('commentsCount', 0)),
                'post_type': post_type,
                'hashtags': hashtags,
                'mentions': mentions,
                'posted_at': raw_data.get('timestamp'),
                'location': raw_data.get('locationName', ''),
                'alt_text': raw_data.get('alt', '')
            }
        except Exception:
            return None

    def _safe_parse_count(self, count_value) -> int:
        try:
            if isinstance(count_value, int):
                return count_value
            if isinstance(count_value, str):
                return parse_follower_count(count_value)
            return int(count_value) if count_value else 0
        except Exception:
            return 0

    # email / phone extraction helpers (kept from your old code)
    def _extract_email_from_bio(self, bio: str) -> Optional[str]:
        if not bio:
            return None
        patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
        ]
        for p in patterns:
            found = re.findall(p, bio)
            if found:
                return re.sub(r'\s', '', found[0])
        return None

    def _extract_phone_from_bio(self, bio: str) -> Optional[str]:
        if not bio:
            return None
        patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?([0-9]{7,15})'
        ]
        for p in patterns:
            found = re.findall(p, bio)
            if found:
                return ''.join(found[0]) if isinstance(found[0], tuple) else found[0]
        return None