import math
from typing import List, Dict, Optional, Tuple
from config import Config
from models.location import Location

class MapsService:
    """Service class for distance and ETA calculations using Haversine formula"""
    
    def __init__(self):
        """Initialize Maps Service"""
        # Average driving speed in km/h (for ETA calculation)
        self.avg_speed_kmh = 40.0  # 40 km/h average city speed
        print("✓ Maps Service initialized (using Haversine distance calculation)")
    
    def _calculate_haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate distance between two locations using Haversine formula
        Returns distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(loc1.latitude)
        lon1_rad = math.radians(loc1.longitude)
        lat2_rad = math.radians(loc2.latitude)
        lon2_rad = math.radians(loc2.longitude)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def _calculate_eta_minutes(self, distance_km: float) -> float:
        """
        Calculate estimated time of arrival in minutes
        Based on average driving speed
        """
        # ETA = distance / speed (in hours) * 60 (to minutes)
        # Add some buffer for traffic (multiply by 1.3)
        eta_hours = (distance_km / self.avg_speed_kmh) * 1.3
        eta_minutes = eta_hours * 60.0
        return round(eta_minutes, 2)
    
    def calculate_distance_matrix(
        self, 
        origins: List[Location], 
        destinations: List[Location]
    ) -> Optional[List[Dict]]:
        """
        Calculate distance matrix using Haversine formula
        Returns list of results with distance and duration for each origin-destination pair
        """
        try:
            results = []
            for i, origin in enumerate(origins):
                for j, destination in enumerate(destinations):
                    # Calculate distance using Haversine formula
                    distance_km = self._calculate_haversine_distance(origin, destination)
                    # Calculate ETA based on distance
                    duration_minutes = self._calculate_eta_minutes(distance_km)
                    
                    results.append({
                        "origin_index": i,
                        "destination_index": j,
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": duration_minutes,
                        "distance_text": f"{distance_km:.2f} km",
                        "duration_text": f"{duration_minutes:.0f} min"
                    })
            return results
        except Exception as e:
            print(f"Error calculating distance matrix: {str(e)}")
            return None
    
    def get_distance_and_eta(
        self, 
        origin: Location, 
        destination: Location
    ) -> Optional[Tuple[float, float]]:
        """
        Get distance (km) and ETA (minutes) between two locations
        Returns (distance_km, eta_minutes) or None
        """
        try:
            distance_km = self._calculate_haversine_distance(origin, destination)
            eta_minutes = self._calculate_eta_minutes(distance_km)
            return (round(distance_km, 2), eta_minutes)
        except Exception as e:
            print(f"Error calculating distance and ETA: {str(e)}")
            return None
    
    def get_nearby_drivers_with_eta(
        self,
        passenger_location: Location,
        driver_locations: List[Tuple[str, Location]]
    ) -> List[Dict]:
        """
        Get nearby drivers with ETA sorted by lowest ETA
        Returns list of dicts with driver_id, location, distance_km, eta_minutes
        """
        if not driver_locations:
            return []
        
        driver_results = []
        
        # Calculate distance and ETA for each driver
        for driver_id, driver_location in driver_locations:
            try:
                distance_km = self._calculate_haversine_distance(passenger_location, driver_location)
                eta_minutes = self._calculate_eta_minutes(distance_km)
                
                driver_results.append({
                    "driver_id": driver_id,
                    "distance_km": round(distance_km, 2),
                    "eta_minutes": eta_minutes,
                    "distance_text": f"{distance_km:.2f} km",
                    "eta_text": f"{eta_minutes:.0f} min"
                })
            except Exception as e:
                print(f"Error calculating distance for driver {driver_id}: {str(e)}")
                continue
        
        # Sort by ETA (lowest first)
        driver_results.sort(key=lambda x: x["eta_minutes"])
        
        return driver_results

