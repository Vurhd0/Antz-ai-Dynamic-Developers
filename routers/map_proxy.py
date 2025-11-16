from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Tuple
import httpx
from config import Config

router = APIRouter(prefix="/api/maps", tags=["Map Proxy"])

# Use the configuration from your existing Config object
ORS_API_KEY = Config.OPENROUTESERVICE_API_KEY
# Use POST endpoint with GeoJSON format - this is the official ORS protocol
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


class DirectionsRequest(BaseModel):
    """Model for the coordinates array received from the frontend JS."""
    coordinates: List[List[float]]  # Changed from Tuple to List for Pydantic compatibility


@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to check API key configuration."""
    return {
        "api_key_configured": bool(ORS_API_KEY and ORS_API_KEY.strip()),
        "api_key_length": len(ORS_API_KEY) if ORS_API_KEY else 0,
        "api_key_prefix": ORS_API_KEY[:20] + "..." if ORS_API_KEY and len(ORS_API_KEY) > 20 else (ORS_API_KEY or "None"),
        "api_key_suffix": "..." + ORS_API_KEY[-10:] if ORS_API_KEY and len(ORS_API_KEY) > 10 else (ORS_API_KEY or "None"),
        "has_equals_sign": "=" in (ORS_API_KEY or ""),
        "note": "Check if OPENROUTESERVICE_API_KEY is set in .env file"
    }


@router.post("/directions")
async def get_route_proxy(request: DirectionsRequest):
    """
    Proxy endpoint to call the OpenRouteService Directions API from the backend.
    This avoids the 403 Access Disallowed error from browser-origin requests.
    Uses POST method with Bearer token authentication - this is the official ORS protocol.
    Endpoint: POST /v2/directions/driving-car/geojson
    """
    # CRITICAL: Get API key and ensure it's not stripped of trailing = characters
    # Base64-encoded API keys often end with = padding, which MUST be preserved
    api_key = ORS_API_KEY.rstrip() if ORS_API_KEY else ""  # Only strip trailing whitespace, not =
    
    if not api_key:
        raise HTTPException(status_code=503, detail="Map Service API key not configured in backend.")
    
    # Warn if API key seems incomplete (missing trailing =)
    # OpenRouteService API keys typically end with = or ==
    expected_length_with_equals = 120  # Approximate length for your API key format
    if len(api_key) < expected_length_with_equals and not api_key.endswith("="):
        print(f"⚠️  WARNING: API key might be missing trailing '=' character!")
        print(f"   Current length: {len(api_key)}")
        print(f"   Current ending: ...{api_key[-10:]}")
        print(f"   Expected format: Should end with '=' (e.g., ...In0=)")
        print(f"   Check your .env file: OPENROUTESERVICE_API_KEY should match your curl example exactly")
    
    # Validate coordinates
    if not request.coordinates or len(request.coordinates) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinates required")
    
    # Validate coordinate format
    for i, coord in enumerate(request.coordinates):
        if not isinstance(coord, (list, tuple)) or len(coord) < 2:
            raise HTTPException(status_code=400, detail=f"Coordinate {i} must have at least 2 values [lon, lat]")
        if len(coord) > 2:
            # ORS accepts [lon, lat, elevation] but we only use first 2
            request.coordinates[i] = [float(coord[0]), float(coord[1])]
        else:
            request.coordinates[i] = [float(coord[0]), float(coord[1])]
    
    try:
        async with httpx.AsyncClient() as client:
            # Use POST method with Bearer token - this is the official ORS protocol for GeoJSON
            # The POST endpoint returns full GeoJSON FeatureCollection with geometry
            payload = {
                "coordinates": request.coordinates  # ORS expects [[lon, lat], [lon, lat], ...]
            }
            
            # CRITICAL: Use Bearer token in Authorization header (official ORS protocol)
            headers = {
                "Authorization": f"Bearer {api_key}",  # Bearer token format
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8"
            }
            
            print(f"🗺️ ORS API Request: POST {ORS_DIRECTIONS_URL}")
            print(f"   API Key length: {len(api_key)}")
            print(f"   API Key starts with: {api_key[:10]}...")
            print(f"   API Key ends with: ...{api_key[-15:]}")
            print(f"   API Key contains '=': {'=' in api_key}")
            print(f"   Request payload: {payload}")
            print(f"   Authorization header: Bearer {api_key[:10]}...")
            
            response = await client.post(
                ORS_DIRECTIONS_URL,
                json=payload,  # httpx will handle JSON serialization
                headers=headers,
                timeout=15.0,
                follow_redirects=True
            )
            
            # Log the actual request details (for debugging)
            print(f"   Request method: {response.request.method}")
            print(f"   Request URL: {response.request.url}")
            
            print(f"✅ ORS API Response: Status {response.status_code}")
            print(f"   Response headers: {dict(response.headers)}")
            
            if response.status_code == 403:
                print(f"❌ 403 Forbidden - Check API key and permissions")
                print(f"   Response text: {response.text[:500]}")
                raise HTTPException(
                    status_code=403,
                    detail=f"ORS API returned 403 Forbidden. Check API key configuration and permissions. Response: {response.text[:200]}"
                )
            
            response.raise_for_status()
            
            # Parse and return GeoJSON response
            result = response.json()
            print(f"✅ ORS API Response parsed successfully (type: {result.get('type', 'unknown')})")
            
            # Return the GeoJSON response directly to the frontend
            return result
            
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", {}).get("message", f"HTTP Error {e.response.status_code}")
        except:
            error_detail = e.response.text or f"HTTP Error {e.response.status_code}"
        
        print(f"❌ ORS Proxy Error (HTTP {e.response.status_code}): {error_detail}")
        print(f"   Response text: {e.response.text[:500]}")
        
        if e.response.status_code in [403, 401]:
            raise HTTPException(
                status_code=403, 
                detail=f"ORS API call failed: Check API Key/Permissions. Detail: {error_detail}"
            )
        raise HTTPException(status_code=500, detail=f"External Map Service Error: {error_detail}")
    
    except httpx.RequestError as e:
        print(f"❌ ORS Proxy Network Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error contacting ORS: {str(e)}")
    
    except Exception as e:
        print(f"❌ ORS Proxy Unexpected Error: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

