from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from models.driver import Driver, DriverLocation
from models.location import Location
from models.booking import Booking, BookingStatus
from services.memory_storage import get_memory_storage
from services.maps_service import MapsService
from services.fare_service import FareService

router = APIRouter(prefix="/driver", tags=["Driver"])

# Initialize services - use in-memory storage with hardcoded data
storage = get_memory_storage()
maps_service = MapsService()
fare_service = FareService()


class DriverRegisterRequest(BaseModel):
    """Request model for driver registration"""
    driver_id: str
    name: str
    phone_number: str
    vehicle_type: str
    vehicle_number: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    """Request model for driver location update"""
    driver_id: str
    latitude: float
    longitude: float


class SetAvailabilityRequest(BaseModel):
    """Request model for setting driver availability"""
    driver_id: str
    is_available: bool


class AcceptBookingRequest(BaseModel):
    """Request model for accepting a booking"""
    driver_id: str
    booking_id: str


class StartRideRequest(BaseModel):
    """Request model for starting a ride"""
    driver_id: str
    booking_id: str


class CompleteRideRequest(BaseModel):
    """Request model for completing a ride"""
    driver_id: str
    booking_id: str
    dropoff_latitude: Optional[float] = None
    dropoff_longitude: Optional[float] = None


@router.post("/register")
async def register_driver(request: DriverRegisterRequest):
    """
    Register a new driver
    """
    try:
        driver = Driver(
            driver_id=request.driver_id,
            name=request.name,
            phone_number=request.phone_number,
            vehicle_type=request.vehicle_type,
            vehicle_number=request.vehicle_number,
            is_online=False,
            is_available=False
        )
        
        success = storage.create_driver(
            request.driver_id,
            driver.to_dict()
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create driver")
        
        return {
            "success": True,
            "message": "Driver registered successfully",
            "driver_id": request.driver_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setavailability")
async def set_availability(request: SetAvailabilityRequest):
    """
    Set driver availability (go online/offline)
    """
    try:
        driver_data = storage.get_driver(request.driver_id)
        if not driver_data:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        update_data = {
            "is_available": request.is_available,
            "is_online": request.is_available,  # If available, must be online
            "updated_at": datetime.now().isoformat()
        }
        
        success = storage.update_driver(request.driver_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update driver availability")
        
        return {
            "success": True,
            "message": f"Driver {'online' if request.is_available else 'offline'}",
            "is_available": request.is_available,
            "is_online": request.is_available
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/updatelocation")
async def update_location(request: LocationUpdateRequest):
    """
    Update driver location (called every 3-5 seconds)
    """
    try:
        driver_data = storage.get_driver(request.driver_id)
        if not driver_data:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        location = Location(
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        # Update location in memory
        update_data = {
            "current_location": location.to_dict(),
            "updated_at": datetime.now().isoformat()
        }
        storage.update_driver(request.driver_id, update_data)
        
        # Store in locations collection for quick access
        driver_location = DriverLocation(
            driver_id=request.driver_id,
            location=location,
            is_available=driver_data.get("is_available", False),
            is_online=driver_data.get("is_online", False)
        )
        storage.update_driver_location(
            request.driver_id,
            driver_location.to_dict()
        )
        
        return {
            "success": True,
            "message": "Location updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{driver_id}")
async def get_driver_status(driver_id: str):
    """
    Get driver status and current bookings
    """
    try:
        driver_data = storage.get_driver(driver_id)
        if not driver_data:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Get active bookings for this driver
        all_bookings = storage.get_all_documents("bookings")
        active_bookings = [
            b for b in all_bookings
            if b.get("driver_id") == driver_id
            and b.get("status") in ["pending", "accepted", "in_progress"]
        ]
        
        return {
            "success": True,
            "driver": driver_data,
            "active_bookings": active_bookings,
            "booking_count": len(active_bookings)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bookings/{driver_id}")
async def get_driver_bookings(driver_id: str, status: Optional[str] = None):
    """
    Get all bookings for a driver, optionally filtered by status
    Calculates distance if missing based on pickup/dropoff locations
    """
    try:
        from services.maps_service import MapsService
        from models.location import Location
        
        maps_service = MapsService()
        all_bookings = storage.get_all_documents("bookings")
        driver_bookings = [
            b for b in all_bookings
            if b.get("driver_id") == driver_id
        ]
        
        if status:
            driver_bookings = [
                b for b in driver_bookings
                if b.get("status") == status.lower()
            ]
        
        # Calculate distance for bookings that don't have it
        for booking in driver_bookings:
            if not booking.get("distance_km") or booking.get("distance_km") == 0:
                pickup_data = booking.get("pickup_location")
                dropoff_data = booking.get("dropoff_location")
                
                if pickup_data and dropoff_data:
                    try:
                        pickup_loc = Location(
                            latitude=pickup_data["latitude"],
                            longitude=pickup_data["longitude"]
                        )
                        dropoff_loc = Location(
                            latitude=dropoff_data["latitude"],
                            longitude=dropoff_data["longitude"]
                        )
                        
                        distance_eta = maps_service.get_distance_and_eta(pickup_loc, dropoff_loc)
                        if distance_eta:
                            booking["distance_km"] = distance_eta[0]
                            booking["estimated_time_minutes"] = distance_eta[1]
                    except Exception as e:
                        print(f"Error calculating distance for booking {booking.get('booking_id')}: {e}")
        
        return {
            "success": True,
            "bookings": driver_bookings,
            "count": len(driver_bookings)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accept")
async def accept_booking(request: AcceptBookingRequest):
    """
    Driver accepts a booking
    """
    try:
        # Get booking
        booking_data = storage.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify driver matches
        if booking_data.get("driver_id") != request.driver_id:
            raise HTTPException(status_code=403, detail="Booking not assigned to this driver")
        
        # Verify booking status
        if booking_data.get("status") != "pending":
            raise HTTPException(status_code=400, detail=f"Booking is already {booking_data.get('status')}")
        
        # Verify driver is available
        driver_data = storage.get_driver(request.driver_id)
        if not driver_data or not driver_data.get("is_available"):
            raise HTTPException(status_code=400, detail="Driver is not available")
        
        # Update booking status - driver accepts, waiting for passenger confirmation
        update_data = {
            "status": BookingStatus.DRIVER_ACCEPTED.value,
            "driver_accepted": True,
            "accepted_at": datetime.now().isoformat()
        }
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update booking")
        
        # Get passenger details for driver
        passenger_id = booking_data.get("passenger_id")
        passenger_data = storage.get_passenger(passenger_id)
        
        # Get pickup location
        pickup_location = booking_data.get("pickup_location", {})
        
        return {
            "success": True,
            "message": "Booking accepted successfully. Waiting for passenger confirmation.",
            "booking_id": request.booking_id,
            "status": "driver_accepted",
            "passenger": {
                "name": passenger_data.get("name") if passenger_data else "Unknown",
                "phone_number": passenger_data.get("phone_number") if passenger_data else "Unknown"
            },
            "pickup_location": pickup_location,
            "fare": booking_data.get("fare"),
            "estimated_time": booking_data.get("estimated_time_minutes"),
            "waiting_for": "passenger_confirmation"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_ride(request: StartRideRequest):
    """
    Driver starts the ride
    """
    try:
        # Get booking
        booking_data = storage.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify driver matches
        if booking_data.get("driver_id") != request.driver_id:
            raise HTTPException(status_code=403, detail="Booking not assigned to this driver")
        
        # Verify booking status - both driver and passenger must have confirmed
        if booking_data.get("status") != "confirmed":
            driver_accepted = booking_data.get("driver_accepted", False)
            passenger_confirmed = booking_data.get("passenger_confirmed", False)
            
            if not driver_accepted:
                raise HTTPException(status_code=400, detail="Driver must accept the booking first")
            if not passenger_confirmed:
                raise HTTPException(status_code=400, detail="Passenger must confirm the booking before starting the ride")
            
            raise HTTPException(status_code=400, detail="Booking must be confirmed by both parties before starting")
        
        # Update booking status
        update_data = {
            "status": BookingStatus.IN_PROGRESS.value,
            "started_at": datetime.now().isoformat()
        }
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update booking")
        
        # Mark driver as unavailable
        storage.update_driver(request.driver_id, {"is_available": False})
        
        return {
            "success": True,
            "message": "Ride started successfully",
            "booking_id": request.booking_id,
            "status": "in_progress"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def complete_ride(request: CompleteRideRequest):
    """
    Driver completes the ride
    """
    try:
        # Get booking
        booking_data = storage.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify driver matches
        if booking_data.get("driver_id") != request.driver_id:
            raise HTTPException(status_code=403, detail="Booking not assigned to this driver")
        
        # Verify booking status
        if booking_data.get("status") != "in_progress":
            raise HTTPException(status_code=400, detail="Ride must be in progress before completing")
        
        # Update dropoff location if provided
        update_data = {
            "status": BookingStatus.COMPLETED.value,
            "completed_at": datetime.now().isoformat()
        }
        
        if request.dropoff_latitude and request.dropoff_longitude:
            dropoff_location = Location(
                latitude=request.dropoff_latitude,
                longitude=request.dropoff_longitude
            )
            update_data["dropoff_location"] = dropoff_location.to_dict()
            
            # Recalculate fare if dropoff location is different
            pickup_location_data = booking_data.get("pickup_location", {})
            if pickup_location_data:
                pickup_location = Location(
                    latitude=pickup_location_data["latitude"],
                    longitude=pickup_location_data["longitude"]
                )
                
                distance_eta = maps_service.get_distance_and_eta(
                    pickup_location,
                    dropoff_location
                )
                
                if distance_eta:
                    distance_km, duration_minutes = distance_eta
                    
                    # Calculate final fare
                    passenger_count = len(storage.get_all_documents("passengers"))
                    driver_count = len(storage.get_available_drivers())
                    
                    fare, surge_multiplier = fare_service.calculate_fare_with_surge(
                        distance_km,
                        duration_minutes,
                        passenger_count,
                        driver_count
                    )
                    
                    update_data["fare"] = fare
                    update_data["distance_km"] = distance_km
                    update_data["estimated_time_minutes"] = duration_minutes
                    update_data["surge_multiplier"] = surge_multiplier
        
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update booking")
        
        # Mark driver as available again
        storage.update_driver(request.driver_id, {"is_available": True})
        
        # Get updated booking
        updated_booking = storage.get_booking(request.booking_id)
        
        return {
            "success": True,
            "message": "Ride completed successfully",
            "booking_id": request.booking_id,
            "status": "completed",
            "final_fare": updated_booking.get("fare") if updated_booking else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/booking/{booking_id}")
async def get_booking(booking_id: str):
    """
    Get booking details
    """
    try:
        booking_data = storage.get_booking(booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return {
            "success": True,
            "booking": booking_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CancelBookingRequest(BaseModel):
    """Request model for cancelling a booking"""
    driver_id: str
    booking_id: str


@router.post("/cancel")
async def cancel_booking(request: CancelBookingRequest):
    """
    Cancel a booking by driver
    Note: Driver cancellations may have different fee structures or penalties
    """
    try:
        # Get booking
        booking_data = storage.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify driver matches
        if booking_data.get("driver_id") != request.driver_id:
            raise HTTPException(status_code=403, detail="Booking not assigned to this driver")
        
        # Check if booking can be cancelled
        status = booking_data.get("status")
        if status in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Booking is already {status}")
        
        if status == "in_progress":
            raise HTTPException(status_code=400, detail="Cannot cancel a ride that is in progress")
        
        # Note: Can cancel at any stage before ride starts (pending, driver_accepted, confirmed)
        
        # For driver cancellations, typically no fee is charged to passenger
        # But you can implement driver penalty logic here if needed
        cancellation_fee = 0.0  # Driver cancellations don't charge passenger
        
        # Update booking status
        update_data = {
            "status": BookingStatus.CANCELLED.value,
            "cancelled_by": "driver",
            "cancelled_at": datetime.now().isoformat(),
            "cancellation_fee": cancellation_fee
        }
        
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel booking")
        
        # Make driver available again
        storage.update_driver(request.driver_id, {"is_available": True})
        
        return {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_id": request.booking_id,
            "cancellation_fee": cancellation_fee,
            "status": "cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

