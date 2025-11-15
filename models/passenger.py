from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .location import Location
from .booking import VehicleType

class PassengerLocation(BaseModel):
    """Passenger location with user details"""
    user_id: str
    location: Location
    phone_number: Optional[str] = None
    name: Optional[str] = None
    vehicle_preference: Optional[VehicleType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        """Convert passenger location to dictionary"""
        return {
            "user_id": self.user_id,
            "location": self.location.to_dict(),
            "phone_number": self.phone_number,
            "name": self.name,
            "vehicle_preference": self.vehicle_preference.value if self.vehicle_preference else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Passenger(BaseModel):
    """Passenger model"""
    user_id: str
    phone_number: str
    name: str
    vehicle_preference: Optional[VehicleType] = None
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
        """Convert passenger to dictionary"""
        return {
            "user_id": self.user_id,
            "phone_number": self.phone_number,
            "name": self.name,
            "vehicle_preference": self.vehicle_preference.value if self.vehicle_preference else None,
            "current_location": self.current_location.to_dict() if self.current_location else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

