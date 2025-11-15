import googlemaps
from typing import List, Dict, Optional, Tuple
from config import Config
from models.location import Location

class MapsService:
    """Service class for Google Maps API operations"""
    
    def __init__(self):
        """Initialize Google Maps client"""
        if Config.GOOGLE_MAPS_API_KEY:
            self.gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)
        else:
            self.gmaps = None
            print("Warning: Google Maps API key not configured.")
    
    def calculate_distance_matrix(
        self, 
        origins: List[Location], 
        destinations: List[Location]
    ) -> Optional[List[Dict]]:
        """
        Calculate distance matrix using Google Distance Matrix API
        Returns list of results with distance and duration for each origin-destination pair
        """
        if not self.gmaps:
            return None
        
        try:
            # Convert Location objects to string format
            origin_strs = [f"{loc.latitude},{loc.longitude}" for loc in origins]
            dest_strs = [f"{loc.latitude},{loc.longitude}" for loc in destinations]
            
            # Call Distance Matrix API
            result = self.gmaps.distance_matrix(
                origins=origin_strs,
                destinations=dest_strs,
                mode="driving",
                units="metric"
            )
            
            if result and "rows" in result:
                results = []
                for i, row in enumerate(result["rows"]):
                    for j, element in enumerate(row["elements"]):
                        if element["status"] == "OK":
                            distance_km = element["distance"]["value"] / 1000.0  # Convert meters to km
                            duration_minutes = element["duration"]["value"] / 60.0  # Convert seconds to minutes
                            
                            results.append({
                                "origin_index": i,
                                "destination_index": j,
                                "distance_km": distance_km,
                                "duration_minutes": duration_minutes,
                                "distance_text": element["distance"]["text"],
                                "duration_text": element["duration"]["text"]
                            })
                return results
            return None
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
        results = self.calculate_distance_matrix([origin], [destination])
        if results and len(results) > 0:
            return (results[0]["distance_km"], results[0]["duration_minutes"])
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
        
        # Prepare origins (passenger) and destinations (drivers)
        origins = [passenger_location]
        destinations = [loc for _, loc in driver_locations]
        
        # Calculate distance matrix
        results = self.calculate_distance_matrix(origins, destinations)
        
        if not results:
            return []
        
        # Map results to drivers
        driver_results = []
        for result in results:
            dest_index = result["destination_index"]
            if dest_index < len(driver_locations):
                driver_id, _ = driver_locations[dest_index]
                driver_results.append({
                    "driver_id": driver_id,
                    "distance_km": result["distance_km"],
                    "eta_minutes": result["duration_minutes"],
                    "distance_text": result["distance_text"],
                    "eta_text": result["duration_text"]
                })
        
        # Sort by ETA (lowest first)
        driver_results.sort(key=lambda x: x["eta_minutes"])
        
        return driver_results

