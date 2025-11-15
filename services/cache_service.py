from upstash_redis import Redis
from typing import Optional, Any
import json
from config import Config
from datetime import timedelta

class CacheService:
    """Service class for Upstash Redis cache operations"""
    
    def __init__(self):
        """Initialize Upstash Redis client"""
        if Config.UPSTASH_REDIS_URL and Config.UPSTASH_REDIS_TOKEN:
            self.redis = Redis(url=Config.UPSTASH_REDIS_URL, token=Config.UPSTASH_REDIS_TOKEN)
        else:
            self.redis = None
            print("Warning: Upstash Redis not configured. Caching disabled.")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL (time to live in seconds)"""
        if not self.redis:
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis.setex(key, ttl or 3600, value)
            return True
        except Exception as e:
            print(f"Error setting cache: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        if not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            print(f"Error getting cache: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting cache: {str(e)}")
            return False
    
    def set_driver_location(self, driver_id: str, location_data: dict, ttl: int = 10) -> bool:
        """Cache driver location with short TTL"""
        key = f"driver_location:{driver_id}"
        return self.set(key, location_data, ttl)
    
    def get_driver_location(self, driver_id: str) -> Optional[dict]:
        """Get cached driver location"""
        key = f"driver_location:{driver_id}"
        return self.get(key)
    
    def set_passenger_location(self, user_id: str, location_data: dict, ttl: int = 60) -> bool:
        """Cache passenger location"""
        key = f"passenger_location:{user_id}"
        return self.set(key, location_data, ttl)
    
    def get_passenger_location(self, user_id: str) -> Optional[dict]:
        """Get cached passenger location"""
        key = f"passenger_location:{user_id}"
        return self.get(key)
    
    def set_available_drivers(self, drivers: list, ttl: int = 5) -> bool:
        """Cache available drivers list"""
        key = "available_drivers"
        return self.set(key, drivers, ttl)
    
    def get_available_drivers(self) -> Optional[list]:
        """Get cached available drivers list"""
        key = "available_drivers"
        return self.get(key)

