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

class InstagramPost(BaseModel):
    post_id: str
    post_url: str
    caption: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    engagement_rate: float = 0.0
    hashtags: List[str] = []
    posted_at: Optional[datetime] = None

class InstagramProfile(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_verified: bool = False
    is_private: bool = False
    profile_pic_url: Optional[str] = None
    external_url: Optional[str] = None
    email: Optional[str] = None
    recent_posts: List[InstagramPost] = []
    engagement_rate: float = 0.0
    top_hashtags: List[str] = []
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
    }