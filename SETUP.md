# Quick Setup Guide

## To Run the App Immediately (Mock Mode)

The app is now configured to run in **mock mode** if Firebase credentials are not found. This means:

1. **No .env file needed** - The app will use default values
2. **No Firebase credentials needed** - The app will run in mock mode (operations will be logged but not persisted)
3. **No Upstash Redis needed** - Caching will be disabled
4. **No Google Maps API needed** - Distance calculations will return None (you'll need to handle this in your app)

## Start the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

## For Full Functionality

### 1. Create .env file

Create a `.env` file in the root directory with:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id

# Upstash Redis Configuration (Optional)
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_TOKEN=your-redis-token

# Google Maps API Configuration (Required for distance/ETA)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Fare Configuration
BASE_FARE=50.0
RATE_PER_KM=10.0
RATE_PER_MIN=2.0

# Location Update Interval (seconds)
LOCATION_UPDATE_INTERVAL=5
```

### 2. Firebase Setup

1. Go to Firebase Console: https://console.firebase.google.com/
2. Create a new project or select existing
3. Go to Project Settings > Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON file as `firebase-credentials.json` in the project root

### 3. Upstash Redis (Optional)

1. Go to https://upstash.com/
2. Create a Redis database
3. Copy the REST URL and Token
4. Add them to `.env`

### 4. Google Maps API

1. Go to Google Cloud Console
2. Enable Distance Matrix API
3. Create an API key
4. Add it to `.env`

## Testing the API

Once the server is running, you can test endpoints using:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Mock Mode Behavior

In mock mode:
- All Firebase operations will print "Mock: Would..." messages
- No data will be persisted
- Cache operations will be skipped
- Google Maps API calls will return None (handle gracefully in your app)

This allows you to test the API structure and endpoints without setting up external services.

