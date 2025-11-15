from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .location import Location

class DriverLocation(BaseModel):
    """Driver location with availability status"""
    driver_id: str
    location: Location
    is_available: bool = False
    is_online: bool = False
    updated_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        """Convert driver location to dictionary"""
        return {
            "driver_id": self.driver_id,
            "location": self.location.to_dict(),
            "is_available": self.is_available,
            "is_online": self.is_online,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Driver(BaseModel):
    """Driver model"""
    driver_id: str
    name: str
    phone_number: str
    vehicle_type: str
    vehicle_number: Optional[str] = None
    is_online: bool = False
    is_available: bool = False
    current_location: Optional[Location] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        """Convert driver to dictionary"""
        return {
            "driver_id": self.driver_id,
            "name": self.name,
            "phone_number": self.phone_number,
            "vehicle_type": self.vehicle_type,
            "vehicle_number": self.vehicle_number,
            "is_online": self.is_online,
            "is_available": self.is_available,
            "current_location": self.current_location.to_dict() if self.current_location else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

