from fastapi import APIRouter, HTTPException, Response
from app.services.database import db_service
from app.services.json_export import json_export_service

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/users/{niche}", response_class=Response)
async def export_users(niche: str):
    """Export scraped users for a niche to JSON"""
    try:
        users = await db_service.get_users_by_niche(niche)
        if not users:
            raise HTTPException(status_code=404, detail="No users found for this niche")
        json_path = json_export_service.export_users(users, niche)
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={niche}_users.json"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles", response_class=Response)
async def export_profiles():
    """Export all scraped profiles to JSON"""
    try:
        profiles = await db_service.get_all_profiles()
        if not profiles:
            raise HTTPException(status_code=404, detail="No profiles found")
        json_path = json_export_service.export_profiles(profiles)
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=all_profiles.json"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))