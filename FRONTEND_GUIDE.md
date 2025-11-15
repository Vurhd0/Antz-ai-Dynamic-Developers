# RealTaxi Frontend Guide

## Quick Start

1. **Start the Backend Server:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Open the Frontend:**
   - Open your browser and go to: `http://localhost:8000`
   - Or directly: `http://localhost:8000/static/index.html`

## Testing the Workflow

### Passenger Workflow

1. **Register a Passenger** (or use existing: `passenger_001`)
   - Fill in name, phone, location (lat/lon), and vehicle preference
   - Click "Register"

2. **Find Nearby Taxis**
   - Enter your User ID (e.g., `passenger_001`)
   - Enter your current location coordinates
   - Click "Find Taxis"
   - You'll see a list of available drivers with:
     - Distance
     - ETA
     - Estimated fare
     - Surge multiplier

3. **Book a Taxi**
   - Enter User ID and Driver ID (or click "Select This Driver" from nearby taxis)
   - Enter pickup and dropoff coordinates
   - Click "Book Taxi"
   - **Note the Booking ID** - you'll need it for confirmation

4. **Confirm Booking** (Two-way acceptance)
   - After driver accepts, you need to confirm
   - Enter User ID and Booking ID
   - Click "Confirm Booking"

5. **Cancel Booking** (Optional)
   - Enter User ID and Booking ID
   - Click "Cancel Booking"
   - Cancellation fee will be calculated based on:
     - Time elapsed since booking
     - Driver proximity
     - Vehicle type

### Driver Workflow

1. **Register a Driver** (or use existing: `driver_001`)
   - Fill in name, phone, vehicle type, and vehicle number
   - Click "Register Driver"

2. **Go Online**
   - Enter Driver ID
   - Click "Go Online" to make yourself available

3. **Update Location**
   - Enter Driver ID and current coordinates
   - Click "Update Location"
   - (In real app, this happens automatically every 3-5 seconds)

4. **View My Bookings**
   - Enter Driver ID
   - Click "Get Bookings"
   - See all your bookings with status

5. **Accept Booking**
   - Enter Driver ID and Booking ID
   - Click "Accept Booking"
   - This sets status to `DRIVER_ACCEPTED`
   - Passenger must then confirm

6. **Start Ride**
   - After passenger confirms, you can start the ride
   - Enter Driver ID and Booking ID
   - Click "Start Ride"
   - Status changes to `IN_PROGRESS`

7. **Complete Ride**
   - Enter Driver ID, Booking ID, and dropoff location
   - Click "Complete Ride"
   - Final fare is calculated and displayed

## Sample Data

### Pre-loaded Passengers:
- `passenger_001` - Rahul Sharma (Sedan preference)
- `passenger_002` - Priya Patel (SUV preference)
- `passenger_003` - Amit Kumar (Hatchback preference)
- `passenger_004` - Sneha Verma (Premium preference)
- `passenger_005` - Vikram Gupta (Sedan preference)
- `passenger_006` - Anjali Desai (SUV preference)

### Pre-loaded Drivers:
- `driver_001` - Rajesh Kumar (Sedan) - Online & Available
- `driver_002` - Amit Singh (SUV) - Online & Available
- `driver_003` - Priya Sharma (Hatchback) - Online & Available
- `driver_004` - Vikram Mehta (Premium) - Online but on ride
- `driver_005` - Sneha Reddy (Hatchback) - Offline
- `driver_006` - Mohit Agarwal (Sedan) - Online & Available
- `driver_007` - Kavita Nair (SUV) - Online & Available
- `driver_008` - Rohit Malhotra (Premium) - Online & Available
- `driver_009` - Deepika Iyer (Hatchback) - Online & Available
- `driver_010` - Arjun Kapoor (Sedan) - Online & Available

## Testing Complete Workflow

### Example Test Scenario:

1. **As Passenger:**
   - Use `passenger_001` to find nearby taxis
   - Book with `driver_001`
   - Note the Booking ID

2. **As Driver:**
   - Use `driver_001` to view bookings
   - Accept the booking (Booking ID from step 1)
   - Wait for passenger confirmation

3. **As Passenger:**
   - Confirm the booking using the Booking ID

4. **As Driver:**
   - Start the ride
   - Complete the ride with dropoff location

5. **View Results:**
   - Go to "View Data" tab
   - Click "Refresh Data"
   - See all stored data including completed booking

## Features

- ✅ Real-time fare calculation with surge pricing
- ✅ Two-way booking acceptance (driver + passenger)
- ✅ Cancellation fee calculation
- ✅ Distance and ETA calculation
- ✅ Multiple vehicle types
- ✅ Driver availability management
- ✅ Location tracking

## Troubleshooting

- **CORS Errors:** Make sure the backend is running and CORS is enabled
- **404 Errors:** Check that the static files are in the `static/` directory
- **API Errors:** Check browser console (F12) for detailed error messages
- **No Drivers Found:** Make sure drivers are online and available

## API Endpoints Used

- `POST /passenger/register` - Register passenger
- `POST /passenger/nearby-taxis` - Find nearby taxis
- `POST /passenger/book` - Book a taxi
- `POST /passenger/confirm` - Confirm booking
- `POST /passenger/cancel` - Cancel booking
- `POST /driver/register` - Register driver
- `POST /driver/setavailability` - Go online/offline
- `POST /driver/updatelocation` - Update driver location
- `GET /driver/bookings/{driver_id}` - Get driver bookings
- `POST /driver/accept` - Accept booking
- `POST /driver/start` - Start ride
- `POST /driver/complete` - Complete ride
- `GET /debug/data` - View all stored data

