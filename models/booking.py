from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from .location import Location

class VehicleType(str, Enum):
    """Vehicle type enumeration"""
    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    PREMIUM = "premium"

class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    DRIVER_ACCEPTED = "driver_accepted"  # Driver accepted, waiting for passenger confirmation
    CONFIRMED = "confirmed"  # Both driver and passenger confirmed
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Booking(BaseModel):
    """Booking model"""
    booking_id: str
    passenger_id: str
    driver_id: Optional[str] = None
    pickup_location: Location
    dropoff_location: Optional[Location] = None
    vehicle_type: VehicleType
    status: BookingStatus = BookingStatus.PENDING
    fare: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_time_minutes: Optional[float] = None
    surge_multiplier: float = 1.0
    cancellation_fee: Optional[float] = None
    cancelled_by: Optional[str] = None  # "passenger" or "driver"
    cancelled_at: Optional[datetime] = None
    driver_accepted: bool = False  # Driver has accepted the booking
    passenger_confirmed: bool = False  # Passenger has confirmed/accepted the booking
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None  # When driver accepted
    confirmed_at: Optional[datetime] = None  # When passenger confirmed (both parties agreed)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        super().__init__(**data)
    
    def to_dict(self) -> dict:
        """Convert booking to dictionary"""
        return {
            "booking_id": self.booking_id,
            "passenger_id": self.passenger_id,
            "driver_id": self.driver_id,
            "pickup_location": self.pickup_location.to_dict(),
            "dropoff_location": self.dropoff_location.to_dict() if self.dropoff_location else None,
            "vehicle_type": self.vehicle_type.value,
            "status": self.status.value,
            "fare": self.fare,
            "distance_km": self.distance_km,
            "estimated_time_minutes": self.estimated_time_minutes,
            "surge_multiplier": self.surge_multiplier,
            "cancellation_fee": self.cancellation_fee,
            "cancelled_by": self.cancelled_by,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "driver_accepted": self.driver_accepted,
            "passenger_confirmed": self.passenger_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

