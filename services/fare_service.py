from typing import Optional, Tuple
from datetime import datetime
from config import Config
from models.location import Location
from models.booking import VehicleType

class FareService:
    """Service class for fare calculation with surge pricing"""
    
    def __init__(self):
        """Initialize fare service with configuration"""
        self.base_fare = Config.BASE_FARE
        self.rate_per_km = Config.RATE_PER_KM
        self.rate_per_min = Config.RATE_PER_MIN
    
    def calculate_surge_multiplier(self, passenger_count: int, driver_count: int) -> float:
        """
        Calculate surge multiplier based on passenger-to-driver ratio
        Returns surge multiplier (1.0 to 2.0)
        """
        if driver_count == 0:
            return Config.SURGE_MULTIPLIER_MAX
        
        ratio = passenger_count / driver_count
        
        if ratio < 1.0:
            return 1.0  # No surge
        elif ratio < 1.5:
            # Mild surge: 1.2x to 1.4x
            # Linear interpolation between 1.2 and 1.4
            surge = Config.SURGE_MULTIPLIER_MILD_MIN + (
                (ratio - 1.0) / 0.5
            ) * (Config.SURGE_MULTIPLIER_MILD_MAX - Config.SURGE_MULTIPLIER_MILD_MIN)
            return round(surge, 2)
        elif ratio < 1.8:
            # Medium surge: 1.5x to 1.8x
            # Linear interpolation between 1.5 and 1.8
            surge = Config.SURGE_MULTIPLIER_MEDIUM_MIN + (
                (ratio - 1.5) / 0.3
            ) * (Config.SURGE_MULTIPLIER_MEDIUM_MAX - Config.SURGE_MULTIPLIER_MEDIUM_MIN)
            return round(surge, 2)
        else:
            # High surge: 2.0x (max allowed)
            return Config.SURGE_MULTIPLIER_HIGH
    
    def calculate_fare(
        self,
        distance_km: float,
        duration_minutes: float,
        surge_multiplier: float = 1.0
    ) -> float:
        """
        Calculate fare using the formula:
        Fare = (Base Fare + (km × Rate) + (min × Rate)) × Surge Multiplier
        
        Args:
            distance_km: Distance in kilometers
            duration_minutes: Duration in minutes
            surge_multiplier: Surge pricing multiplier (default 1.0)
        
        Returns:
            Calculated fare amount
        """
        base = self.base_fare
        distance_cost = distance_km * self.rate_per_km
        time_cost = duration_minutes * self.rate_per_min
        
        base_fare = base + distance_cost + time_cost
        final_fare = base_fare * surge_multiplier
        
        return round(final_fare, 2)
    
    def calculate_fare_with_surge(
        self,
        distance_km: float,
        duration_minutes: float,
        passenger_count: int,
        driver_count: int
    ) -> Tuple[float, float]:
        """
        Calculate fare with automatic surge pricing
        Returns (fare, surge_multiplier)
        """
        surge_multiplier = self.calculate_surge_multiplier(passenger_count, driver_count)
        fare = self.calculate_fare(distance_km, duration_minutes, surge_multiplier)
        return (fare, surge_multiplier)
    
    def calculate_cancellation_fee(
        self,
        total_fare: float,
        vehicle_type: VehicleType,
        created_at: Optional[datetime] = None,
        accepted_at: Optional[datetime] = None
    ) -> Tuple[float, float]:
        """
        Calculate cancellation fee based on:
        1. Base formula: Min(10% of Total Fare, ₹100)
        2. Category-based fee (if booking is after time threshold)
        3. GST (6%)
        
        Args:
            total_fare: Total fare of the booking
            vehicle_type: Type of vehicle (HATCHBACK, SEDAN, SUV, PREMIUM)
            created_at: When the booking was created
            accepted_at: When the booking was accepted (None if not accepted yet)
        
        Returns:
            Tuple of (cancellation_fee_before_gst, cancellation_fee_after_gst)
        """
        # Calculate time elapsed since booking creation
        time_elapsed_minutes = 0.0
        if created_at:
            time_elapsed_minutes = (datetime.now() - created_at).total_seconds() / 60.0
        
        # Determine time threshold based on vehicle type
        time_threshold = Config.CANCELLATION_TIME_THRESHOLD_STANDARD
        if vehicle_type == VehicleType.HATCHBACK:
            time_threshold = Config.CANCELLATION_TIME_THRESHOLD_STANDARD  # 5 minutes
        
        # Check if time threshold has passed
        time_threshold_passed = time_elapsed_minutes >= time_threshold
        
        # Calculate base cancellation fee: Min(10% of Total Fare, ₹100)
        base_fee = min(total_fare * Config.CANCELLATION_FARE_PERCENTAGE, Config.CANCELLATION_FARE_MAX)
        
        # Get category-based fee
        category_fee = 0.0
        if vehicle_type == VehicleType.HATCHBACK:
            category_fee = Config.CANCELLATION_FEE_HATCHBACK
        elif vehicle_type == VehicleType.SEDAN:
            category_fee = Config.CANCELLATION_FEE_SEDAN
        elif vehicle_type == VehicleType.SUV:
            category_fee = Config.CANCELLATION_FEE_SUV
        elif vehicle_type == VehicleType.PREMIUM:
            category_fee = Config.CANCELLATION_FEE_PREMIUM
        
        # Apply category fee if time threshold has passed, otherwise use base fee
        if time_threshold_passed:
            # Use the higher of base fee or category fee
            cancellation_fee_before_gst = max(base_fee, category_fee)
        else:
            # Before time threshold, use base fee only
            cancellation_fee_before_gst = base_fee
        
        # Add GST (6%)
        gst_amount = cancellation_fee_before_gst * Config.GST_RATE
        cancellation_fee_after_gst = cancellation_fee_before_gst + gst_amount
        
        return (round(cancellation_fee_before_gst, 2), round(cancellation_fee_after_gst, 2))
    
    def _calculate_haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate approximate distance between two locations using Haversine formula
        Returns distance in kilometers
        """
        import math
        
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

