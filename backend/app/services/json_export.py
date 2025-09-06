import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class JsonExportService:
    """Service for exporting data to JSON files for n8n integration"""
    
    def __init__(self):
        base_dir = Path(__file__).resolve().parents[2]  # backend/
        self.export_base_path = str(base_dir / "data")  # Relative to backend directory
        
    def export_users(self, users: List[Dict], niche: str) -> str:
        """Export users to JSON file and return file path"""
        try:
            # Create directory if it doesn't exist
            export_dir = os.path.join(self.export_base_path, "exported_users")
            os.makedirs(export_dir, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{niche}_users_{timestamp}.json"
            filepath = os.path.join(export_dir, filename)
            
            # Prepare export data with metadata
            export_data = {
                "metadata": {
                    "niche": niche,
                    "total_users": len(users),
                    "exported_at": datetime.now().isoformat(),
                    "export_type": "instagram_users"
                },
                "users": self._serialize_data(users)
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Exported {len(users)} users to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting users: {str(e)}")
            raise

    def export_profiles(self, profiles: List[Dict]) -> str:
        """Export profiles to JSON file and return file path"""
        try:
            # Create directory if it doesn't exist
            export_dir = os.path.join(self.export_base_path, "exported_profiles")
            os.makedirs(export_dir, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"profiles_{timestamp}.json"
            filepath = os.path.join(export_dir, filename)
            
            # Prepare export data with metadata
            export_data = {
                "metadata": {
                    "total_profiles": len(profiles),
                    "exported_at": datetime.now().isoformat(),
                    "export_type": "instagram_profiles"
                },
                "profiles": self._serialize_data(profiles)
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Exported {len(profiles)} profiles to {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error exporting profiles: {str(e)}")
            raise
    
    def export_jobs(self, jobs: List[Dict], search_query: str) -> str:
        """Export jobs to JSON file and return file path"""
        try:
            # Create directory if it doesn't exist
            export_dir = os.path.join(self.export_base_path, "exported_jobs")
            os.makedirs(export_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{search_query}_jobs_{timestamp}.json"
            filepath = os.path.join(export_dir, filename)

            # Prepare export data with metadata
            export_data = {
                "metadata": {
                    "search_query": search_query,
                    "total_jobs": len(jobs),
                    "exported_at": datetime.now().isoformat(),
                    "export_type": "freelance_jobs",
                    "remote_jobs": sum(1 for job in jobs if job.get('is_remote_friendly')),
                    "contract_jobs": sum(1 for job in jobs if job.get('is_contract_work')),
                    "platforms": list(set(job.get('platform', 'unknown') for job in jobs))
                },
                "jobs": self._serialize_data(jobs)
            }

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)

            print(f"✅ Exported {len(jobs)} jobs to {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ Error exporting jobs: {str(e)}")
            raise

    def _serialize_data(self, data: List[Dict]) -> List[Dict]:
        """Serialize data for JSON export, handling special types"""
        serialized = []
        for item in data:
            serialized_item = {}
            for key, value in item.items():
                if isinstance(value, datetime):
                    serialized_item[key] = value.isoformat()
                elif hasattr(value, '__str__') and 'ObjectId' in str(type(value)):
                    serialized_item[key] = str(value)
                elif isinstance(value, list):
                    serialized_item[key] = [self._serialize_item(v) if isinstance(v, dict) else v for v in value]
                else:
                    serialized_item[key] = value
            serialized.append(serialized_item)
        return serialized
    
    def _serialize_item(self, item: Dict) -> Dict:
        """Helper to serialize nested items"""
        serialized = {}
        for key, value in item.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

# Global instance
json_export_service = JsonExportService()

# Test function (optional, for debugging)
if __name__ == "__main__":
    # Sample test data
    test_users = [
        {"username": "testuser", "follower_count": 1000, "scraped_at": datetime.now()}
    ]
    print(json_export_service.export_users(test_users, "test_niche"))