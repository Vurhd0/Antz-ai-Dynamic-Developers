import requests
import json

# --- 1. CONFIGURATION (REQUIRED) ---

# !!! IMPORTANT: Replace YOUR_ORS_API_KEY with your actual, complete key string.
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZjODg4ZjBhN2I4ZDQ2ODNhYzBkMzAwOWMxZDVmZjRjIiwiaCI6Im11cm11cjY0In0="

# Coordinates for testing (Delhi area to Ghaziabad area)
# ORS standard format is [Longitude, Latitude]
TEST_COORDINATES = [
    [-73.9856, 40.7484], # Start: LON, LAT
    [-73.9839, 40.7580]  # End: LON, LAT
]

# Correct ORS endpoint for GeoJSON routing (requires POST and Authorization header)
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


def run_ors_test():
    """
    Makes a direct POST request to ORS using the GeoJSON endpoint
    and Bearer token authentication.
    """
    if ORS_API_KEY == "YOUR_ORS_API_KEY" or not ORS_API_KEY:
        print("🛑 ERROR: Please set your ORS_API_KEY in the script before running.")
        return

    # 1. Prepare Headers (Crucial for Bearer Token Authentication)
    headers = {
        "Authorization": f"Bearer {ORS_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/geo+json"
    }

    # 2. Prepare JSON Body
    payload = {
        "coordinates": TEST_COORDINATES
    }

    print("-" * 50)
    print(f"Attempting POST request to ORS...")
    print(f"Target URL: {ORS_URL}")
    print(f"Payload: {payload}")
    print("-" * 50)

    try:
        response = requests.post(
            ORS_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        print(f"STATUS CODE: {response.status_code}")
        
        # --- Check for Success ---
        if response.status_code == 200:
            data = response.json()
            route_distance_m = data['features'][0]['properties']['summary']['distance']
            route_duration_s = data['features'][0]['properties']['summary']['duration']
            
            print("✅ SUCCESS! ORS API key and request format are correct.")
            print(f"   Response Type: {data['type']}")
            print(f"   Route Distance: {route_distance_m / 1000:.2f} km")
            print(f"   Route Duration: {route_duration_s / 60:.0f} minutes")
            print("\nIf this works, your key is valid and the issue is resolved!")
            return

        # --- Check for Failure (403, 401, 400) ---
        print("❌ REQUEST FAILED.")
        print(f"   Response Headers: {response.headers}")
        print(f"   Response Body (ORS Error):")
        
        try:
            error_data = response.json()
            if response.status_code == 403:
                print(f"   403 Forbidden: {error_data.get('error', 'Unknown Error')}")
                print("\n🛑 **CONCLUSION:** The API key is restricted by OpenRouteService and must be replaced.")
            else:
                print(json.dumps(error_data, indent=2))
        except:
            print(f"   Could not parse JSON error: {response.text[:100]}...")

    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: Could not connect to ORS. Check internet or DNS. Detail: {e}")

if __name__ == "__main__":
    run_ors_test()