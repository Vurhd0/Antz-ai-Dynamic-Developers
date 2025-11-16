"""
In-memory storage service to replace Firebase
Stores all data in Python dictionaries/lists with hardcoded sample data
"""
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class MemoryStorage:
    """In-memory storage service for passengers, drivers, bookings, and locations"""
    
    def __init__(self):
        """Initialize in-memory storage with hardcoded sample data"""
        # Storage dictionaries
        self.passengers: Dict[str, dict] = {}
        self.drivers: Dict[str, dict] = {}
        self.bookings: Dict[str, dict] = {}
        self.locations: Dict[str, dict] = {}  # For driver/passenger locations
        
        # Initialize with hardcoded sample data
        self._initialize_hardcoded_data()
        print("="*60)
        print("✓ Memory Storage initialized with hardcoded sample data")
        print(f"✓ Loaded {len(self.passengers)} passengers")
        print(f"✓ Loaded {len(self.drivers)} drivers")
        print(f"✓ Loaded {len(self.bookings)} bookings")
        print("="*60)
    
    def _initialize_hardcoded_data(self):
        """Initialize with comprehensive sample data"""
        # Sample Passengers with locations
        self.passengers["passenger_001"] = {
            "user_id": "passenger_001",
            "phone_number": "+919876543210",
            "name": "Rahul Sharma",
            "vehicle_preference": "sedan",
            "current_location": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passengers["passenger_002"] = {
            "user_id": "passenger_002",
            "phone_number": "+919876543211",
            "name": "Priya Patel",
            "vehicle_preference": "suv",
            "current_location": {
                "latitude": 28.7041,
                "longitude": 77.1025,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passengers["passenger_003"] = {
            "user_id": "passenger_003",
            "phone_number": "+919876543212",
            "name": "Amit Kumar",
            "vehicle_preference": "hatchback",
            "current_location": {
                "latitude": 28.5355,
                "longitude": 77.3910,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passengers["passenger_004"] = {
            "user_id": "passenger_004",
            "phone_number": "+919876543213",
            "name": "Sneha Verma",
            "vehicle_preference": "premium",
            "current_location": {
                "latitude": 28.4595,
                "longitude": 77.0266,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passengers["passenger_005"] = {
            "user_id": "passenger_005",
            "phone_number": "+919876543214",
            "name": "Vikram Gupta",
            "vehicle_preference": "sedan",
            "current_location": {
                "latitude": 28.4089,
                "longitude": 77.0378,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passengers["passenger_006"] = {
            "user_id": "passenger_006",
            "phone_number": "+919876543215",
            "name": "Anjali Desai",
            "vehicle_preference": "suv",
            "current_location": {
                "latitude": 28.5500,
                "longitude": 77.2500,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Sample Drivers with locations and availability
        self.drivers["driver_001"] = {
            "driver_id": "driver_001",
            "name": "Rajesh Kumar",
            "phone_number": "+919123456789",
            "vehicle_type": "sedan",
            "vehicle_number": "DL-01-AB-1234",
            "is_online": True,
            "is_available": True,
            "current_location": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "timestamp": datetime.now().isoformat()
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        
        
        # Store driver locations
        for driver_id, driver in self.drivers.items():
            if driver.get("current_location"):
                self.locations[driver_id] = {
                    "driver_id": driver_id,
                    "location": driver["current_location"],
                    "is_available": driver.get("is_available", False),
                    "is_online": driver.get("is_online", False),
                    "updated_at": driver.get("updated_at")
                }
        
        # Store passenger locations
        for passenger_id, passenger in self.passengers.items():
            if passenger.get("current_location"):
                self.locations[passenger_id] = {
                    "user_id": passenger_id,
                    "location": passenger["current_location"],
                    "phone_number": passenger.get("phone_number"),
                    "name": passenger.get("name"),
                    "vehicle_preference": passenger.get("vehicle_preference")
                }
        
        # Update locations for new drivers
        for driver_id, driver in self.drivers.items():
            if driver_id not in self.locations and driver.get("current_location"):
                self.locations[driver_id] = {
                    "driver_id": driver_id,
                    "location": driver["current_location"],
                    "is_available": driver.get("is_available", False),
                    "is_online": driver.get("is_online", False),
                    "updated_at": driver.get("updated_at")
                }
        
        # Sample Bookings (some active, some completed)
        booking_1 = {
            "booking_id": "booking_001",
            "passenger_id": "passenger_001",
            "driver_id": "driver_001",
            "pickup_location": {
                "latitude": 28.6139,
                "longitude": 77.2090,
                "timestamp": datetime.now().isoformat()
            },
            "dropoff_location": {
                "latitude": 28.7041,
                "longitude": 77.1025,
                "timestamp": datetime.now().isoformat()
            },
            "vehicle_type": "sedan",
            "status": "confirmed",
            "fare": 150.50,
            "distance_km": 12.5,
            "estimated_time_minutes": 25.0,
            "surge_multiplier": 1.0,
            "driver_accepted": True,
            "passenger_confirmed": True,
            "created_at": datetime.now().isoformat(),
            "accepted_at": datetime.now().isoformat(),
            "confirmed_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None
        }
        
        booking_2 = {
            "booking_id": "booking_002",
            "passenger_id": "passenger_002",
            "driver_id": "driver_002",
            "pickup_location": {
                "latitude": 28.7041,
                "longitude": 77.1025,
                "timestamp": datetime.now().isoformat()
            },
            "dropoff_location": {
                "latitude": 28.5355,
                "longitude": 77.3910,
                "timestamp": datetime.now().isoformat()
            },
            "vehicle_type": "suv",
            "status": "in_progress",
            "fare": 220.75,
            "distance_km": 18.3,
            "estimated_time_minutes": 35.0,
            "surge_multiplier": 1.2,
            "driver_accepted": True,
            "passenger_confirmed": True,
            "created_at": datetime.now().isoformat(),
            "accepted_at": datetime.now().isoformat(),
            "confirmed_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.bookings["booking_001"] = booking_1
        self.bookings["booking_002"] = booking_2
    
    # Passenger methods
    def get_passenger(self, user_id: str) -> Optional[dict]:
        """Get passenger by user_id"""
        return self.passengers.get(user_id)
    
    def create_passenger(self, user_id: str, data: dict) -> bool:
        """Create passenger document"""
        self.passengers[user_id] = data
        # Also store location
        if data.get("current_location"):
            self.locations[user_id] = {
                "user_id": user_id,
                "location": data["current_location"],
                "phone_number": data.get("phone_number"),
                "name": data.get("name"),
                "vehicle_preference": data.get("vehicle_preference")
            }
        print(f"✓ Created passenger {user_id} in memory")
        return True
    
    def update_passenger(self, user_id: str, data: dict) -> bool:
        """Update passenger document"""
        if user_id in self.passengers:
            self.passengers[user_id].update(data)
            self.passengers[user_id]["updated_at"] = datetime.now().isoformat()
            # Update location if provided
            if "current_location" in data:
                if user_id in self.locations:
                    self.locations[user_id]["location"] = data["current_location"]
                else:
                    self.locations[user_id] = {
                        "user_id": user_id,
                        "location": data["current_location"],
                        "phone_number": self.passengers[user_id].get("phone_number"),
                        "name": self.passengers[user_id].get("name"),
                        "vehicle_preference": self.passengers[user_id].get("vehicle_preference")
                    }
            print(f"✓ Updated passenger {user_id} in memory")
            return True
        return False
    
    # Driver methods
    def get_driver(self, driver_id: str) -> Optional[dict]:
        """Get driver by driver_id"""
        return self.drivers.get(driver_id)
    
    def create_driver(self, driver_id: str, data: dict) -> bool:
        """Create driver document"""
        self.drivers[driver_id] = data
        # Also store location
        if data.get("current_location"):
            self.locations[driver_id] = {
                "driver_id": driver_id,
                "location": data["current_location"],
                "is_available": data.get("is_available", False),
                "is_online": data.get("is_online", False),
                "updated_at": data.get("updated_at")
            }
        print(f"✓ Created driver {driver_id} in memory")
        return True
    
    def update_driver(self, driver_id: str, data: dict) -> bool:
        """Update driver document"""
        if driver_id in self.drivers:
            self.drivers[driver_id].update(data)
            self.drivers[driver_id]["updated_at"] = datetime.now().isoformat()
            # Update location if provided
            if "current_location" in data and driver_id in self.locations:
                self.locations[driver_id]["location"] = data["current_location"]
            # Update availability in location
            if driver_id in self.locations:
                if "is_available" in data:
                    self.locations[driver_id]["is_available"] = data["is_available"]
                if "is_online" in data:
                    self.locations[driver_id]["is_online"] = data["is_online"]
            print(f"✓ Updated driver {driver_id} in memory")
            return True
        return False
    
    def get_available_drivers(self) -> List[dict]:
        """Get all available drivers"""
        return [
            driver for driver in self.drivers.values()
            if driver.get("is_available") and driver.get("is_online")
        ]
    
    # Booking methods
    def create_booking(self, booking_id: str, data: dict) -> bool:
        """Create booking document"""
        self.bookings[booking_id] = data
        print(f"✓ Created booking {booking_id} in memory")
        return True
    
    def get_booking(self, booking_id: str) -> Optional[dict]:
        """Get booking by booking_id"""
        return self.bookings.get(booking_id)
    
    def update_booking(self, booking_id: str, data: dict) -> bool:
        """Update booking document"""
        if booking_id in self.bookings:
            self.bookings[booking_id].update(data)
            print(f"✓ Updated booking {booking_id} in memory")
            return True
        return False
    
    def get_all_bookings(self, filters: Optional[List[tuple]] = None) -> List[dict]:
        """Get all bookings with optional filters"""
        bookings = list(self.bookings.values())
        
        if filters:
            for field, operator, value in filters:
                if operator == "==":
                    bookings = [b for b in bookings if b.get(field) == value]
                elif operator == "!=":
                    bookings = [b for b in bookings if b.get(field) != value]
        
        return bookings
    
    # Location methods
    def update_driver_location(self, driver_id: str, location_data: dict) -> bool:
        """Update driver location"""
        self.locations[driver_id] = location_data
        # Also update in driver document
        if driver_id in self.drivers:
            if "location" in location_data:
                self.drivers[driver_id]["current_location"] = location_data["location"]
        print(f"✓ Updated driver location {driver_id} in memory")
        return True
    
    def get_driver_location(self, driver_id: str) -> Optional[dict]:
        """Get driver location"""
        return self.locations.get(driver_id)
    
    def get_passenger_location(self, user_id: str) -> Optional[dict]:
        """Get passenger location"""
        return self.locations.get(user_id)
    
    def get_all_documents(self, collection: str, filters: Optional[List[tuple]] = None) -> List[dict]:
        """Get all documents from a collection"""
        if collection == "passengers":
            data = list(self.passengers.values())
        elif collection == "drivers":
            data = list(self.drivers.values())
        elif collection == "bookings":
            data = list(self.bookings.values())
        else:
            return []
        
        if filters:
            for field, operator, value in filters:
                if operator == "==":
                    data = [d for d in data if d.get(field) == value]
                elif operator == "!=":
                    data = [d for d in data if d.get(field) != value]
        
        return data
    
    def get_stats(self) -> dict:
        """Get storage statistics"""
        return {
            "passengers": len(self.passengers),
            "drivers": len(self.drivers),
            "bookings": len(self.bookings),
            "locations": len(self.locations),
            "available_drivers": len(self.get_available_drivers()),
            "online_drivers": len([d for d in self.drivers.values() if d.get("is_online")]),
            "active_bookings": len([b for b in self.bookings.values() if b.get("status") in ["pending", "driver_accepted", "confirmed", "in_progress"]])
        }

# Singleton instance
_memory_storage_instance = None

def get_memory_storage() -> MemoryStorage:
    """Get or create the singleton MemoryStorage instance"""
    global _memory_storage_instance
    if _memory_storage_instance is None:
        _memory_storage_instance = MemoryStorage()
    return _memory_storage_instance

