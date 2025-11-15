import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    
    # Google Maps API Configuration
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Application Configuration
    BASE_FARE = float(os.getenv("BASE_FARE", "50.0"))  # Base fare in currency units
    RATE_PER_KM = float(os.getenv("RATE_PER_KM", "10.0"))  # Rate per kilometer
    RATE_PER_MIN = float(os.getenv("RATE_PER_MIN", "2.0"))  # Rate per minute
    
    # Surge Pricing Configuration
    SURGE_MULTIPLIER_MILD_MIN = 1.2
    SURGE_MULTIPLIER_MILD_MAX = 1.4
    SURGE_MULTIPLIER_MEDIUM_MIN = 1.5
    SURGE_MULTIPLIER_MEDIUM_MAX = 1.8
    SURGE_MULTIPLIER_HIGH = 2.0
    SURGE_MULTIPLIER_MAX = 2.0  # Government limit
    
    # Location Update Interval (seconds)
    LOCATION_UPDATE_INTERVAL = int(os.getenv("LOCATION_UPDATE_INTERVAL", "5"))
    
    # Cancellation Fee Configuration
    # Base formula: Min(10% of Total Fare, ₹100)
    CANCELLATION_FARE_PERCENTAGE = 0.10  # 10% of total fare
    CANCELLATION_FARE_MAX = 100.0  # Maximum ₹100 for percentage-based calculation
    
    # Category-based cancellation fees (applied after time threshold)
    # Vehicle type mapping: HATCHBACK=UberGO, SEDAN=UberX, SUV=UberXL, PREMIUM=UberX
    CANCELLATION_FEE_HATCHBACK = 60.0  # ₹60 (after 5 min)
    CANCELLATION_FEE_SEDAN = 90.0  # ₹90 (after 5 min)
    CANCELLATION_FEE_SUV = 100.0  # ₹100 (after 5 min)
    CANCELLATION_FEE_PREMIUM = 90.0  # ₹90 (after 5 min)
    
    # Time thresholds (in minutes) after which category fee applies
    CANCELLATION_TIME_THRESHOLD_STANDARD = 5  # 5 minutes for most categories
    CANCELLATION_TIME_THRESHOLD_POOL = 2  # 2 minutes for pool/hatchback (if applicable)
    
    # GST Configuration
    GST_RATE = 0.06  # 6% GST
    
    # Database Collections
    COLLECTION_PASSENGERS = "passengers"
    COLLECTION_DRIVERS = "drivers"
    COLLECTION_BOOKINGS = "bookings"
    COLLECTION_LOCATIONS = "locations"

