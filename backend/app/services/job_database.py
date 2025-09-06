# app/services/job_database.py

import motor.motor_asyncio
from bson import ObjectId
from app.utils.config import settings
from app.models.job_model import JobListing
from typing import List, Dict, Optional

class JobDatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self.jobs_collection = None

    async def connect(self):
        """Connect to MongoDB and initialize job collections."""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client.freelancer_leads  # Separate database for jobs
        self.jobs_collection = self.db.jobs
        
        # Create indexes for efficient querying
        await self._create_indexes()
        print("job db connected")

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
        print("job db disconnected")

    async def _create_indexes(self):
        """Create database indexes for efficient querying."""
        try:
            # Index for search queries
            await self.jobs_collection.create_index([
                ("search_keywords", 1),
                ("platform", 1),
                ("scraped_at", -1)
            ])
            
            # Index for salary filtering
            await self.jobs_collection.create_index([
                ("salary_min", 1),
                ("salary_max", 1),
                ("is_remote_friendly", 1)
            ])
            
            # Index for job type filtering
            await self.jobs_collection.create_index([
                ("job_type", 1),
                ("is_contract_work", 1),
                ("trust_score", -1)
            ])
            
            # Unique index to prevent duplicates
            await self.jobs_collection.create_index([
                ("job_id", 1),
                ("platform", 1)
            ], unique=True)
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")

    def is_connected(self) -> bool:
        """Check if the database is connected."""
        return self.db is not None

    async def save_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Save jobs to DB and return serialized list with string 'id'."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected. Call connect() first.")

        # Convert to dicts if needed
        job_dicts = []
        for job in jobs:
            if isinstance(job, JobListing):
                job_dicts.append(job.model_dump())
            elif isinstance(job, dict):
                job_dicts.append(job)
            else:
                raise ValueError(f"Unsupported job type: {type(job)}")

        # Upsert jobs (prevent duplicates based on job_id + platform)
        inserted_ids = []
        updated_count = 0
        
        for job_dict in job_dicts:
            try:
                result = await self.jobs_collection.update_one(
                    {
                        "job_id": job_dict.get("job_id"),
                        "platform": job_dict.get("platform")
                    },
                    {"$set": job_dict},
                    upsert=True
                )
                
                if result.upserted_id:
                    inserted_ids.append(result.upserted_id)
                elif result.modified_count > 0:
                    # Find the existing job's ObjectId
                    existing = await self.jobs_collection.find_one({
                        "job_id": job_dict.get("job_id"),
                        "platform": job_dict.get("platform")
                    })
                    if existing:
                        inserted_ids.append(existing["_id"])
                        updated_count += 1
                        
            except Exception as e:
                print(f"⚠️ Error saving job {job_dict.get('title', 'Unknown')}: {e}")
                continue

        # Fetch back the saved jobs with serialized IDs
        if inserted_ids:
            pipeline = [
                {"$match": {"_id": {"$in": inserted_ids}}},
                {"$project": {
                    "id": {"$toString": "$_id"},
                    "_id": 0,
                    "job_id": 1,
                    "title": 1,
                    "company_name": 1,
                    "location": 1,
                    "is_remote_friendly": 1,
                    "job_type": 1,
                    "is_contract_work": 1,
                    "salary_range": 1,
                    "salary_min": 1,
                    "salary_max": 1,
                    "description": 1,
                    "requirements": 1,
                    "skills": 1,
                    "posted_date": 1,
                    "application_url": 1,
                    "platform": 1,
                    "company_website": 1,
                    "contact_email": 1,
                    "trust_score": 1,
                    "experience_level": 1,
                    "benefits": 1,
                    "scraped_at": 1,
                    "search_keywords": 1
                }}
            ]
            
            cursor = self.jobs_collection.aggregate(pipeline)
            serialized_jobs = await cursor.to_list(length=None)
            
            print(f"✅ Saved {len(serialized_jobs)} jobs ({len(inserted_ids) - updated_count} new, {updated_count} updated)")
            return serialized_jobs
        
        return []

    async def get_jobs_by_keywords(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """Get jobs by search keywords."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected.")
        
        # Create search query
        query = {
            "$or": [
                {"search_keywords": {"$in": keywords}},
                {"title": {"$regex": "|".join(keywords), "$options": "i"}},
                {"description": {"$regex": "|".join(keywords), "$options": "i"}}
            ]
        }
        
        cursor = self.jobs_collection.find(query).sort("scraped_at", -1).limit(limit)
        return await cursor.to_list(length=None)

    async def get_remote_jobs(self, limit: int = 50) -> List[Dict]:
        """Get remote-friendly jobs."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected.")
        
        query = {"is_remote_friendly": True}
        cursor = self.jobs_collection.find(query).sort([("trust_score", -1), ("scraped_at", -1)]).limit(limit)
        return await cursor.to_list(length=None)

    async def get_contract_jobs(self, limit: int = 50) -> List[Dict]:
        """Get contract/freelance jobs."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected.")
        
        query = {
            "$or": [
                {"is_contract_work": True},
                {"job_type": {"$in": ["contract", "freelance", "project"]}}
            ]
        }
        cursor = self.jobs_collection.find(query).sort([("salary_min", -1), ("scraped_at", -1)]).limit(limit)
        return await cursor.to_list(length=None)

    async def get_high_paying_jobs(self, min_salary: int = 50000, limit: int = 50) -> List[Dict]:
        """Get high-paying jobs."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected.")
        
        query = {"salary_min": {"$gte": min_salary}}
        cursor = self.jobs_collection.find(query).sort([("salary_min", -1), ("trust_score", -1)]).limit(limit)
        return await cursor.to_list(length=None)

    async def search_jobs(self, filters: Dict) -> List[Dict]:
        """Advanced job search with filters."""
        if self.jobs_collection is None:
            raise ValueError("Database not connected.")
        
        query = {}
        
        # Keyword search
        if filters.get("keywords"):
            keywords = filters["keywords"]
            if isinstance(keywords, str):
                keywords = [keywords]
            query["$or"] = [
                {"search_keywords": {"$in": keywords}},
                {"title": {"$regex": "|".join(keywords), "$options": "i"}},
                {"skills": {"$in": keywords}}
            ]
        
        # Location filter
        if filters.get("location") and filters["location"].lower() not in ["any", "anywhere"]:
            if filters["location"].lower() in ["remote", "work from home"]:
                query["is_remote_friendly"] = True
            else:
                query["location"] = {"$regex": filters["location"], "$options": "i"}
        
        # Job type filter
        if filters.get("job_type"):
            query["job_type"] = {"$regex": filters["job_type"], "$options": "i"}
        
        # Contract work filter
        if filters.get("is_contract_only"):
            query["is_contract_work"] = True
        
        # Remote only filter
        if filters.get("is_remote_only"):
            query["is_remote_friendly"] = True
        
        # Salary filter
        if filters.get("min_salary"):
            query["salary_min"] = {"$gte": filters["min_salary"]}
        
        # Experience level filter
        if filters.get("experience_level"):
            query["experience_level"] = filters["experience_level"]
        
        limit = filters.get("max_results", 50)
        cursor = self.jobs_collection.find(query).sort([
            ("trust_score", -1),
            ("salary_min", -1),
            ("scraped_at", -1)
        ]).limit(limit)
        
        return await cursor.to_list(length=None)

# Global instance
job_db_service = JobDatabaseService()