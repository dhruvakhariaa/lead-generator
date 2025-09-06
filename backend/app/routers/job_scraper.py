# app/routers/job_scraper.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
import asyncio

from app.services.playwright_job_scraper import PlaywrightJobScraper
from app.services.job_database import job_db_service
from app.services.json_export import json_export_service
from app.models.job_model import JobSearchRequest, JobFilters

router = APIRouter(prefix="/jobs", tags=["Job Scraper"])

@router.get("/search")
async def search_jobs(
    keywords: str = Query(..., description="Job search keywords (e.g., 'python developer', 'marketing remote')"),
    location: str = Query(default="remote", description="Location preference"),
    job_type: str = Query(default="contract", description="Job type: contract, freelance, full-time, part-time"),
    max_results: int = Query(default=10, description="Maximum jobs to scrape (1-20)"),
    platforms: str = Query(default="indeed,glassdoor,google", description="Comma-separated platforms")
):
    """
    Search for freelance and contract jobs across multiple platforms.
    Optimized for remote work and contract opportunities.
    """
    try:
        # Validate inputs
        if max_results > 20:
            max_results = 20
        if max_results < 1:
            max_results = 1
            
        platform_list = [p.strip() for p in platforms.split(',') if p.strip()]
        valid_platforms = ['indeed', 'glassdoor', 'google']
        platform_list = [p for p in platform_list if p in valid_platforms]
        
        if not platform_list:
            platform_list = ['indeed']
        
        print(f"🎯 Job search request: '{keywords}' | {location} | {job_type} | {max_results} results")
        
        # Perform scraping
        collected_jobs = []
        scraper_used = []
        
        async with PlaywrightJobScraper() as scraper:
            jobs = await scraper.scrape_jobs(
                keywords=keywords,
                location=location,
                job_type=job_type,
                max_results=max_results,
                platforms=platform_list
            )
            
            collected_jobs.extend(jobs)
            scraper_used = platform_list

        # Save to database
        saved_jobs = []
        if collected_jobs:
            saved_jobs = await job_db_service.save_jobs(collected_jobs)
        
        # Export to JSON
        file_path = ""
        if saved_jobs:
            file_path = json_export_service.export_jobs(saved_jobs, keywords.replace(' ', '_'))
        
        # Calculate some stats
        remote_count = sum(1 for job in saved_jobs if job.get('is_remote_friendly'))
        contract_count = sum(1 for job in saved_jobs if job.get('is_contract_work'))
        high_trust_count = sum(1 for job in saved_jobs if job.get('trust_score', 0) >= 70)
        
        return {
            "status": "success" if saved_jobs else "no_jobs_found",
            "total_jobs": len(saved_jobs),
            "remote_jobs": remote_count,
            "contract_jobs": contract_count,
            "high_trust_jobs": high_trust_count,
            "platforms_used": scraper_used,
            "search_params": {
                "keywords": keywords,
                "location": location,
                "job_type": job_type,
                "platforms": platform_list
            },
            "jobs": saved_jobs[:10],  # Return first 10 in response
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in job search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

@router.get("/remote")
async def get_remote_jobs(
    limit: int = Query(default=20, description="Number of remote jobs to return")
):
    """Get remote-friendly jobs from database"""
    try:
        jobs = await job_db_service.get_remote_jobs(limit)
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contract")
async def get_contract_jobs(
    limit: int = Query(default=20, description="Number of contract jobs to return")
):
    """Get contract/freelance jobs from database"""
    try:
        jobs = await job_db_service.get_contract_jobs(limit)
        return {
            "status": "success", 
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/high-paying")
async def get_high_paying_jobs(
    min_salary: int = Query(default=75000, description="Minimum salary filter"),
    limit: int = Query(default=20, description="Number of jobs to return")
):
    """Get high-paying jobs from database"""
    try:
        jobs = await job_db_service.get_high_paying_jobs(min_salary, limit)
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "min_salary": min_salary,
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced-search")
async def advanced_job_search(filters: JobFilters):
    """Advanced job search with multiple filters"""
    try:
        filter_dict = filters.model_dump()
        jobs = await job_db_service.search_jobs(filter_dict)
        
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "filters": filter_dict,
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-keywords/{keywords}")
async def get_jobs_by_keywords(
    keywords: str,
    limit: int = Query(default=20, description="Number of jobs to return")
):
    """Get jobs by keyword search from database"""
    try:
        keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
        jobs = await job_db_service.get_jobs_by_keywords(keyword_list, limit)
        
        return {
            "status": "success",
            "total_jobs": len(jobs),
            "keywords": keyword_list,
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms/{platform}")
async def get_jobs_by_platform(
    platform: str,
    limit: int = Query(default=20, description="Number of jobs to return")
):
    """Get jobs from specific platform"""
    try:
        if platform not in ['indeed', 'glassdoor', 'google']:
            raise HTTPException(status_code=400, detail="Invalid platform. Use: indeed, glassdoor, google")
        
        # Simple database query by platform
        jobs = []
        if job_db_service.is_connected():
            cursor = job_db_service.jobs_collection.find({"platform": platform}).sort("scraped_at", -1).limit(limit)
            jobs = await cursor.to_list(length=None)
        
        return {
            "status": "success",
            "platform": platform,
            "total_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))