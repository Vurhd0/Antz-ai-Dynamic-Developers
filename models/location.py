from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Location(BaseModel):
    """Location model for GPS coordinates"""
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        """Convert location to dictionary"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

