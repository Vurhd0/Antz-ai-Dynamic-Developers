# RealTaxi Backend API

Backend API for RealTaxi - A Taxi Booking Application built with FastAPI, Firebase, and Google Maps API.

## Tech Stack

- **Framework**: FastAPI
- **Database**: Firebase Firestore
- **Cache**: Upstash Redis
- **Maps API**: Google Maps API
- **Language**: Python 3.8+

## Features

### Passenger Workflow
- Register passenger with location
- Update passenger details and location
- Request nearby available taxis with ETA and fare estimates
- Book a taxi with a specific driver
- View booking details

### Driver Workflow
- Register driver
- Go online/offline (set availability)
- Update location in real-time (every 3-5 seconds)
- Accept bookings
- Start and complete rides
- View booking history

### Additional Features
- Real-time location tracking
- Dynamic fare calculation with surge pricing
- Distance and ETA calculation using Google Maps API
- Caching for improved performance

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd antzai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your configuration:
- Firebase credentials path and project ID
- Upstash Redis URL and token
- Google Maps API key
- Fare configuration (optional)

4. Set up Firebase:
   - Download your Firebase service account credentials JSON file
   - Place it in the project root as `firebase-credentials.json` (or update the path in `.env`)

## Running the Application

```bash
# Development server
uvicorn main:app --reload

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

## API Endpoints

### Passenger Endpoints

- `POST /passenger/register` - Register a new passenger
- `PUT /passenger/update` - Update passenger details
- `POST /passenger/location/update` - Update passenger location
- `POST /passenger/nearby-taxis` - Get nearby available taxis
- `POST /passenger/book` - Book a taxi
- `GET /passenger/booking/{booking_id}` - Get booking details

### Driver Endpoints

- `POST /driver/register` - Register a new driver
- `POST /driver/setavailability` - Set driver availability (go online/offline)
- `POST /driver/updatelocation` - Update driver location
- `GET /driver/status/{driver_id}` - Get driver status
- `GET /driver/bookings/{driver_id}` - Get driver bookings
- `POST /driver/accept` - Accept a booking
- `POST /driver/start` - Start a ride
- `POST /driver/complete` - Complete a ride
- `GET /driver/booking/{booking_id}` - Get booking details

## Fare Calculation

The fare is calculated using the formula:
```
Fare = (Base Fare + (km × Rate) + (min × Rate)) × Surge Multiplier
```

### Surge Pricing

Surge multiplier is calculated based on passenger-to-driver ratio:
- Ratio < 1.0 → No surge (1.0×)
- Ratio 1.0-1.5 → Mild surge (1.2×-1.4×)
- Ratio 1.5-1.8 → Medium surge (1.5×-1.8×)
- Ratio ≥ 1.8 → High surge (2.0×) - Maximum allowed

## Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── models/               # Data models/classes
│   ├── __init__.py
│   ├── location.py
│   ├── passenger.py
│   ├── driver.py
│   └── booking.py
├── services/             # Business logic services
│   ├── __init__.py
│   ├── firebase_service.py
│   ├── cache_service.py
│   ├── maps_service.py
│   └── fare_service.py
└── routers/              # API route handlers
    ├── __init__.py
    ├── passenger_router.py
    └── driver_router.py
```

## Notes

- The backend uses object-oriented programming with classes and objects as requested
- All services are implemented as classes with proper initialization
- Location updates should be sent every 3-5 seconds for real-time tracking
- The system uses caching to improve performance for frequently accessed data
- Firebase Firestore is used for persistent storage
- Upstash Redis is used for caching driver locations and available drivers list

## License

This project is part of the RealTaxi application.

