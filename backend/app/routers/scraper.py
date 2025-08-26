from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import asyncio
import os
from app.services.apify_scraper import ApifyScraper
from app.services.playwright_scraper import PlaywrightScraper
from app.services.database import db_service
from app.services.json_export import json_export_service

router = APIRouter(prefix="/scraper", tags=["Scraper"])

@router.get("/users")
async def scrape_users(
    niche: str = Query(..., description="Instagram hashtag without #"),
    min_followers: int = Query(5000, description="Minimum follower count"),
    target_count: int = Query(10, description="Target number of valid users"),
    max_results: int = Query(100, description="Maximum results to keep"),
    use_playwright_only: bool = Query(False, description="Skip Apify and use only Playwright")
):
    """
    Orchestrates scraping:
    - Apify primary (with fallback sources & proxy)
    - Playwright fallback (with stealth + selector fixes)
    - Exports JSON & saves to DB
    """

    collected_users = []
    scraper_used = None

    if not use_playwright_only:
        async with ApifyScraper() as apify:
            print(f"🔍 Apify: starting scrape for #{niche}")
            collected_users = await apify.scrape_users(
                niche=niche,
                min_followers=min_followers,
                target_count=target_count,
                max_results=max_results
            )
            scraper_used = "apify"

    # Playwright fallback
    if len(collected_users) < target_count:
        print(f"⚠️ Apify returned {len(collected_users)} users — falling back to Playwright")
        async with PlaywrightScraper() as pw:
            playwright_users = await pw.scrape_users(
                niche=niche,
                min_followers=min_followers,
                target_count=target_count - len(collected_users),
                max_results=max_results
            )
            collected_users.extend(playwright_users)
            scraper_used = "apify+playwright" if scraper_used else "playwright"

    # Deduplicate by username
    seen = set()
    deduped_users = []
    for u in collected_users:
        if u["username"] not in seen:
            deduped_users.append(u)
            seen.add(u["username"])

    # Save to DB
    if deduped_users:
        await db_service.save_users(deduped_users)

    # Export JSON
    file_path = json_export_service.export_users(
        niche=niche,
        users=deduped_users
    )

    return {
        "status": "success" if deduped_users else "no_users_found",
        "scraper_used": scraper_used,
        "total_users": len(deduped_users),
        "file_path": file_path,
        "timestamp": datetime.utcnow().isoformat()
    }