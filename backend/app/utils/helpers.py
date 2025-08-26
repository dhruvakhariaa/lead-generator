import re
from typing import Optional, List, Dict
from datetime import datetime
import json
import os

def clean_username(username: str) -> str:
    """Clean and validate Instagram username"""
    if not username:
        return ""
    
    # Remove @ symbol and whitespace
    username = username.strip().lstrip('@')
    
    # Instagram username validation (1-30 characters, letters, numbers, periods, underscores)
    if re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
        return username
    return ""

def parse_follower_count(follower_text: str) -> int:
    """Parse follower count from text (handles K, M, B suffixes and commas)"""
    if not follower_text:
        return 0
    
    # Remove commas and convert to lowercase
    text = follower_text.replace(',', '').lower()
    
    # Extract number and suffix
    match = re.search(r'(\d+\.?\d*)([kmb]?)', text)
    if not match:
        return 0
    
    num = float(match.group(1))
    suffix = match.group(2)
    
    # Apply multiplier based on suffix
    multipliers = {
        'k': 1000,
        'm': 1000000,
        'b': 1000000000
    }
    return int(num * multipliers.get(suffix, 1))

def format_number(num: int) -> str:
    """Format number with commas for readability"""
    return f"{num:,}"

def extract_email_from_bio(bio: str) -> Optional[str]:
    """Extract email address from bio text"""
    if not bio:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, bio)
    return emails[0] if emails else None

def calculate_engagement_rate(likes: int, comments: int, followers: int) -> float:
    """Calculate engagement rate as percentage"""
    if followers == 0:
        return 0.0
    return round(((likes + comments) / followers) * 100, 2)

def export_to_json(data: List[Dict], folder: str, name: str) -> str:
    """Export data to JSON file and return file path"""
    export_dir = os.path.join('data', folder)
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{name}_{timestamp}.json"
    filepath = os.path.join(export_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, default=str)  # Handle datetime and ObjectId
    
    print(f"✅ Exported to {filepath}")
    return filepath

# Example usage (for testing)
if __name__ == "__main__":
    # Test clean_username
    print(clean_username("@test.user_123"))  # Output: "test.user_123"
    
    # Test parse_follower_count
    print(parse_follower_count("1.5k"))  # Output: 1500
    print(parse_follower_count("2M"))  # Output: 2000000
    print(parse_follower_count("500"))  # Output: 500
    
    # Test extract_email_from_bio
    print(extract_email_from_bio("Contact me at test@example.com"))  # Output: "test@example.com"
    
    # Test calculate_engagement_rate
    print(calculate_engagement_rate(100, 20, 1000))  # Output: 12.0