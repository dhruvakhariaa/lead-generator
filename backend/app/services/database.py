# app/services/database.py
import motor.motor_asyncio
from bson import ObjectId
from app.utils.config import settings
from app.models.user_model import InstagramUser
from app.models.profile_model import InstagramProfile

class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.profiles_collection = None

    async def connect(self):
        """Connect to MongoDB and initialize collections."""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client.instagram_leads
        self.users_collection = self.db.users
        self.profiles_collection = self.db.profiles
        print("db connected")  # Matches your log

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
        print("db disconnected")  # Matches your log

    def is_connected(self) -> bool:
        """Check if the database is connected."""
        return self.db is not None
    
    async def get_users_by_niche(self, niche: str) -> list[dict]:
        if self.users_collection is None:
            raise ValueError("Database not connected. Call connect() first.")
        cursor = self.users_collection.find({"niche": niche})
        return await cursor.to_list(length=None)

    async def get_all_profiles(self) -> list[dict]:
        if self.profiles_collection is None:
            raise ValueError("Database not connected. Call connect() first.")
        cursor = self.profiles_collection.find({})
        return await cursor.to_list(length=None)


    async def save_users(self, users: list) -> list[dict]:
        """Save users to DB and return serialized list with string 'id'."""
        if self.users_collection is None:
            raise ValueError("Database not connected. Call connect() first.")
        
        # Convert Pydantic models to dicts if necessary (ensures insert_one works)
        user_dicts = []
        for user in users:
            if isinstance(user, InstagramUser):
                user_dicts.append(user.model_dump())
            elif isinstance(user, dict):
                user_dicts.append(user)
            else:
                raise ValueError(f"Unsupported user type: {type(user)}. Expected InstagramUser or dict.")
        
        inserted_ids = []
        for user_dict in user_dicts:
            result = await self.users_collection.insert_one(user_dict)
            inserted_ids.append(result.inserted_id)
        
        # Use aggregate to fetch back with serialized 'id' (exact pipeline provided)
        pipeline = [
            {"$match": {"_id": {"$in": inserted_ids}}},
            {"$project": {
                "id": {"$toString": "$_id"},
                "_id": 0,  # Exclude raw ObjectId from response
                "username": 1,
                "full_name": 1,
                "follower_count": 1,
                "following_count": 1,
                "posts_count": 1,
                "is_verified": 1,
                "is_private": 1,
                "is_business": 1,
                "profile_pic_url": 1,
                "external_url": 1,
                "niche": 1,
                "scraped_at": 1
            }}
        ]
        cursor = self.users_collection.aggregate(pipeline)
        serialized_users = await cursor.to_list(length=None)
        return serialized_users

    async def save_profile(self, profile) -> dict:
        """Save profile to DB and return serialized with string 'id'."""
        if self.profiles_collection is None:
            raise ValueError("Database not connected. Call connect() first.")
        
        # Convert Pydantic model to dict if necessary (ensures insert_one works)
        if isinstance(profile, InstagramProfile):
            profile_dict = profile.model_dump()
        elif isinstance(profile, dict):
            profile_dict = profile
        else:
            raise ValueError(f"Unsupported profile type: {type(profile)}. Expected InstagramProfile or dict.")
        
        result = await self.profiles_collection.insert_one(profile_dict)
        inserted_id = result.inserted_id
        
        # Use aggregate for single record (exact pipeline provided)
        pipeline = [
            {"$match": {"_id": inserted_id}},
            {"$project": {
                "id": {"$toString": "$_id"},
                "_id": 0,  # Exclude raw ObjectId from response
                "username": 1,
                "full_name": 1,
                "follower_count": 1,
                "following_count": 1,
                "posts_count": 1,
                "is_verified": 1,
                "is_private": 1,
                "is_business": 1,
                "profile_pic_url": 1,
                "external_url": 1,
                "niche": 1,
                "scraped_at": 1,
                "posts": 1  # Include if your profile model has posts (list of InstagramPost)
            }}
        ]
        cursor = self.profiles_collection.aggregate(pipeline)
        serialized_profile = await cursor.next()  # For single record
        return serialized_profile
    
    

# Global instance (assuming this is how it's exported for import in other files)
db_service = DatabaseService()