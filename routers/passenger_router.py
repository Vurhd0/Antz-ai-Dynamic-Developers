from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from models.passenger import Passenger, PassengerLocation
from models.location import Location
from models.booking import Booking, BookingStatus, VehicleType
from services.firebase_service import FirebaseService
from services.cache_service import CacheService
from services.maps_service import MapsService
from services.fare_service import FareService
from config import Config

router = APIRouter(prefix="/passenger", tags=["Passenger"])

# Initialize services
firebase_service = FirebaseService()
cache_service = CacheService()
maps_service = MapsService()
fare_service = FareService()


class PassengerRegisterRequest(BaseModel):
    """Request model for passenger registration"""
    user_id: str
    latitude: float
    longitude: float
    phone_number: str
    name: str
    vehicle_preference: Optional[str] = None


class PassengerUpdateRequest(BaseModel):
    """Request model for updating passenger details"""
    phone_number: Optional[str] = None
    name: Optional[str] = None
    vehicle_preference: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    """Request model for location update"""
    user_id: str
    latitude: float
    longitude: float


class NearbyTaxisRequest(BaseModel):
    """Request model for requesting nearby taxis"""
    user_id: str
    latitude: float
    longitude: float
    vehicle_preference: Optional[str] = None


class BookTaxiRequest(BaseModel):
    """Request model for booking a taxi"""
    user_id: str
    driver_id: str
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: Optional[float] = None
    dropoff_longitude: Optional[float] = None
    vehicle_preference: Optional[str] = None


