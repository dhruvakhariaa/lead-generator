# app/routers/scraper.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import asyncio
import os

from app.services.service_factory import ServiceFactory
from app.services.database import db_service
from app.services.json_export import json_export_service

router = APIRouter(prefix="/scraper", tags=["Instagram Scraper"])

@router.get("/users")
async def scrape_users(
    niche: str = Query(..., description="Instagram hashtag without #"),
    min_followers: int = Query(5000, description="Minimum follower count"),
    target_count: int = Query(10, description="Target number of valid users"),
    max_results: int = Query(100, description="Maximum results to keep"),
    use_playwright_only: bool = Query(False, description="Skip Apify and use only Playwright")
):
    """
    Orchestrates Instagram scraping with proper service separation:
    - Apify primary (with fallback to Playwright)
    - Playwright fallback (with stealth + selector fixes)
    - Exports JSON & saves to DB
    """
    
    collected_users = []
    scraper_used = None
    
    try:
        if not use_playwright_only:
            # Try Apify first
            apify_scraper = ServiceFactory.create_instagram_scraper("apify", fallback=False)
            if apify_scraper:
                try:
                    async with apify_scraper as scraper:
                        print(f"🔍 Apify: starting scrape for #{niche}")
                        collected_users = await scraper.scrape_users(
                            niche=niche,
                            min_followers=min_followers,
                            target_count=target_count,
                            max_results=max_results
                        )
                        scraper_used = "apify"
                except Exception as e:
                    print(f"⚠️ Apify scraper failed: {e}")
                    collected_users = []

        # Playwright fallback if needed
        if len(collected_users) < target_count:
            print(f"⚠️ Primary scraper returned {len(collected_users)} users — falling back to Playwright")
            
            playwright_scraper = ServiceFactory.create_instagram_scraper("playwright")
            if playwright_scraper:
                try:
                    async with playwright_scraper as scraper:
                        playwright_users = await scraper.scrape_users(
                            niche=niche,
                            min_followers=min_followers,
                            target_count=target_count - len(collected_users),
                            max_results=max_results
                        )
                        collected_users.extend(playwright_users)
                        scraper_used = "apify+playwright" if scraper_used else "playwright"
                except Exception as e:
                    print(f"❌ Playwright scraper also failed: {e}")
                    if not collected_users:
                        raise HTTPException(status_code=500, detail="All scraping services failed")

        # Deduplicate by username
        seen = set()
        deduped_users = []
        for u in collected_users:
            if u.get("username") and u["username"] not in seen:
                deduped_users.append(u)
                seen.add(u["username"])

        # Save to DB
        if deduped_users:
            try:
                await db_service.save_users(deduped_users)
            except Exception as e:
                print(f"⚠️ Database save failed: {e}")

        # Export JSON
        file_path = ""
        if deduped_users:
            try:
                file_path = json_export_service.export_users(deduped_users, niche)
            except Exception as e:
                print(f"⚠️ JSON export failed: {e}")

        return {
            "status": "success" if deduped_users else "no_users_found",
            "scraper_used": scraper_used,
            "total_users": len(deduped_users),
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "service_info": ServiceFactory.get_available_services()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in scraper endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.get("/users/niche/{niche}")
async def get_users_by_niche(niche: str):
    """Get users by niche from database"""
    users = await db_service.get_users_by_niche(niche)
    if not users:
        raise HTTPException(status_code=404, detail="No users found for this niche")
    return users

@router.get("/services/status")
async def get_service_status():
    """Get status of available scraping services"""
    return {
        "services": ServiceFactory.get_available_services(),
        "timestamp": datetime.utcnow().isoformat()
    }