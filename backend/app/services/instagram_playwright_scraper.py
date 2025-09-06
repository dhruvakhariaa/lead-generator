from playwright.async_api import async_playwright, TimeoutError
from typing import List, Dict, Optional
import asyncio
import json
import random
import re
from datetime import datetime
import logging

class InstagramPlaywrightScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        """Initialize Playwright browser context"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            # Create context with realistic user agent and viewport
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            # Set extra headers to appear more legitimate
            await self.context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            return self
        except Exception as e:
            print(f"❌ Error initializing Playwright: {str(e)}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up Playwright resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")

    async def scrape_users(self, niche: str, min_followers: int, max_results: int = 100, target_count: int = 10, max_attempts: int = 5) -> List[Dict]:
        """
        Scrape Instagram users by niche, looping until at least target_count valid users are collected or max_attempts reached.
        Optimized with progressive scrolling on a single page, deduplication, jittered backoff, and error checks.
        """
        try:
            print(f"🔍 Playwright: Starting user scraping for #{niche} with target {target_count} valid users")
            
            filtered_users = []  # Accumulator for valid users
            processed_usernames = set()  # Deduplication across loops
            attempt = 0
            scroll_increment = 5  # Base scrolls per attempt (increases progressively)
            
            # Single page setup
            page = await self.context.new_page()
            hashtag_url = f'https://www.instagram.com/explore/tags/{niche}/'
            await page.goto(hashtag_url, wait_until='networkidle', timeout=30000)
            
            while len(filtered_users) < target_count and attempt < max_attempts:
                attempt += 1
                print(f"🔄 Attempt {attempt}/{max_attempts}")
                
                try:
                    # Error check: If page indicates block or no content, abort
                    if await page.locator('text=Sorry, this page isn\'t available').count() > 0 or await page.locator('text=Try again later').count() > 0:
                        print(f"❌ Page error in attempt {attempt} - aborting")
                        break
                    
                    # Progressive scroll on the same page
                    await self._scroll_page(page, scroll_increment)
                    
                    # Extract usernames
                    all_usernames = await self._extract_usernames_from_page(page)
                    
                    # Error check and retry once if no usernames
                    if not all_usernames:
                        print(f"⚠️ No usernames found in attempt {attempt} - retrying once")
                        await asyncio.sleep(random.uniform(5, 10))  # Short delay before retry
                        await self._scroll_page(page, scroll_increment)
                        all_usernames = await self._extract_usernames_from_page(page)
                        if not all_usernames:
                            print(f"⚠️ Retry failed - continuing to next attempt")
                            continue
                    
                    new_usernames = [u for u in all_usernames if u not in processed_usernames]
                    processed_usernames.update(new_usernames)
                    
                    if not new_usernames:
                        print(f"⚠️ No new usernames found in attempt {attempt}")
                        continue
                    
                    # Fetch profile info and filter (with rate limiting)
                    for username in new_usernames:
                        user_info = await self._get_user_basic_info(username)
                        if user_info and user_info.get('follower_count', 0) >= min_followers:
                            user_info['niche'] = niche
                            user_info['scraped_at'] = datetime.utcnow().isoformat()
                            filtered_users.append(user_info)
                            print(f"✅ Added @{username} ({user_info['follower_count']:,} followers)")
                        await asyncio.sleep(random.uniform(2, 4))  # Delay between profiles
                    
                    # Print statement after running the loop
                    print(f"🔄 Loop {attempt} completed: Currently have {len(filtered_users)} valid users")
                    
                    # Apply jittered backoff delay (exponential base + random 1-3s)
                    if len(filtered_users) < target_count and attempt < max_attempts:
                        delay = 10 * (attempt ** 1.5) + random.uniform(1, 3)
                        print(f"⏳ Waiting {delay:.1f}s before next attempt")
                        await asyncio.sleep(delay)
                    
                    # Increase scroll_increment for more content next time
                    scroll_increment += 3  # Progressive increase
                
                except TimeoutError as e:
                    print(f"❌ Timeout error in attempt {attempt}: {str(e)} - skipping to next")
                    continue
                except Exception as e:
                    print(f"❌ Unexpected error in attempt {attempt}: {str(e)} - retrying once")
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
            
            await page.close()
            
            # Trim to max_results if exceeded
            filtered_users = filtered_users[:max_results]
            
            if len(filtered_users) < target_count:
                print(f"⚠️ Reached max attempts; only {len(filtered_users)} valid users found. The niche you have chosen is a low-activity niche so try some other niches or hashtags that would target what you want to have a lead for.")
            
            print(f"✅ Playwright collected {len(filtered_users)} valid users")
            return filtered_users
        
        except Exception as e:
            print(f"❌ Error in scrape_users: {str(e)}")
            return []

    async def scrape_profile(self, username: str) -> Optional[Dict]:
        """
        Scrape detailed profile information for a specific user
        Args:
            username: Instagram username (without @)
        Returns:
            Dictionary with detailed profile information
        """
        try:
            print(f"👤 Playwright: Scraping detailed profile for @{username}")
            page = await self.context.new_page()
            # Navigate to profile page
            profile_url = f'https://www.instagram.com/{username}/'
            await page.goto(profile_url, wait_until='networkidle', timeout=30000)
            # Check if profile exists
            if await page.locator('text=Sorry, this page isn\'t available').count() > 0:
                print(f"❌ Profile @{username} not found")
                await page.close()
                return None
            # Wait for profile content to load
            try:
                await page.wait_for_selector('header', timeout=10000)
            except:
                print(f"⚠️ Profile header not loaded for @{username}")
                await page.close()
                return None
            # Extract profile information
            profile_data = await self._extract_profile_data(page, username)
            # Extract recent posts if profile is public
            if not profile_data.get('is_private', True):
                posts = await self._extract_recent_posts(page, username)
                profile_data['recent_posts'] = posts
                profile_data['engagement_rate'] = self._calculate_engagement_rate(
                    posts, profile_data.get('follower_count', 0)
                )
                profile_data['top_hashtags'] = self._extract_top_hashtags(posts)
            else:
                profile_data['recent_posts'] = []
                profile_data['engagement_rate'] = 0.0
                profile_data['top_hashtags'] = []
                print(f"⚠️ Profile @{username} is private, limited data available")
            profile_data['scraped_at'] = datetime.utcnow().isoformat()
            await page.close()
            print(f"✅ Successfully scraped detailed profile for @{username}")
            return profile_data
        except Exception as e:
            print(f"❌ Error scraping profile @{username}: {str(e)}")
            return None

    async def _scroll_page(self, page, scroll_count: int = 3):
        """Scroll page to load more content"""
        for i in range(scroll_count):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(random.uniform(1.5, 3))
            print(f"📜 Scrolling... ({i+1}/{scroll_count})")

    async def _extract_usernames_from_page(self, page) -> List[str]:
        """Extract unique usernames from posts on the page"""
        try:
            usernames = await page.evaluate('''
                () => {
                    const usernames = new Set();
                    // Look for username links in posts
                    const usernameLinks = document.querySelectorAll('a[href^="/"][href$="/"]');
                    usernameLinks.forEach(link => {
                        const href = link.get_attribute('href');
                        if (href && href.length > 2) {
                            const username = href.slice(1, -1);
                            // Filter out non-username paths
                            if (username &&
                                !username.includes('/') &&
                                !username.includes('p') &&
                                !username.includes('reel') &&
                                !username.includes('explore') &&
                                username.length <= 30 &&
                                /^[a-zA-Z0-9._]+$/.test(username)) {
                                usernames.add(username);
                            }
                        }
                    });
                    return Array.from(usernames);
                }
            ''')
            return usernames[:50]  # Limit to first 50 unique usernames
        except Exception as e:
            print(f"⚠️ Error extracting usernames: {str(e)}")
            return []

    async def _get_user_basic_info(self, username: str) -> Optional[Dict]:
        """Get basic user information (follower count, verification, etc.)"""
        try:
            page = await self.context.new_page()
            profile_url = f'https://www.instagram.com/{username}/'
            await page.goto(profile_url, wait_until='networkidle', timeout=20000)
            # Check if profile exists
            if await page.locator('text=Sorry, this page isn\'t available').count() > 0:
                await page.close()
                return None
            # Wait for header to load
            await page.wait_for_selector('header', timeout=10000)
            # Extract basic profile data
            profile_data = await page.evaluate('''
                () => {
                    const getTextContent = (selector) => {
                        const element = document.querySelector(selector);
                        return element ? element.textContent.trim() : '';
                    };
                    const getMetaContent = (property) => {
                        const meta = document.querySelector(`meta[property="${property}"]`);
                        return meta ? meta.getAttribute('content') : '';
                    };
                    // Try multiple selectors for follower count
                    const followerSelectors = [
                        'a[href*="/followers/"] span[title]',
                        'a[href*="/followers/"] span',
                        'header section ul li:nth-child(2) span',
                        'header ul li:nth-child(2) span'
                    ];
                    let followerCount = '0';
                    for (const selector of followerSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            followerCount = element.getAttribute('title') || element.textContent.trim();
                            break;
                        }
                    }
                    // Try multiple selectors for following count
                    const followingSelectors = [
                        'a[href*="/following/"] span[title]',
                        'a[href*="/following/"] span',
                        'header section ul li:nth-child(3) span',
                        'header ul li:nth-child(3) span'
                    ];
                    let followingCount = '0';
                    for (const selector of followingSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            followingCount = element.getAttribute('title') || element.textContent.trim();
                            break;
                        }
                    }
                    return {
                        username: window.location.pathname.slice(1, -1) || window.location.pathname.slice(1),
                        full_name: getTextContent('header h2') || getMetaContent('og:title'),
                        follower_count: followerCount,
                        following_count: followingCount,
                        profile_pic_url: getMetaContent('og:image'),
                        is_verified: !!document.querySelector('svg[aria-label="Verified"]'),
                        is_private: !!document.querySelector('svg[aria-label="Private account"]') ||
                                   !!document.querySelector('text="This Account is Private"')
                    };
                }
            ''')
            await page.close()
            # Process and clean the data
            return {
                'username': self._clean_username(profile_data.get('username', '')),
                'full_name': profile_data.get('full_name', ''),
                'follower_count': self._parse_follower_count(profile_data.get('follower_count', '0')),
                'following_count': self._parse_follower_count(profile_data.get('following_count', '0')),
                'profile_pic_url': profile_data.get('profile_pic_url', ''),
                'is_verified': bool(profile_data.get('is_verified', False)),
                'is_private': bool(profile_data.get('is_private', False))
            }
        except Exception as e:
            print(f"⚠️ Error getting basic info for @{username}: {str(e)}")
            return None

    async def _extract_profile_data(self, page, username: str) -> Dict:
        """Extract detailed profile data from profile page"""
        try:
            profile_data = await page.evaluate('''
                () => {
                    const getTextContent = (selector) => {
                        const element = document.querySelector(selector);
                        return element ? element.textContent.trim() : '';
                    };
                    const getMetaContent = (property) => {
                        const meta = document.querySelector(`meta[property="${property}"]`);
                        return meta ? meta.getAttribute('content') : '';
                    };
                    // Extract bio
                    const bioSelectors = [
                        'header div[data-testid="user-bio"]',
                        'header section div span',
                        'header div h1 + div',
                        'header span'
                    ];
                    let bio = '';
                    for (const selector of bioSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim()) {
                            bio = element.textContent.trim();
                            break;
                        }
                    }
                    // Extract counts
                    const followerElement = document.querySelector('a[href*="/followers/"] span[title]') ||
                                            document.querySelector('a[href*="/followers/"] span');
                    const followingElement = document.querySelector('a[href*="/following/"] span[title]') ||
                                             document.querySelector('a[href*="/following/"] span');
                    const postsElement = document.querySelector('header ul li:first-child span') ||
                                         document.querySelector('header section ul li:first-child span');
                    // Extract external URL
                    const externalLink = document.querySelector('header a[href*="http"]:not([href*="instagram.com"])');
                    return {
                        username: window.location.pathname.slice(1, -1) || window.location.pathname.slice(1),
                        full_name: getTextContent('header h2') || getMetaContent('og:title'),
                        bio: bio,
                        follower_count: followerElement ? (followerElement.getAttribute('title') || followerElement.textContent.trim()) : '0',
                        following_count: followingElement ? (followingElement.getAttribute('title') || followingElement.textContent.trim()) : '0',
                        posts_count: postsElement ? postsElement.textContent.trim() : '0',
                        profile_pic_url: getMetaContent('og:image'),
                        external_url: externalLink ? externalLink.getAttribute('href') : '',
                        is_verified: !!document.querySelector('svg[aria-label="Verified"]'),
                        is_private: !!document.querySelector('svg[aria-label="Private account"]') ||
                                   !!document.querySelector('text="This Account is Private"'),
                        is_business: !!document.querySelector('text="Contact"') ||
                                     !!document.querySelector('button:contains("Contact")')
                    };
                }
            ''')
            # Process the extracted data
            bio = profile_data.get('bio', '')
            return {
                'username': self._clean_username(profile_data.get('username', '')),
                'full_name': profile_data.get('full_name', ''),
                'bio': bio,
                'follower_count': self._parse_follower_count(profile_data.get('follower_count', '0')),
                'following_count': self._parse_follower_count(profile_data.get('following_count', '0')),
                'posts_count': self._parse_follower_count(profile_data.get('posts_count', '0')),
                'profile_pic_url': profile_data.get('profile_pic_url', ''),
                'external_url': profile_data.get('external_url', ''),
                'email': self._extract_email_from_bio(bio),
                'is_verified': bool(profile_data.get('is_verified', False)),
                'is_private': bool(profile_data.get('is_private', False)),
                'is_business': bool(profile_data.get('is_business', False))
            }
        except Exception as e:
            print(f"⚠️ Error extracting profile data: {str(e)}")
            return {'username': username, 'error': str(e)}

    async def _extract_recent_posts(self, page, username: str, limit: int = 12) -> List[Dict]:
        """Extract recent posts from profile page"""
        try:
            # Scroll a bit to load posts
            await page.evaluate('window.scrollTo(0, window.innerHeight)')
            await asyncio.sleep(2)
            posts_data = await page.evaluate(f'''
                (limit) => {{
                    const posts = document.querySelectorAll('article a[href*="/p/"]');
                    const postData = [];
                    for (let i = 0; i < Math.min(posts.length, limit); i++) {{
                        const post = posts[i];
                        const img = post.querySelector('img');
                        const href = post.getAttribute('href');
                        if (img && href) {{
                            // Extract post ID from URL
                            const postIdMatch = href.match(/\/p\/([^\/]+)/);
                            const postId = postIdMatch ? postIdMatch[1] : '';
                            // Try to get caption from alt text
                            const caption = img.getAttribute('alt') || '';
                            postData.push({{
                                post_id: postId,
                                post_url: 'https://www.instagram.com' + href,
                                caption: caption,
                                image_url: img.getAttribute('src') || '',
                                likes_count: 0, // Would need to click on post to get actual numbers
                                comments_count: 0,
                                hashtags: [],
                                posted_at: null
                            }});
                        }}
                    }}
                    return postData;
                }}
            ''', limit)
            # Process posts to extract hashtags from captions
            for post in posts_data:
                if post.get('caption'):
                    post['hashtags'] = re.findall(r'#(\w+)', post['caption'])
            return posts_data
        except Exception as e:
            print(f"⚠️ Error extracting posts: {str(e)}")
            return []

    def _clean_username(self, username: str) -> str:
        """Clean and validate Instagram username"""
        if not username:
            return ""
        # Remove @ symbol and whitespace
        username = username.strip().lstrip('@')
        # Instagram username validation
        if re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return username
        return ""

    def _parse_follower_count(self, follower_text: str) -> int:
        """Parse follower count from text (handles K, M, B suffixes)"""
        if not follower_text:
            return 0
        # Remove commas and convert to lowercase
        text = follower_text.replace(',', '').lower()
        # Extract number
        match = re.search(r'(\d+\.?\d*)', text)
        if not match:
            return 0
        num = float(match.group(1))
        # Handle suffixes
        if 'k' in text:
            return int(num * 1000)
        elif 'm' in text:
            return int(num * 1000000)
        elif 'b' in text:
            return int(num * 1000000000)
        return int(num)

    def _extract_email_from_bio(self, bio: str) -> Optional[str]:
        """Extract email address from bio text"""
        if not bio:
            return None
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, bio)
        return emails[0] if emails else None

    def _calculate_engagement_rate(self, posts: List[Dict], follower_count: int) -> float:
        """Calculate engagement rate from posts"""
        if not posts or follower_count == 0:
            return 0.0
        total_engagement = sum(
            post.get('likes_count', 0) + post.get('comments_count', 0)
            for post in posts
        )
        avg_engagement = total_engagement / len(posts) if posts else 0
        engagement_rate = (avg_engagement / follower_count) * 100 if follower_count > 0 else 0
        return round(engagement_rate, 2)

    def _extract_top_hashtags(self, posts: List[Dict]) -> List[str]:
        """Extract most frequently used hashtags from posts"""
        hashtag_count = {}
        for post in posts:
            for hashtag in post.get('hashtags', []):
                hashtag = hashtag.lower()
                hashtag_count[hashtag] = hashtag_count.get(hashtag, 0) + 1
        # Return top 10 most used hashtags
        return sorted(hashtag_count.keys(), key=hashtag_count.get, reverse=True)[:10]

# Global instance
instagram_scraper = InstagramPlaywrightScraper()