import math
import httpx
from typing import List, Dict, Optional, Tuple
from config import Config
from models.location import Location

class MapsService:
    """Service class for distance and ETA calculations using OpenRouteService API with Haversine fallback"""
    
    def __init__(self):
        """Initialize Maps Service"""
        # Average driving speed in km/h (for ETA calculation fallback)
        self.avg_speed_kmh = 40.0 # 40 km/h average city speed
        
        # OpenRouteService API configuration (primary)
        self.ors_api_key = Config.OPENROUTESERVICE_API_KEY
        self.use_ors = bool(self.ors_api_key and self.ors_api_key.strip())
        
        # Google Maps API configuration (legacy fallback)
        self.google_api_key = Config.GOOGLE_MAPS_API_KEY
        self.use_google_maps = bool(self.google_api_key and self.google_api_key.strip())
        
        # OpenRouteService API endpoints
        if self.use_ors:
            self.ors_base_url = "https://api.openrouteservice.org/v2"
            self.ors_matrix_url = f"{self.ors_base_url}/matrix/driving-car"
            self.ors_directions_url = f"{self.ors_base_url}/directions/driving-car"
            print("✓ Maps Service initialized (using OpenRouteService API)")
        elif self.use_google_maps:
            self.google_base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            print("✓ Maps Service initialized (using Google Maps API as fallback)")
        else:
            print("⚠ Maps Service initialized (using Haversine formula - no API key configured)")
            print("  To use accurate road distances, set OPENROUTESERVICE_API_KEY in .env file")
    
    def _calculate_haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate distance between two locations using Haversine formula (fallback)
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
    
    def _calculate_eta_minutes(self, distance_km: float, duration_seconds: Optional[float] = None) -> float:
        """
        Calculate estimated time of arrival in minutes
        If duration_seconds is provided (from Google Maps/ORS), use it directly
        Otherwise, estimate based on average driving speed
        """
        if duration_seconds is not None:
            # Convert seconds to minutes
            return round(duration_seconds / 60.0, 2)
        
        # Fallback: ETA = distance / speed (in hours) * 60 (to minutes)
        # Add some buffer for traffic (multiply by 1.3)
        eta_hours = (distance_km / self.avg_speed_kmh) * 1.3
        eta_minutes = eta_hours * 60.0
        return round(eta_minutes, 2)
    
    def _get_ors_distance(
        self, 
        origin: Location, 
        destination: Location
    ) -> Optional[Tuple[float, float]]:
        """
        Get distance and duration from OpenRouteService Matrix API
        Returns (distance_km, duration_seconds) or None if API call fails
        """
        if not self.use_ors:
            return None
        
        try:
            # OpenRouteService Matrix API expects POST with JSON body
            locations = [
                [origin.longitude, origin.latitude], # ORS uses [lon, lat] format
                [destination.longitude, destination.latitude]
            ]
            
            payload = {
                "locations": locations,
                "metrics": ["distance", "duration"]
            }
            
            headers = {
                # FIX APPLIED HERE: Must use Bearer scheme for Authorization header with ORS API key
                "Authorization": f"Bearer {self.ors_api_key}", 
                "Content-Type": "application/json"
            }
            
            response = httpx.post(
                self.ors_matrix_url,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Check for errors in response
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"⚠ OpenRouteService API error: {error_msg}")
                return None
            
            # Extract distance and duration
            distances = data.get("distances", [])
            durations = data.get("durations", [])
            
            if not distances or not durations:
                return None
            
            # Matrix returns 2x2 array, we want [0][1] (origin to destination)
            distance_m = distances[0][1] if len(distances) > 0 and len(distances[0]) > 1 else 0
            duration_seconds = durations[0][1] if len(durations) > 0 and len(durations[0]) > 1 else 0
            
            if distance_m == 0 or duration_seconds == 0:
                return None
            
            distance_km = distance_m / 1000.0
            
            return (round(distance_km, 2), duration_seconds)
            
        except httpx.RequestError as e:
            print(f"⚠ OpenRouteService API request error: {str(e)}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"⚠ OpenRouteService API HTTP error: {e.response.status_code}")
            if e.response.status_code == 401:
                print("  Check your OPENROUTESERVICE_API_KEY and ensure it supports Bearer token authentication")
            return None
        except Exception as e:
            print(f"⚠ OpenRouteService API error: {str(e)}")
            return None
    
    def _get_google_maps_distance(
        self, 
        origin: Location, 
        destination: Location
    ) -> Optional[Tuple[float, float]]:
        """
        Get distance and duration from Google Maps Distance Matrix API (legacy fallback)
        Returns (distance_km, duration_seconds) or None if API call fails
        """
        if not self.use_google_maps:
            return None
        
        try:
            # Format locations for API
            origins = f"{origin.latitude},{origin.longitude}"
            destinations = f"{destination.latitude},{destination.longitude}"
            
            # Make API request
            params = {
                "origins": origins,
                "destinations": destinations,
                "key": self.google_api_key,
                "units": "metric" # Get distance in kilometers
            }
            
            response = httpx.get(self.google_base_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Check API response status
            if data.get("status") != "OK":
                error_msg = data.get("error_message", f"API returned status: {data.get('status')}")
                print(f"⚠ Google Maps API error: {error_msg}")
                return None
            
            # Extract distance and duration from response
            rows = data.get("rows", [])
            if not rows:
                return None
            
            elements = rows[0].get("elements", [])
            if not elements:
                return None
            
            element = elements[0]
            if element.get("status") != "OK":
                print(f"⚠ Google Maps API: Route status is {element.get('status')}")
                return None
            
            # Get distance in meters, convert to kilometers
            distance_m = element.get("distance", {}).get("value", 0)
            distance_km = distance_m / 1000.0
            
            # Get duration in seconds
            duration_seconds = element.get("duration", {}).get("value", 0)
            
            return (round(distance_km, 2), duration_seconds)
            
        except httpx.RequestError as e:
            print(f"⚠ Google Maps API request error: {str(e)}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"⚠ Google Maps API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"⚠ Google Maps API error: {str(e)}")
            return None
    
    def get_distance_and_eta(
        self, 
        origin: Location, 
        destination: Location
    ) -> Optional[Tuple[float, float]]:
        """
        Get distance (km) and ETA (minutes) between two locations
        Uses OpenRouteService API if available, falls back to Google Maps, then Haversine
        Returns (distance_km, eta_minutes) or None
        """
        try:
            # Try OpenRouteService API first (primary)
            if self.use_ors:
                result = self._get_ors_distance(origin, destination)
                if result:
                    distance_km, duration_seconds = result
                    eta_minutes = self._calculate_eta_minutes(distance_km, duration_seconds)
                    return (distance_km, eta_minutes)
                else:
                    print(f"⚠ OpenRouteService API failed, trying fallback")
            
            # Try Google Maps API as fallback
            if self.use_google_maps:
                result = self._get_google_maps_distance(origin, destination)
                if result:
                    distance_km, duration_seconds = result
                    eta_minutes = self._calculate_eta_minutes(distance_km, duration_seconds)
                    return (distance_km, eta_minutes)
                else:
                    print(f"⚠ Google Maps API failed, using Haversine fallback")
            
            # Fallback to Haversine formula
            distance_km = self._calculate_haversine_distance(origin, destination)
            eta_minutes = self._calculate_eta_minutes(distance_km)
            return (round(distance_km, 2), eta_minutes)
            
        except Exception as e:
            print(f"Error calculating distance and ETA: {str(e)}")
            return None
    
    def get_distance_matrix_ors(
        self,
        origins: List[Location],
        destinations: List[Location]
    ) -> Optional[List[Dict]]:
        """
        Get distance matrix from OpenRouteService API for multiple origin-destination pairs
        Returns list of results with distance and duration
        """
        if not self.use_ors:
            return None
        
        try:
            # OpenRouteService Matrix API expects all locations in one array
            # Format: [[lon, lat], [lon, lat], ...]
            all_locations = []
            
            # Add origins
            for origin in origins:
                all_locations.append([origin.longitude, origin.latitude])
            
            # Add destinations
            for destination in destinations:
                all_locations.append([destination.longitude, destination.latitude])
            
            payload = {
                "locations": all_locations,
                "metrics": ["distance", "duration"],
                "sources": list(range(len(origins))),  # First N locations are sources
                "destinations": list(range(len(origins), len(all_locations)))  # Rest are destinations
            }
            
            headers = {
                # FIX APPLIED HERE: Must use Bearer scheme for Authorization header with ORS API key
                "Authorization": f"Bearer {self.ors_api_key}", 
                "Content-Type": "application/json"
            }
            
            response = httpx.post(
                self.ors_matrix_url,
                json=payload,
                headers=headers,
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"⚠ OpenRouteService API error: {error_msg}")
                return None
            
            distances = data.get("distances", [])
            durations = data.get("durations", [])
            
            if not distances or not durations:
                return None
            
            results = []
            # Process matrix results
            for i, origin in enumerate(origins):
                for j, destination in enumerate(destinations):
                    # Destination index in the matrix response is offset by the number of origins
                    dest_idx_in_matrix = j + len(origins) 
                    
                    if i < len(distances) and dest_idx_in_matrix < len(distances[i]):
                        distance_m = distances[i][dest_idx_in_matrix]
                        duration_seconds = durations[i][dest_idx_in_matrix]
                        
                        if distance_m is not None and duration_seconds is not None:
                            distance_km = distance_m / 1000.0
                            duration_minutes = duration_seconds / 60.0
                            
                            results.append({
                                "origin_index": i,
                                "destination_index": j,
                                "distance_km": round(distance_km, 2),
                                "duration_minutes": round(duration_minutes, 2),
                                "distance_text": f"{distance_km:.2f} km",
                                "duration_text": f"{duration_minutes:.0f} min"
                            })
            
            return results
            
        except Exception as e:
            print(f"⚠ OpenRouteService Matrix API error: {str(e)}")
            return None
    
    def get_distance_matrix_google_maps(
        self,
        origins: List[Location],
        destinations: List[Location]
    ) -> Optional[List[Dict]]:
        """
        Get distance matrix from Google Maps API for multiple origin-destination pairs (legacy fallback)
        Returns list of results with distance and duration
        """
        if not self.use_google_maps:
            return None
        
        try:
            # Format origins and destinations
            origins_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in origins])
            destinations_str = "|".join([f"{loc.latitude},{loc.longitude}" for loc in destinations])
            
            params = {
                "origins": origins_str,
                "destinations": destinations_str,
                "key": self.google_api_key,
                "units": "metric"
            }
            
            response = httpx.get(self.google_base_url, params=params, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                error_msg = data.get("error_message", f"API returned status: {data.get('status')}")
                print(f"⚠ Google Maps API error: {error_msg}")
                return None
            
            results = []
            rows = data.get("rows", [])
            
            for i, row in enumerate(rows):
                elements = row.get("elements", [])
                for j, element in enumerate(elements):
                    if element.get("status") == "OK":
                        distance_m = element.get("distance", {}).get("value", 0)
                        distance_km = distance_m / 1000.0
                        duration_seconds = element.get("duration", {}).get("value", 0)
                        duration_minutes = duration_seconds / 60.0
                        
                        results.append({
                            "origin_index": i,
                            "destination_index": j,
                            "distance_km": round(distance_km, 2),
                            "duration_minutes": round(duration_minutes, 2),
                            "distance_text": f"{distance_km:.2f} km",
                            "duration_text": f"{duration_minutes:.0f} min"
                        })
            
            return results
            
        except Exception as e:
            print(f"⚠ Google Maps Distance Matrix API error: {str(e)}")
            return None
    
    def calculate_distance_matrix(
        self, 
        origins: List[Location], 
        destinations: List[Location]
    ) -> Optional[List[Dict]]:
        """
        Calculate distance matrix using OpenRouteService API if available, falls back to Google Maps, then Haversine
        Returns list of results with distance and duration for each origin-destination pair
        """
        # Try OpenRouteService API first (primary)
        if self.use_ors:
            result = self.get_distance_matrix_ors(origins, destinations)
            if result:
                return result
            print("⚠ OpenRouteService API failed, trying Google Maps fallback")
        
        # Try Google Maps API as fallback
        if self.use_google_maps:
            result = self.get_distance_matrix_google_maps(origins, destinations)
            if result:
                return result
            print("⚠ Google Maps API failed, using Haversine fallback for distance matrix")
        
        # Fallback to Haversine formula
        try:
            results = []
            for i, origin in enumerate(origins):
                for j, destination in enumerate(destinations):
                    distance_km = self._calculate_haversine_distance(origin, destination)
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
    
    def get_nearby_drivers_with_eta(
        self,
        passenger_location: Location,
        driver_locations: List[Tuple[str, Location]]
    ) -> List[Dict]:
        """
        Get nearby drivers with ETA sorted by lowest ETA
        Uses Maps API if available for accurate road distances
        Returns list of dicts with driver_id, location, distance_km, eta_minutes
        """
        if not driver_locations:
            return []
        
        driver_results = []
        
        # If Maps API is available, use batch API call for better performance
        if (self.use_ors or self.use_google_maps) and len(driver_locations) > 0:
            try:
                # Prepare origins (all driver locations) and destinations (passenger location)
                origins = [loc for _, loc in driver_locations]
                destinations = [passenger_location]
                
                # Get distance matrix from API (prefers OpenRouteService)
                # Note: Swapping origin/destination here to efficiently calculate Driver -> Passenger ETA
                matrix_results = self.calculate_distance_matrix(origins, destinations)
                
                if matrix_results:
                    # Map results back to drivers
                    for idx, (driver_id, _) in enumerate(driver_locations):
                        # Find result for this driver (origin_index=idx, destination_index=0)
                        result = next(
                            (r for r in matrix_results if r["origin_index"] == idx and r["destination_index"] == 0),
                            None
                        )
                        
                        if result:
                            driver_results.append({
                                "driver_id": driver_id,
                                "distance_km": result["distance_km"],
                                "eta_minutes": result["duration_minutes"],
                                "distance_text": result["distance_text"],
                                "eta_text": result["duration_text"]
                            })
                        else:
                            # Fallback for this driver if not in results
                            driver_location = origins[idx]
                            distance_eta = self.get_distance_and_eta(driver_location, passenger_location)
                            if distance_eta:
                                distance_km, eta_minutes = distance_eta
                                driver_results.append({
                                    "driver_id": driver_id,
                                    "distance_km": distance_km,
                                    "eta_minutes": eta_minutes,
                                    "distance_text": f"{distance_km:.2f} km",
                                    "eta_text": f"{eta_minutes:.0f} min"
                                })
                    
                    # Sort by ETA (lowest first)
                    driver_results.sort(key=lambda x: x["eta_minutes"])
                    return driver_results
                    
            except Exception as e:
                print(f"⚠ Batch Maps API call failed: {str(e)}, falling back to individual calls")
        
        # Fallback: Calculate individually (works with or without API keys)
        for driver_id, driver_location in driver_locations:
            try:
                # Calculate Driver -> Passenger ETA
                distance_eta = self.get_distance_and_eta(driver_location, passenger_location)
                if distance_eta:
                    distance_km, eta_minutes = distance_eta
                    
                    driver_results.append({
                        "driver_id": driver_id,
                        "distance_km": distance_km,
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