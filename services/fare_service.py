from typing import Optional, Tuple
from datetime import datetime
from models.location import Location
from models.booking import VehicleType
import math

class FareService:
    def __init__(self):
        # Hardcoded values
        self.base_fare = 50
        self.rate_per_km = 10
        self.rate_per_min = 2

        # Surge settings
        self.SURGE_MILD_MIN = 1.2
        self.SURGE_MILD_MAX = 1.4
        self.SURGE_MED_MIN = 1.5
        self.SURGE_MED_MAX = 1.8
        self.SURGE_HIGH = 2.0

        # Cancellation rules
        self.GST_RATE = 0.06
        self.CANCEL_PERCENT = 0.10
        self.CANCEL_MAX = 100

        self.FEE_HATCHBACK = 30
        self.FEE_SEDAN = 40
        self.FEE_SUV = 50
        self.FEE_PREMIUM = 70

        self.CANCEL_TIME_LIMIT = 5  # minutes

    def calculate_surge_multiplier(self, passengers: int, drivers: int) -> float:
        if drivers == 0:
            return self.SURGE_HIGH

        ratio = passengers / drivers

        if ratio < 1.0:
            return 1.0

        elif ratio < 1.5:
            return round(
                self.SURGE_MILD_MIN +
                ((ratio - 1.0) / 0.5) * (self.SURGE_MILD_MAX - self.SURGE_MILD_MIN),
                2
            )

        elif ratio < 1.8:
            return round(
                self.SURGE_MED_MIN +
                ((ratio - 1.5) / 0.3) * (self.SURGE_MED_MAX - self.SURGE_MED_MIN),
                2
            )

        return self.SURGE_HIGH

    def calculate_fare(self, distance_km: float, duration_min: float, surge: float = 1.0) -> float:
        amount = self.base_fare + (distance_km * self.rate_per_km) + (duration_min * self.rate_per_min)
        return round(amount * surge, 2)

    def calculate_fare_with_surge(self, distance, duration, passengers, drivers):
        surge = self.calculate_surge_multiplier(passengers, drivers)
        fare = self.calculate_fare(distance, duration, surge)
        return fare, surge

    def calculate_cancellation_fee(self, total_fare, vehicle_type, created_at=None, accepted_at=None):
        time_elapsed = 0
        if created_at:
            time_elapsed = (datetime.now() - created_at).total_seconds() / 60

        base_fee = min(total_fare * self.CANCEL_PERCENT, self.CANCEL_MAX)

        if vehicle_type == VehicleType.HATCHBACK:
            category_fee = self.FEE_HATCHBACK
        elif vehicle_type == VehicleType.SEDAN:
            category_fee = self.FEE_SEDAN
        elif vehicle_type == VehicleType.SUV:
            category_fee = self.FEE_SUV
        else:
            category_fee = self.FEE_PREMIUM

        if time_elapsed >= self.CANCEL_TIME_LIMIT:
            final_before_gst = max(base_fee, category_fee)
        else:
            final_before_gst = base_fee

        final_after_gst = final_before_gst * (1 + self.GST_RATE)

        return round(final_before_gst, 2), round(final_after_gst, 2)

    def haversine_distance(self, loc1: Location, loc2: Location) -> float:
        R = 6371
        lat1, lon1 = math.radians(loc1.latitude), math.radians(loc1.longitude)
        lat2, lon2 = math.radians(loc2.latitude), math.radians(loc2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
