from fastapi import APIRouter, HTTPException
import httpx
from config import Config

router = APIRouter(prefix="/api/test/ors", tags=["ORS Testing"])

# Hardcoded coordinates near Delhi (India Gate to Ghaziabad area)
# ORS expects [lon, lat]
TEST_COORDINATES = [
    [77.21, 28.61], # Lon, Lat (Delhi)
    [77.10, 28.70]  # Lon, Lat (Ghaziabad area)
]
ORS_API_KEY = Config.OPENROUTESERVICE_API_KEY

@router.get("/config")
async def check_config():
    """Check if the API key is configured."""
    return {
        "configured": bool(ORS_API_KEY),
        "key_present": ORS_API_KEY[:4] + "..." if ORS_API_KEY else "None"
    }

@router.get("/test-matrix")
async def test_matrix_api():
    """Tests the OpenRouteService Matrix API (used for ETA/distance calculations)."""
    if not ORS_API_KEY:
        raise HTTPException(status_code=503, detail="ORS API Key not configured.")
    
    # Endpoint used by MapsService for distance/duration lookup
    url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    
    payload = {
        "locations": TEST_COORDINATES,
        "metrics": ["distance", "duration"]
    }
    
    headers = {
        # CRITICAL FIX: Ensure Bearer scheme is used for POST requests
        "Authorization": f"Bearer {ORS_API_KEY}", 
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            
            print(f"--- ORS Matrix Test Result ---")
            print(f"URL: {url}")
            print(f"Request Body: {payload}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text (start): {response.text[:500]}...")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "note": "If Status Code is 200, the Matrix API call works correctly."
            }

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        return {
            "success": False,
            "status_code": e.response.status_code,
            "error_message": f"HTTP Error from ORS Matrix API. Check Python console for full response.",
            "ors_response": error_detail
        }
    except Exception as e:
        return {"success": False, "error_message": str(e)}


@router.get("/test-directions")
async def test_directions_api():
    """Tests the OpenRouteService Directions API (used for GeoJSON route lines)."""
    if not ORS_API_KEY:
        raise HTTPException(status_code=503, detail="ORS API Key not configured.")
    
    # Correct V2 endpoint for GeoJSON route shape
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    payload = {
        "coordinates": TEST_COORDINATES
    }
    
    headers = {
        # CRITICAL FIX: Ensure Bearer scheme is used for POST requests
        "Authorization": f"Bearer {ORS_API_KEY}", 
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)

            print(f"--- ORS Directions Test Result ---")
            print(f"URL: {url}")
            print(f"Request Body: {payload}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text (start): {response.text[:500]}...")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json(),
                "note": "If Status Code is 200, the Directions API call works correctly."
            }

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        return {
            "success": False,
            "status_code": e.response.status_code,
            "error_message": f"HTTP Error from ORS Directions API. Check Python console for full response.",
            "ors_response": error_detail
        }
    except Exception as e:
        return {"success": False, "error_message": str(e)}