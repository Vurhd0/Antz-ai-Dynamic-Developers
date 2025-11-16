from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from models.passenger import Passenger, PassengerLocation
from models.location import Location
from models.booking import Booking, BookingStatus, VehicleType
from services.memory_storage import get_memory_storage
from services.maps_service import MapsService
from services.fare_service import FareService
from config import Config

router = APIRouter(prefix="/passenger", tags=["Passenger"])

# Initialize services - use in-memory storage with hardcoded data
storage = get_memory_storage()
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
    latitude: float  # Pickup latitude
    longitude: float  # Pickup longitude
    destination_latitude: Optional[float] = None  # Destination latitude
    destination_longitude: Optional[float] = None  # Destination longitude
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
        
        # Store in memory
        success = storage.create_passenger(
            request.user_id,
            passenger.to_dict()
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create passenger")
        
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
        passenger_data = storage.get_passenger(user_id)
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
        
        # Update in memory
        success = storage.update_passenger(user_id, update_data)
        
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
        passenger_data = storage.get_passenger(request.user_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Update location in memory
        update_data = {
            "current_location": location.to_dict(),
            "updated_at": datetime.now().isoformat()
        }
        storage.update_passenger(request.user_id, update_data)
        
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
        
        # Get available drivers from memory
        available_drivers = storage.get_available_drivers()
        
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
        
        # Get driver locations from memory
        driver_locations = []
        for driver in available_drivers:
            driver_id = driver.get("driver_id")
            if not driver_id:
                continue
            
            # Get location from memory
            driver_location_data = storage.get_driver_location(driver_id)
            if driver_location_data and driver_location_data.get("location"):
                loc_data = driver_location_data["location"]
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
        
        # Calculate distances and ETAs from driver to pickup (for ETA only)
        driver_results = maps_service.get_nearby_drivers_with_eta(
            passenger_location,  # Pickup location
            driver_locations
        )
        
        # Calculate ride distance (pickup → destination) for fare calculation
        ride_distance_km = None
        ride_eta_minutes = None
        
        if request.destination_latitude and request.destination_longitude:
            destination_location = Location(
                latitude=request.destination_latitude,
                longitude=request.destination_longitude
            )
            
            # Calculate pickup → destination distance (the actual ride distance)
            ride_distance_eta = maps_service.get_distance_and_eta(
                passenger_location,  # Pickup
                destination_location  # Destination
            )
            
            if ride_distance_eta:
                ride_distance_km, ride_eta_minutes = ride_distance_eta
        
        # Get passenger and driver counts for surge calculation
        passenger_count = len(storage.get_all_documents("passengers"))
        driver_count = len(available_drivers)
        
        # Calculate fare for each driver based on ride distance (pickup → destination)
        # NOT driver → pickup distance!
        for result in driver_results:
            # Use ride distance for fare calculation (same for all drivers)
            # Driver → pickup distance is only for ETA display
            if ride_distance_km and ride_eta_minutes:
                # Calculate fare based on actual ride distance (pickup → destination)
                fare, surge_multiplier = fare_service.calculate_fare_with_surge(
                    ride_distance_km,  # Use ride distance, not driver-to-pickup distance
                    ride_eta_minutes,  # Use ride ETA, not driver-to-pickup ETA
                    passenger_count,
                    driver_count
                )
            else:
                # Fallback: if no destination provided, use driver-to-pickup distance
                # But this shouldn't happen in normal flow
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
            
            # Add ride distance info to result (for display)
            if ride_distance_km:
                result["ride_distance_km"] = ride_distance_km
                result["ride_eta_minutes"] = ride_eta_minutes
            
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
        passenger_data = storage.get_passenger(request.user_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Verify driver exists and is available
        driver_data = storage.get_driver(request.driver_id)
        if not driver_data:
            raise HTTPException(status_code=404, detail=f"Driver {request.driver_id} not found. Please select a valid driver.")
        
        is_available = driver_data.get("is_available", False)
        is_online = driver_data.get("is_online", False)
        
        if not is_available:
            raise HTTPException(status_code=400, detail=f"Driver {request.driver_id} is not available (currently on a ride). Please select another driver.")
        
        if not is_online:
            raise HTTPException(status_code=400, detail=f"Driver {request.driver_id} is offline. Please select an online driver.")
        
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
        driver_location_data = storage.get_driver_location(request.driver_id)
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
        
        # Calculate distance and ETA from driver to pickup (for ETA display only)
        driver_to_pickup_eta = maps_service.get_distance_and_eta(driver_loc, pickup_location)
        if not driver_to_pickup_eta:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to calculate distance from driver location ({driver_loc.latitude}, {driver_loc.longitude}) to pickup ({pickup_location.latitude}, {pickup_location.longitude})"
            )
        
        driver_to_pickup_distance, driver_to_pickup_eta_minutes = driver_to_pickup_eta
        
        # Calculate fare based on ACTUAL RIDE DISTANCE (pickup → destination)
        # NOT driver → pickup distance!
        if not dropoff_location:
            raise HTTPException(status_code=400, detail="Dropoff location is required to calculate fare")
        
        ride_distance_eta = maps_service.get_distance_and_eta(pickup_location, dropoff_location)
        if not ride_distance_eta:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate distance from pickup ({pickup_location.latitude}, {pickup_location.longitude}) to destination ({dropoff_location.latitude}, {dropoff_location.longitude})"
            )
        
        ride_distance_km, ride_eta_minutes = ride_distance_eta
        
        # Calculate fare based on actual ride distance (pickup → destination)
        passenger_count = len(storage.get_all_documents("passengers"))
        driver_count = len(storage.get_available_drivers())
        
        fare, surge_multiplier = fare_service.calculate_fare_with_surge(
            ride_distance_km,  # Use ride distance, not driver-to-pickup distance
            ride_eta_minutes,   # Use ride ETA, not driver-to-pickup ETA
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
            distance_km=ride_distance_km,  # Store actual ride distance (pickup → destination)
            estimated_time_minutes=ride_eta_minutes,  # Store actual ride ETA
            surge_multiplier=surge_multiplier
        )
        
        # Store booking in memory
        success = storage.create_booking(booking_id, booking.to_dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create booking in storage")
        
        return {
            "success": True,
            "message": "Booking created successfully",
            "booking_id": booking_id,
            "booking": booking.to_dict()
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions with their details
        raise he
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in book_taxi: {error_details}")
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


@router.get("/booking/{booking_id}")
async def get_booking(booking_id: str):
    """
    Get booking details
    Calculates distance if missing based on pickup/dropoff locations
    """
    try:
        booking_data = storage.get_booking(booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Calculate distance if missing
        if not booking_data.get("distance_km") or booking_data.get("distance_km") == 0:
            pickup_data = booking_data.get("pickup_location")
            dropoff_data = booking_data.get("dropoff_location")
            
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
                        booking_data["distance_km"] = distance_eta[0]
                        booking_data["estimated_time_minutes"] = distance_eta[1]
                        # Update in storage
                        storage.update_booking(booking_id, {
                            "distance_km": distance_eta[0],
                            "estimated_time_minutes": distance_eta[1]
                        })
                except Exception as e:
                    print(f"Error calculating distance for booking {booking_id}: {e}")
        
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
        booking_data = storage.get_booking(request.booking_id)
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
        
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to confirm booking")
        
        # Get driver details for passenger
        driver_id = booking_data.get("driver_id")
        driver_data = None
        if driver_id:
            driver_data = storage.get_driver(driver_id)
        
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
        booking_data = storage.get_booking(request.booking_id)
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
            # If fare not set, use a default minimum from Config
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
        
        success = storage.update_booking(request.booking_id, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel booking")
        
        # If driver was assigned, make them available again
        if booking_data.get("driver_id"):
            driver_id = booking_data.get("driver_id")
            storage.update_driver(driver_id, {"is_available": True})
        
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