@router.post("/register")
async def register_passenger(request: PassengerRegisterRequest):
    """
    Register a new passenger and store their location
    """
    try:
        # Create location object
        location = Location(
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        # Determine vehicle type
        vehicle_type = None
        if request.vehicle_preference:
            try:
                vehicle_type = VehicleType(request.vehicle_preference.lower())
            except ValueError:
                vehicle_type = None
        
        # Create passenger object
        passenger = Passenger(
            user_id=request.user_id,
            phone_number=request.phone_number,
            name=request.name,
            vehicle_preference=vehicle_type,
            current_location=location
        )
        
        # Store in Firebase
        success = firebase_service.create_passenger(
            request.user_id,
            passenger.to_dict()
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create passenger")
        
        # Cache location
        location_data = {
            "user_id": request.user_id,
            "location": location.to_dict(),
            "phone_number": request.phone_number,
            "name": request.name,
            "vehicle_preference": vehicle_type.value if vehicle_type else None
        }
        cache_service.set_passenger_location(request.user_id, location_data)
        
        return {
            "success": True,
            "message": "Passenger registered successfully",
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update")
async def update_passenger(request: PassengerUpdateRequest, user_id: str = Body(...)):
    """
    Update passenger details
    """
    try:
        # Get existing passenger
        passenger_data = firebase_service.get_passenger(user_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Update fields
        update_data = {}
        if request.phone_number:
            update_data["phone_number"] = request.phone_number
        if request.name:
            update_data["name"] = request.name
        if request.vehicle_preference:
            try:
                vehicle_type = VehicleType(request.vehicle_preference.lower())
                update_data["vehicle_preference"] = vehicle_type.value
            except ValueError:
                pass
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Update in Firebase
        success = firebase_service.update_passenger(user_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update passenger")
        
        return {
            "success": True,
            "message": "Passenger updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/location/update")
async def update_passenger_location(request: LocationUpdateRequest):
    """
    Update passenger location
    """
    try:
        location = Location(
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        # Get passenger data
        passenger_data = firebase_service.get_passenger(request.user_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Update location in Firebase
        update_data = {
            "current_location": location.to_dict(),
            "updated_at": datetime.now().isoformat()
        }
        firebase_service.update_passenger(request.user_id, update_data)
        
        # Update cache
        location_data = {
            "user_id": request.user_id,
            "location": location.to_dict(),
            "phone_number": passenger_data.get("phone_number"),
            "name": passenger_data.get("name"),
            "vehicle_preference": passenger_data.get("vehicle_preference")
        }
        cache_service.set_passenger_location(request.user_id, location_data)
        
        return {
            "success": True,
            "message": "Location updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nearby-taxis")
async def get_nearby_taxis(request: NearbyTaxisRequest):
    """
    Get nearby available taxis with ETA and fare estimates
    """
    try:
        passenger_location = Location(
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        # Get available drivers from Firebase
        available_drivers = firebase_service.get_available_drivers()
        
        if not available_drivers:
            return {
                "success": True,
                "drivers": [],
                "message": "No available drivers found"
            }
        
        # Filter by vehicle preference if specified
        if request.vehicle_preference:
            try:
                preferred_type = VehicleType(request.vehicle_preference.lower())
                available_drivers = [
                    d for d in available_drivers
                    if d.get("vehicle_type", "").lower() == preferred_type.value
                ]
            except ValueError:
                pass
        
        # Get driver locations from cache or Firebase
        driver_locations = []
        for driver in available_drivers:
            driver_id = driver.get("driver_id")
            if not driver_id:
                continue
            
            # Try cache first
            cached_location = cache_service.get_driver_location(driver_id)
            if cached_location and cached_location.get("location"):
                loc_data = cached_location["location"]
                location = Location(
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"]
                )
            elif driver.get("current_location"):
                loc_data = driver["current_location"]
                location = Location(
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"]
                )
            else:
                continue
            
            driver_locations.append((driver_id, location))
        
        if not driver_locations:
            return {
                "success": True,
                "drivers": [],
                "message": "No drivers with location data found"
            }
        
        # Calculate distances and ETAs using Google Maps API
        driver_results = maps_service.get_nearby_drivers_with_eta(
            passenger_location,
            driver_locations
        )
        
        # Get passenger and driver counts for surge calculation
        passenger_count = len(firebase_service.get_all_documents("passengers"))
        driver_count = len(available_drivers)
        
        # Calculate fare for each driver
        for result in driver_results:
            distance_km = result["distance_km"]
            eta_minutes = result["eta_minutes"]
            
            fare, surge_multiplier = fare_service.calculate_fare_with_surge(
                distance_km,
                eta_minutes,
                passenger_count,
                driver_count
            )
            
            result["estimated_fare"] = fare
            result["surge_multiplier"] = surge_multiplier
            
            # Add driver details
            driver_id = result["driver_id"]
            driver_data = next((d for d in available_drivers if d.get("driver_id") == driver_id), {})
            result["driver_name"] = driver_data.get("name", "")
            result["driver_phone"] = driver_data.get("phone_number", "")
            result["vehicle_type"] = driver_data.get("vehicle_type", "")
        
        return {
            "success": True,
            "drivers": driver_results,
            "count": len(driver_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book")
async def book_taxi(request: BookTaxiRequest):
    """
    Book a taxi with a specific driver
    """
    try:
        # Verify passenger exists
        passenger_data = firebase_service.get_passenger(request.user_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Verify driver exists and is available
        driver_data = firebase_service.get_driver(request.driver_id)
        if not driver_data:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        if not driver_data.get("is_available") or not driver_data.get("is_online"):
            raise HTTPException(status_code=400, detail="Driver is not available")
        
        # Create pickup location
        pickup_location = Location(
            latitude=request.pickup_latitude,
            longitude=request.pickup_longitude
        )
        
        # Create dropoff location if provided
        dropoff_location = None
        if request.dropoff_latitude and request.dropoff_longitude:
            dropoff_location = Location(
                latitude=request.dropoff_latitude,
                longitude=request.dropoff_longitude
            )
        
        # Determine vehicle type
        vehicle_type = VehicleType.SEDAN  # Default
        if request.vehicle_preference:
            try:
                vehicle_type = VehicleType(request.vehicle_preference.lower())
            except ValueError:
                pass
        elif passenger_data.get("vehicle_preference"):
            try:
                vehicle_type = VehicleType(passenger_data["vehicle_preference"])
            except ValueError:
                pass
        
        # Calculate distance and ETA
        driver_location_data = cache_service.get_driver_location(request.driver_id)
        if driver_location_data and driver_location_data.get("location"):
            driver_loc = Location(
                latitude=driver_location_data["location"]["latitude"],
                longitude=driver_location_data["location"]["longitude"]
            )
        elif driver_data.get("current_location"):
            loc_data = driver_data["current_location"]
            driver_loc = Location(
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"]
            )
        else:
            raise HTTPException(status_code=400, detail="Driver location not available")
        
        # Get distance and ETA
        distance_eta = maps_service.get_distance_and_eta(driver_loc, pickup_location)
        if not distance_eta:
            raise HTTPException(status_code=500, detail="Failed to calculate distance")
        
        distance_km, eta_minutes = distance_eta
        
        # Calculate fare
        passenger_count = len(firebase_service.get_all_documents("passengers"))
        driver_count = len(firebase_service.get_available_drivers())
        
        fare, surge_multiplier = fare_service.calculate_fare_with_surge(
            distance_km,
            eta_minutes,
            passenger_count,
            driver_count
        )
        
        # Create booking
        booking_id = str(uuid.uuid4())
        booking = Booking(
            booking_id=booking_id,
            passenger_id=request.user_id,
            driver_id=request.driver_id,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            vehicle_type=vehicle_type,
            status=BookingStatus.PENDING,
            fare=fare,
            distance_km=distance_km,
            estimated_time_minutes=eta_minutes,
            surge_multiplier=surge_multiplier
        )
        
        # Store booking in Firebase
        success = firebase_service.create_booking(booking_id, booking.to_dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create booking")
        
        return {
            "success": True,
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "booking": booking.to_dict()
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
        booking_data = firebase_service.get_booking(booking_id)
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


class ConfirmBookingRequest(BaseModel):
    """Request model for passenger to confirm/accept a booking"""
    user_id: str
    booking_id: str


@router.post("/confirm")
async def confirm_booking(request: ConfirmBookingRequest):
    """
    Passenger confirms/accepts a booking after driver has accepted
    Both parties must confirm before the ride can start
    """
    try:
        # Get booking
        booking_data = firebase_service.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify passenger matches
        if booking_data.get("passenger_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Booking does not belong to this passenger")
        
        # Check if driver has already accepted
        if not booking_data.get("driver_accepted", False):
            raise HTTPException(status_code=400, detail="Driver must accept the booking first before passenger can confirm")
        
        # Check if already confirmed
        if booking_data.get("passenger_confirmed", False):
            raise HTTPException(status_code=400, detail="Booking is already confirmed")
        
        # Check booking status
        status = booking_data.get("status")
        if status in ["completed", "cancelled", "in_progress"]:
            raise HTTPException(status_code=400, detail=f"Cannot confirm booking that is {status}")
        
        # Update booking - passenger confirms, both parties now agreed
        update_data = {
            "status": BookingStatus.CONFIRMED.value,
            "passenger_confirmed": True,
            "confirmed_at": datetime.now().isoformat()
        }
        
        success = firebase_service.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to confirm booking")
        
        # Get driver details for passenger
        driver_id = booking_data.get("driver_id")
        driver_data = None
        if driver_id:
            driver_data = firebase_service.get_driver(driver_id)
        
        return {
            "success": True,
            "message": "Booking confirmed successfully. Ride can now be started.",
            "booking_id": request.booking_id,
            "status": "confirmed",
            "driver": {
                "name": driver_data.get("name") if driver_data else "Unknown",
                "phone_number": driver_data.get("phone_number") if driver_data else "Unknown",
                "vehicle_type": driver_data.get("vehicle_type") if driver_data else "Unknown"
            },
            "fare": booking_data.get("fare"),
            "ready_to_start": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CancelBookingRequest(BaseModel):
    """Request model for cancelling a booking"""
    user_id: str
    booking_id: str


@router.post("/cancel")
async def cancel_booking(request: CancelBookingRequest):
    """
    Cancel a booking by passenger
    Calculates and charges cancellation fee based on driver proximity and time
    """
    try:
        # Get booking
        booking_data = firebase_service.get_booking(request.booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Verify passenger matches
        if booking_data.get("passenger_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Booking does not belong to this passenger")
        
        # Check if booking can be cancelled
        status = booking_data.get("status")
        if status in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail=f"Booking is already {status}")
        
        if status == "in_progress":
            raise HTTPException(status_code=400, detail="Cannot cancel a ride that is in progress")
        
        # Note: Can cancel at any stage before ride starts (pending, driver_accepted, confirmed)
        
        # Get booking details for cancellation fee calculation
        total_fare = booking_data.get("fare", 0.0)
        if not total_fare or total_fare == 0:
            # If fare not set, use a default minimum
            total_fare = Config.BASE_FARE
        
        # Get vehicle type
        vehicle_type_str = booking_data.get("vehicle_type", "sedan")
        try:
            vehicle_type = VehicleType(vehicle_type_str.lower())
        except ValueError:
            vehicle_type = VehicleType.SEDAN  # Default
        
        # Get created_at timestamp
        created_at = None
        if booking_data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(booking_data["created_at"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = None
        
        # Get accepted_at timestamp (optional)
        accepted_at = None
        if booking_data.get("accepted_at"):
            try:
                accepted_at = datetime.fromisoformat(booking_data["accepted_at"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                accepted_at = None
        
        # Calculate cancellation fee using new formula
        cancellation_fee_before_gst, cancellation_fee_after_gst = fare_service.calculate_cancellation_fee(
            total_fare=total_fare,
            vehicle_type=vehicle_type,
            created_at=created_at,
            accepted_at=accepted_at
        )
        
        # Use the fee after GST (final amount to charge)
        cancellation_fee = cancellation_fee_after_gst
        
        # Update booking status
        update_data = {
            "status": BookingStatus.CANCELLED.value,
            "cancelled_by": "passenger",
            "cancelled_at": datetime.now().isoformat(),
            "cancellation_fee": cancellation_fee
        }
        
        success = firebase_service.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel booking")
        
        # If driver was assigned, make them available again
        if booking_data.get("driver_id"):
            driver_id = booking_data.get("driver_id")
            firebase_service.update_driver(driver_id, {"is_available": True})
        
        return {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_id": request.booking_id,
            "cancellation_fee": cancellation_fee,
            "cancellation_fee_before_gst": cancellation_fee_before_gst,
            "gst_amount": round(cancellation_fee - cancellation_fee_before_gst, 2),
            "status": "cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

