# app/services/playwright_job_scraper.py

from playwright.async_api import async_playwright, TimeoutError
from app.services.proxy_manager import proxy_manager
from app.services.session_manager import session_manager
from typing import List, Dict, Optional
import asyncio
import random
import re
from datetime import datetime, timedelta
import logging
from urllib.parse import quote_plus, urljoin

class PlaywrightJobScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.current_proxy = None

    async def __aenter__(self):
        """Initialize Playwright with proxy and session management"""
        try:
            self.playwright = await async_playwright().start()
            
            # Get proxy
            self.current_proxy = proxy_manager.get_proxy()
            
            # Browser launch args with stealth
            launch_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--hide-scrollbars',
                '--metrics-recording-only',
                '--mute-audio',
                '--no-default-browser-check',
                '--safebrowsing-disable-auto-update',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
            
            # Add proxy if available
            if self.current_proxy:
                proxy_parts = self.current_proxy.split(':')
                if len(proxy_parts) == 2:
                    proxy_config = {
                        "server": f"http://{self.current_proxy}"
                    }
                else:
                    proxy_config = None
                    print(f"⚠️ Invalid proxy format: {self.current_proxy}")
            else:
                proxy_config = None
                print("⚠️ No proxy available")

            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Run headless for job scraping
                args=launch_args,
                proxy=proxy_config
            )

            # Create context with realistic fingerprint
            context_options = {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': {'width': 1920, 'height': 1080},
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': [],
                'java_script_enabled': True,
                'ignore_https_errors': True
            }

            self.context = await self.browser.new_context(**context_options)

            # Load saved cookies if available
            cookies = await session_manager.load_cookies()
            if cookies:
                await self.context.add_cookies(cookies)

            # Set extra headers for legitimacy
            await self.context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })

            print(f"🤖 JobScraper initialized with proxy: {self.current_proxy or 'None'}")
            return self

        except Exception as e:
            print(f"❌ Error initializing JobScraper: {str(e)}")
            if self.current_proxy:
                proxy_manager.report_failure(self.current_proxy)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources"""
        try:
            # Save cookies before closing
            if self.context:
                cookies = await self.context.cookies()
                if cookies:
                    await session_manager.save_cookies(cookies)
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()

        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")

    async def scrape_jobs(
        self,
        keywords: str,
        location: str = "remote",
        job_type: str = "contract",
        max_results: int = 10,
        platforms: List[str] = ["indeed", "glassdoor", "google"]
    ) -> List[Dict]:
        """
        Main job scraping orchestrator
        """
        all_jobs = []
        search_keywords = [kw.strip().lower() for kw in keywords.split() if kw.strip()]
        
        print(f"🔍 Starting job search: '{keywords}' in '{location}' ({job_type})")
        
        for platform in platforms:
            if len(all_jobs) >= max_results:
                break
                
            try:
                remaining_count = max_results - len(all_jobs)
                print(f"📋 Searching {platform.title()} for {remaining_count} jobs...")
                
                if platform == "indeed":
                    jobs = await self._scrape_indeed(keywords, location, job_type, remaining_count)
                elif platform == "glassdoor":
                    jobs = await self._scrape_glassdoor(keywords, location, job_type, remaining_count)
                elif platform == "google":
                    jobs = await self._scrape_google_jobs(keywords, location, job_type, remaining_count)
                else:
                    print(f"⚠️ Platform '{platform}' not supported")
                    continue
                
                # Add search keywords to each job
                for job in jobs:
                    job['search_keywords'] = search_keywords
                    job['platform'] = platform
                    job['scraped_at'] = datetime.utcnow().isoformat()
                
                all_jobs.extend(jobs)
                print(f"✅ Found {len(jobs)} jobs from {platform}")
                
                # Conservative delay between platforms
                if len(all_jobs) < max_results and platform != platforms[-1]:
                    delay = random.uniform(30, 45)  # 30-45 second delay
                    print(f"⏳ Waiting {delay:.1f}s before next platform...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                print(f"❌ Error scraping {platform}: {str(e)}")
                if self.current_proxy:
                    proxy_manager.report_failure(self.current_proxy)
                continue

        # Deduplicate jobs by title + company
        seen_jobs = set()
        unique_jobs = []
        
        for job in all_jobs:
            job_key = (job.get('title', '').lower(), job.get('company_name', '').lower())
            if job_key not in seen_jobs and job_key != ('', ''):
                seen_jobs.add(job_key)
                unique_jobs.append(job)
        
        # Limit to max_results
        unique_jobs = unique_jobs[:max_results]
        
        print(f"🎯 Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs

    async def _scrape_indeed(self, keywords: str, location: str, job_type: str, limit: int) -> List[Dict]:
        """Scrape Indeed jobs"""
        jobs = []
        try:
            page = await self.context.new_page()
            
            # Build Indeed search URL
            search_params = {
                'q': keywords,
                'l': location if location.lower() != 'remote' else '',
                'jt': self._map_job_type_indeed(job_type),
                'radius': '25',
                'fromage': '14'  # Last 14 days
            }
            
            # Add remote filter if needed
            if location.lower() in ['remote', 'work from home']:
                search_params['remotejob'] = '032b3046-06a3-4876-8dfd-474eb5e7ed11'
            
            # Build URL
            base_url = 'https://www.indeed.com/jobs?'
            url_params = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in search_params.items() if v])
            search_url = base_url + url_params
            
            print(f"🔗 Indeed URL: {search_url}")
            
            # Navigate with stealth
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(3, 6))
            
            # Extract job listings
            jobs_data = await page.evaluate('''
            () => {
                const jobs = [];
                const jobCards = document.querySelectorAll('[data-jk], .job_seen_beacon');
                
                jobCards.forEach((card, index) => {
                    if (index >= 10) return; // Limit per page
                    
                    try {
                        // Title and link
                        const titleEl = card.querySelector('h2 a span[title], .jobTitle a span[title]');
                        const titleLinkEl = card.querySelector('h2 a, .jobTitle a');
                        
                        // Company
                        const companyEl = card.querySelector('[data-testid="company-name"], .companyName');
                        
                        // Location
                        const locationEl = card.querySelector('[data-testid="job-location"], .companyLocation');
                        
                        // Description snippet
                        const descEl = card.querySelector('.job-snippet, [data-testid="job-snippet"]');
                        
                        // Salary
                        const salaryEl = card.querySelector('.salary-snippet, [data-testid="attribute_snippet_testid"]');
                        
                        // Date
                        const dateEl = card.querySelector('.date, [data-testid="myJobsStateDate"]');
                        
                        if (titleEl && companyEl) {
                            const title = titleEl.getAttribute('title') || titleEl.textContent.trim();
                            const company = companyEl.textContent.trim();
                            const location = locationEl ? locationEl.textContent.trim() : '';
                            const description = descEl ? descEl.textContent.trim() : '';
                            const salary = salaryEl ? salaryEl.textContent.trim() : '';
                            const postedDate = dateEl ? dateEl.textContent.trim() : '';
                            
                            // Build job URL
                            let jobUrl = '';
                            if (titleLinkEl) {
                                const href = titleLinkEl.getAttribute('href');
                                if (href) {
                                    jobUrl = href.startsWith('http') ? href : 'https://www.indeed.com' + href;
                                }
                            }
                            
                            jobs.push({
                                title,
                                company,
                                location,
                                description,
                                salary,
                                postedDate,
                                jobUrl
                            });
                        }
                    } catch (e) {
                        console.log('Error processing job card:', e);
                    }
                });
                
                return jobs;
            }
            ''')
            
            # Process Indeed jobs
            for job_data in jobs_data[:limit]:
                if not job_data.get('title') or not job_data.get('company'):
                    continue
                    
                processed_job = await self._process_indeed_job(job_data)
                if processed_job:
                    jobs.append(processed_job)
            
            await page.close()
            
        except Exception as e:
            print(f"❌ Indeed scraping error: {e}")
            
        return jobs

    async def _scrape_glassdoor(self, keywords: str, location: str, job_type: str, limit: int) -> List[Dict]:
        """Scrape Glassdoor jobs"""
        jobs = []
        try:
            page = await self.context.new_page()
            
            # Build Glassdoor search URL
            location_param = location if location.lower() != 'remote' else 'remote'
            search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={quote_plus(keywords)}&locT=C&locId=&jobType={self._map_job_type_glassdoor(job_type)}&sc.occupationParam={quote_plus(keywords)}"
            
            if location.lower() in ['remote', 'work from home']:
                search_url += "&remoteWorkType=1"
            
            print(f"🔗 Glassdoor URL: {search_url}")
            
            # Navigate
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(4, 7))
            
            # Handle potential popups/overlays
            try:
                await page.click('button[data-test="close-modal"], .CloseButton', timeout=3000)
            except:
                pass
            
            # Extract jobs
            jobs_data = await page.evaluate('''
            () => {
                const jobs = [];
                const jobCards = document.querySelectorAll('[data-test="job-listing"], .react-job-listing');
                
                jobCards.forEach((card, index) => {
                    if (index >= 8) return;
                    
                    try {
                        const titleEl = card.querySelector('[data-test="job-title"], .jobTitle');
                        const companyEl = card.querySelector('[data-test="employer-name"], .employerName');
                        const locationEl = card.querySelector('[data-test="job-location"], .location');
                        const salaryEl = card.querySelector('.salaryEstimate, [data-test="salary-estimate"]');
                        const ratingEl = card.querySelector('.companyRating, [data-test="rating"]');
                        
                        if (titleEl && companyEl) {
                            const title = titleEl.textContent.trim();
                            const company = companyEl.textContent.trim();
                            const location = locationEl ? locationEl.textContent.trim() : '';
                            const salary = salaryEl ? salaryEl.textContent.trim() : '';
                            const rating = ratingEl ? ratingEl.textContent.trim() : '';
                            
                            // Get job URL
                            let jobUrl = '';
                            const linkEl = card.querySelector('a[data-test="job-title"], .jobTitle a');
                            if (linkEl) {
                                const href = linkEl.getAttribute('href');
                                if (href) {
                                    jobUrl = href.startsWith('http') ? href : 'https://www.glassdoor.com' + href;
                                }
                            }
                            
                            jobs.push({
                                title,
                                company,
                                location,
                                salary,
                                rating,
                                jobUrl
                            });
                        }
                    } catch (e) {
                        console.log('Error processing Glassdoor job:', e);
                    }
                });
                
                return jobs;
            }
            ''')
            
            # Process Glassdoor jobs
            for job_data in jobs_data[:limit]:
                if not job_data.get('title') or not job_data.get('company'):
                    continue
                    
                processed_job = await self._process_glassdoor_job(job_data)
                if processed_job:
                    jobs.append(processed_job)
            
            await page.close()
            
        except Exception as e:
            print(f"❌ Glassdoor scraping error: {e}")
            
        return jobs

    async def _scrape_google_jobs(self, keywords: str, location: str, job_type: str, limit: int) -> List[Dict]:
        """Scrape Google Jobs"""
        jobs = []
        try:
            page = await self.context.new_page()
            
            # Build Google Jobs search URL
            location_param = location if location.lower() != 'remote' else 'anywhere'
            search_query = f"{keywords} {job_type} jobs"
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&ibp=htl;jobs&sa=X&ved=&sxsrf="
            
            if location.lower() in ['remote', 'work from home']:
                search_query += " remote"
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&ibp=htl;jobs"
            
            print(f"🔗 Google Jobs URL: {search_url}")
            
            # Navigate
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(3, 6))
            
            # Accept cookies if prompted
            try:
                await page.click('button:has-text("Accept all"), button:has-text("I agree")', timeout=3000)
                await asyncio.sleep(2)
            except:
                pass
            
            # Extract jobs from Google Jobs widget
            jobs_data = await page.evaluate('''
            () => {
                const jobs = [];
                
                // Try multiple selectors for Google Jobs
                const jobSelectors = [
                    '.tM9F2e',  // Main job card selector
                    '.PwjeAc',  // Alternative selector
                    '[data-ved][role="listitem"]'  // Broader selector
                ];
                
                let jobCards = [];
                for (const selector of jobSelectors) {
                    jobCards = document.querySelectorAll(selector);
                    if (jobCards.length > 0) break;
                }
                
                jobCards.forEach((card, index) => {
                    if (index >= 6) return; // Limit for Google
                    
                    try {
                        // Try different title selectors
                        let titleEl = card.querySelector('.BjJfJf, .vNEEBe, h3');
                        let companyEl = card.querySelector('.vNEEBe .nJlQNd, .uMdZh, .nJlQNd');
                        let locationEl = card.querySelector('.Qk80Jf, .sMzDkb');
                        
                        if (titleEl && companyEl) {
                            const title = titleEl.textContent.trim();
                            const company = companyEl.textContent.trim();
                            const location = locationEl ? locationEl.textContent.trim() : '';
                            
                            // Get job URL if available
                            let jobUrl = '';
                            const linkEl = card.querySelector('a');
                            if (linkEl) {
                                jobUrl = linkEl.getAttribute('href') || '';
                                if (jobUrl.startsWith('/url?q=')) {
                                    // Extract actual URL from Google redirect
                                    const urlMatch = jobUrl.match(/url\?q=([^&]+)/);
                                    if (urlMatch) {
                                        jobUrl = decodeURIComponent(urlMatch[1]);
                                    }
                                }
                            }
                            
                            jobs.push({
                                title,
                                company,
                                location,
                                jobUrl
                            });
                        }
                    } catch (e) {
                        console.log('Error processing Google job:', e);
                    }
                });
                
                return jobs;
            }
            ''')
            
            # Process Google jobs
            for job_data in jobs_data[:limit]:
                if not job_data.get('title') or not job_data.get('company'):
                    continue
                    
                processed_job = await self._process_google_job(job_data)
                if processed_job:
                    jobs.append(processed_job)
            
            await page.close()
            
        except Exception as e:
            print(f"❌ Google Jobs scraping error: {e}")
            
        return jobs

    async def _process_indeed_job(self, job_data: Dict) -> Optional[Dict]:
        """Process Indeed job data"""
        try:
            # Parse salary
            salary_min, salary_max = self._parse_salary(job_data.get('salary', ''))
            
            # Determine job characteristics
            is_remote = self._is_remote_job(job_data.get('location', ''), job_data.get('description', ''))
            is_contract = self._is_contract_job(job_data.get('title', ''), job_data.get('description', ''))
            
            # Calculate trust score
            trust_score = self._calculate_trust_score(
                company=job_data.get('company', ''),
                description=job_data.get('description', ''),
                salary_range=job_data.get('salary', ''),
                has_benefits=bool(salary_min),  # If salary is listed, more legitimate
                platform='indeed'
            )
            
            # Extract skills and requirements
            skills = self._extract_skills(job_data.get('description', ''))
            experience_level = self._determine_experience_level(job_data.get('title', ''), job_data.get('description', ''))
            
            return {
                'job_id': f"indeed_{hash(job_data.get('title', '') + job_data.get('company', ''))}",
                'title': job_data.get('title', ''),
                'company_name': job_data.get('company', ''),
                'location': job_data.get('location', ''),
                'is_remote_friendly': is_remote,
                'job_type': 'contract' if is_contract else 'full-time',
                'is_contract_work': is_contract,
                'salary_range': job_data.get('salary', ''),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'description': job_data.get('description', ''),
                'requirements': [],
                'skills': skills,
                'posted_date': self._parse_date(job_data.get('postedDate', '')),
                'application_url': job_data.get('jobUrl', ''),
                'platform': 'indeed',
                'company_website': '',
                'contact_email': None,
                'trust_score': trust_score,
                'experience_level': experience_level,
                'benefits': []
            }
            
        except Exception as e:
            print(f"❌ Error processing Indeed job: {e}")
            return None

    async def _process_glassdoor_job(self, job_data: Dict) -> Optional[Dict]:
        """Process Glassdoor job data"""
        try:
            # Parse salary
            salary_min, salary_max = self._parse_salary(job_data.get('salary', ''))
            
            # Glassdoor characteristics
            is_remote = self._is_remote_job(job_data.get('location', ''), '')
            is_contract = self._is_contract_job(job_data.get('title', ''), '')
            
            # Higher trust score for Glassdoor (company reviews available)
            trust_score = self._calculate_trust_score(
                company=job_data.get('company', ''),
                description='',
                salary_range=job_data.get('salary', ''),
                has_benefits=bool(salary_min),
                platform='glassdoor',
                company_rating=job_data.get('rating', '')
            )
            
            skills = self._extract_skills(job_data.get('title', ''))
            experience_level = self._determine_experience_level(job_data.get('title', ''), '')
            
            return {
                'job_id': f"glassdoor_{hash(job_data.get('title', '') + job_data.get('company', ''))}",
                'title': job_data.get('title', ''),
                'company_name': job_data.get('company', ''),
                'location': job_data.get('location', ''),
                'is_remote_friendly': is_remote,
                'job_type': 'contract' if is_contract else 'full-time',
                'is_contract_work': is_contract,
                'salary_range': job_data.get('salary', ''),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'description': f"Company Rating: {job_data.get('rating', 'N/A')}",
                'requirements': [],
                'skills': skills,
                'posted_date': None,
                'application_url': job_data.get('jobUrl', ''),
                'platform': 'glassdoor',
                'company_website': '',
                'contact_email': None,
                'trust_score': trust_score,
                'experience_level': experience_level,
                'benefits': []
            }
            
        except Exception as e:
            print(f"❌ Error processing Glassdoor job: {e}")
            return None

    async def _process_google_job(self, job_data: Dict) -> Optional[Dict]:
        """Process Google job data"""
        try:
            is_remote = self._is_remote_job(job_data.get('location', ''), '')
            is_contract = self._is_contract_job(job_data.get('title', ''), '')
            
            # Medium trust score for Google (aggregated from multiple sources)
            trust_score = self._calculate_trust_score(
                company=job_data.get('company', ''),
                description='',
                salary_range='',
                has_benefits=False,
                platform='google'
            )
            
            skills = self._extract_skills(job_data.get('title', ''))
            experience_level = self._determine_experience_level(job_data.get('title', ''), '')
            
            return {
                'job_id': f"google_{hash(job_data.get('title', '') + job_data.get('company', ''))}",
                'title': job_data.get('title', ''),
                'company_name': job_data.get('company', ''),
                'location': job_data.get('location', ''),
                'is_remote_friendly': is_remote,
                'job_type': 'contract' if is_contract else 'full-time',
                'is_contract_work': is_contract,
                'salary_range': '',
                'salary_min': None,
                'salary_max': None,
                'description': 'Job found via Google Jobs aggregation',
                'requirements': [],
                'skills': skills,
                'posted_date': None,
                'application_url': job_data.get('jobUrl', ''),
                'platform': 'google',
                'company_website': '',
                'contact_email': None,
                'trust_score': trust_score,
                'experience_level': experience_level,
                'benefits': []
            }
            
        except Exception as e:
            print(f"❌ Error processing Google job: {e}")
            return None

    def _map_job_type_indeed(self, job_type: str) -> str:
        """Map job type to Indeed parameter"""
        mapping = {
            'full-time': 'fulltime',
            'part-time': 'parttime',
            'contract': 'contract',
            'freelance': 'contract',
            'temporary': 'temporary',
            'internship': 'internship'
        }
        return mapping.get(job_type.lower(), '')

    def _map_job_type_glassdoor(self, job_type: str) -> str:
        """Map job type to Glassdoor parameter"""
        mapping = {
            'full-time': 'fulltime',
            'part-time': 'parttime', 
            'contract': 'contract',
            'freelance': 'contract',
            'internship': 'internship'
        }
        return mapping.get(job_type.lower(), '')

    def _parse_salary(self, salary_text: str) -> tuple:
        """Parse salary range from text"""
        if not salary_text:
            return None, None
            
        # Remove common salary text
        salary_clean = re.sub(r'(a year|annually|per year|/yr|yearly)', '', salary_text, flags=re.IGNORECASE)
        salary_clean = re.sub(r'(an hour|hourly|per hour|/hr)', '', salary_clean, flags=re.IGNORECASE)
        
        # Find salary numbers
        numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', salary_clean)
        
        if len(numbers) >= 2:
            try:
                min_sal = int(numbers[0].replace(',', ''))
                max_sal = int(numbers[1].replace(',', ''))
                return min_sal, max_sal
            except:
                pass
        elif len(numbers) == 1:
            try:
                sal = int(numbers[0].replace(',', ''))
                return sal, sal
            except:
                pass
                
        return None, None

    def _is_remote_job(self, location: str, description: str) -> bool:
        """Determine if job is remote-friendly"""
        remote_indicators = [
            'remote', 'work from home', 'wfh', 'telecommute', 
            'distributed', 'anywhere', 'virtual', 'home office'
        ]
        
        text = f"{location} {description}".lower()
        return any(indicator in text for indicator in remote_indicators)

    def _is_contract_job(self, title: str, description: str) -> bool:
        """Determine if job is contract/freelance work"""
        contract_indicators = [
            'contract', 'contractor', 'freelance', 'freelancer',
            'consultant', 'temporary', 'temp', 'project', 'gig'
        ]
        
        text = f"{title} {description}".lower()
        return any(indicator in text for indicator in contract_indicators)

    def _calculate_trust_score(self, company: str, description: str, salary_range: str, 
                             has_benefits: bool, platform: str, company_rating: str = '') -> int:
        """Calculate trust score 0-100"""
        score = 30  # Base score
        
        # Platform reliability
        platform_scores = {'glassdoor': 25, 'indeed': 20, 'google': 15}
        score += platform_scores.get(platform, 10)
        
        # Company name quality (avoid obvious scams)
        if len(company) > 3 and company.replace(' ', '').isalpha():
            score += 15
        
        # Salary transparency
        if salary_range:
            score += 15
        if has_benefits:
            score += 10
        
        # Company rating (Glassdoor)
        if company_rating:
            try:
                rating = float(company_rating.split()[0])
                if rating >= 4.0:
                    score += 10
                elif rating >= 3.5:
                    score += 5
            except:
                pass
        
        # Description quality
        if len(description) > 100:
            score += 10
        
        return min(100, max(0, score))

    def _extract_skills(self, text: str) -> List[str]:
        """Extract relevant skills from job text"""
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'html', 'css', 'typescript',
            'angular', 'vue.js', 'php', 'ruby', 'go', 'rust', 'c++',
            'machine learning', 'data science', 'ai', 'blockchain',
            'marketing', 'seo', 'content writing', 'graphic design',
            'project management', 'scrum', 'agile', 'jira'
        ]
        
        text_lower = text.lower()
        found_skills = [skill for skill in common_skills if skill in text_lower]
        return found_skills[:10]  # Limit to top 10

    def _determine_experience_level(self, title: str, description: str) -> str:
        """Determine experience level from job text"""
        text = f"{title} {description}".lower()
        
        if any(term in text for term in ['senior', 'lead', 'principal', 'architect', 'manager']):
            return 'senior'
        elif any(term in text for term in ['junior', 'entry', 'graduate', 'intern']):
            return 'entry'
        elif any(term in text for term in ['mid', 'intermediate', '2-4 years', '3-5 years']):
            return 'mid'
        else:
            return 'unknown'

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse job posting date"""
        if not date_text:
            return None
            
        try:
            # Handle "X days ago" format
            if 'day' in date_text.lower():
                days_match = re.search(r'(\d+)', date_text)
                if days_match:
                    days_ago = int(days_match.group(1))
                    return datetime.utcnow() - timedelta(days=days_ago)
            
            # Handle "today", "yesterday"
            if 'today' in date_text.lower():
                return datetime.utcnow()
            elif 'yesterday' in date_text.lower():
                return datetime.utcnow() - timedelta(days=1)
                
        except Exception as e:
            print(f"⚠️ Error parsing date '{date_text}': {e}")
            
        return None