# Google Maps Visualization Setup

## Current Status

✅ **Backend**: Using Google Maps Distance Matrix API for accurate road distance calculations
⚠️ **Frontend**: Map visualization requires Google Maps JavaScript API key

## Frontend Map Setup

To enable the interactive map visualization in the frontend:

### Option 1: Add API Key Directly (Quick Setup)

1. Get your Google Maps JavaScript API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Maps JavaScript API" and "Directions API" for your project
3. Open `static/index.html`
4. Find this line (around line 9):
   ```javascript
   mapsApiKey = window.GOOGLE_MAPS_API_KEY || '';
   ```
5. Replace with:
   ```javascript
   mapsApiKey = 'YOUR_ACTUAL_API_KEY_HERE';
   ```

### Option 2: Use Environment Variable (Recommended)

1. Add to your `.env` file:
   ```env
   GOOGLE_MAPS_FRONTEND_API_KEY=your_frontend_api_key_here
   ```

2. Update `static/index.html` to read from backend:
   ```javascript
   // The backend can serve this via an endpoint
   ```

### Option 3: Set in Browser Console (For Testing)

Open browser console and run:
```javascript
window.GOOGLE_MAPS_API_KEY = 'your_api_key_here';
location.reload();
```

## What the Map Shows

When enabled, the map displays:
- 👤 **Green marker**: Passenger/pickup location
- 🚕 **Yellow marker**: Driver location
- 🛣️ **Yellow route line**: Road path between locations
- 📊 **Info box**: Distance and ETA

## API Key Security

⚠️ **Important**: Google Maps JavaScript API keys are meant to be used in frontend code.

**Best Practices:**
1. **Restrict your API key** in Google Cloud Console:
   - Go to "APIs & Services" → "Credentials"
   - Click on your API key
   - Under "Application restrictions", select "HTTP referrers"
   - Add your domain (e.g., `http://localhost:8000/*`)

2. **Use separate keys** for frontend and backend:
   - Frontend key: For Maps JavaScript API (used in browser)
   - Backend key: For Distance Matrix API (used server-side)

## Current Features

✅ Backend uses Google Maps Distance Matrix API (if key configured)
✅ Accurate road distances calculated
✅ Frontend map ready (needs API key to activate)
✅ Fallback to Haversine if API unavailable

## Testing

1. Add your API key to `static/index.html`
2. Restart the server
3. Register as passenger
4. Find nearby taxis
5. Select a driver
6. You should see an interactive map with markers and route!

