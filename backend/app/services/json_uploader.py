# app/services/json_uploader.py
import json
import os
from typing import List, Dict
from app.services.database import db_service  # Import existing DB service
from datetime import datetime
from app.models.user_model import InstagramUser  # For validation
from app.models.profile_model import InstagramProfile  # For validation
import logging

logging.basicConfig(level=logging.INFO)  # Set logging level

class JsonUploader:
    def __init__(self):
        self.users_dir = os.path.abspath("data/scraped_users/")  # Absolute path for reliability
        self.profiles_dir = os.path.abspath("data/scraped_profiles/")  # Absolute path
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.profiles_dir, exist_ok=True)

    async def upload_json_files(self):
        """Scan directories and upload all JSON files to MongoDB."""
        await self.upload_from_directory(self.users_dir, is_profile=False)
        await self.upload_from_directory(self.profiles_dir, is_profile=True)

    async def upload_from_directory(self, directory: str, is_profile: bool):
        """Upload JSON files from a directory to the appropriate collection."""
        if db_service.users_collection is None or db_service.profiles_collection is None:
            raise ValueError("Database not connected. Call connect() first.")
        
        collection = db_service.profiles_collection if is_profile else db_service.users_collection
        
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Handle list (for users) or dict (for profiles)
                    documents = data if isinstance(data, list) else [data]
                    
                    uploaded_count = 0
                    for doc in documents:
                        # Add or update metadata if needed (e.g., scraped_at)
                        if "scraped_at" not in doc:
                            doc["scraped_at"] = datetime.now().isoformat()
                        
                        # Validate with Pydantic to ensure proper dict format
                        if is_profile:
                            InstagramProfile.model_validate(doc)  # Validates structure
                        else:
                            InstagramUser.model_validate(doc)  # Validates structure
                        
                        # Upsert (insert or update if username exists)
                        result = await collection.update_one(
                            {"username": doc.get("username")},
                            {"$set": doc},
                            upsert=True
                        )
                        if result.upserted_id or result.modified_count > 0:
                            uploaded_count += 1
                            logging.info(f"Upserted document for username: {doc.get('username')}")
                        else:
                            logging.info(f"No change for username: {doc.get('username')} (already up-to-date)")
                    
                    # Optional: Delete file after successful upload (uncomment if desired)
                    # os.remove(file_path)
                    
                    logging.info(f"Processed {uploaded_count} documents from {filename} to {'profiles' if is_profile else 'users'} collection.")
                
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in {filename}: {str(e)}")
                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}")

    async def upload_users_from_json(self, json_path: str):
        """Upload a specific users JSON file to DB (callable from endpoints)."""
        await self.upload_from_directory(os.path.dirname(os.path.abspath(json_path)), is_profile=False)

    async def upload_profiles_from_json(self, json_path: str):
        """Upload a specific profiles JSON file to DB (callable from endpoints)."""
        await self.upload_from_directory(os.path.dirname(os.path.abspath(json_path)), is_profile=True)

# Global instance for import in other files (e.g., scraper.py)
json_uploader = JsonUploader()