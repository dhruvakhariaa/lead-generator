# app/models/job_model.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(cls),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class JobListing(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    job_id: str = Field(..., description="Unique identifier from the platform")
    title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    is_remote_friendly: bool = Field(default=False, description="Remote work allowed")
    job_type: str = Field(..., description="full-time, part-time, contract, freelance")
    is_contract_work: bool = Field(default=False, description="Contract/project based")
    salary_range: Optional[str] = Field(None, description="Salary information if available")
    salary_min: Optional[int] = Field(None, description="Minimum salary (parsed)")
    salary_max: Optional[int] = Field(None, description="Maximum salary (parsed)")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default=[], description="Job requirements")
    skills: List[str] = Field(default=[], description="Required skills")
    posted_date: Optional[datetime] = Field(None, description="When job was posted")
    application_url: str = Field(..., description="URL to apply")
    platform: str = Field(..., description="indeed, glassdoor, google")
    company_website: Optional[str] = Field(None, description="Company website")
    contact_email: Optional[str] = Field(None, description="Contact email if available")
    trust_score: int = Field(default=0, description="Trust score 0-100 based on company indicators")
    experience_level: str = Field(default="unknown", description="entry, mid, senior, executive")
    benefits: List[str] = Field(default=[], description="Job benefits")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    search_keywords: List[str] = Field(default=[], description="Keywords used to find this job")

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
    }

class JobSearchRequest(BaseModel):
    keywords: str = Field(..., description="Job search keywords")
    location: str = Field(default="remote", description="Location filter")
    job_type: str = Field(default="contract", description="Job type filter")
    min_salary: Optional[int] = Field(None, description="Minimum salary filter")
    max_results: int = Field(default=10, description="Maximum results to return")
    platforms: List[str] = Field(default=["indeed", "glassdoor", "google"], description="Platforms to search")

class JobFilters(BaseModel):
    keywords: List[str]
    location: str
    job_type: str
    min_salary: Optional[int] = None
    experience_level: Optional[str] = None
    is_remote_only: bool = False
    is_contract_only: bool = False