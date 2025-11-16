from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import passenger_router, driver_router 
from routers import map_proxy 
from routers import test_ors_router # <--- NEW IMPORT
from services.memory_storage import get_memory_storage
from config import Config

# Create FastAPI app instance
app = FastAPI(
    title="RealTaxi Backend API",
    description="Backend API for RealTaxi - Taxi Booking Application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend) - mount before routers to avoid conflicts
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# Include routers
app.include_router(passenger_router)
app.include_router(driver_router)
# Register the map proxy and test router
app.include_router(map_proxy.router) 
app.include_router(test_ors_router.router) # <--- REGISTERED TEST ROUTER


@app.get("/")
async def root():
    """Serve frontend"""
    try:
        return FileResponse("static/index.html")
    except Exception:
        return {
            "message": "Welcome to RealTaxi Backend API",
            "version": "1.0.0",
            "status": "running",
            "frontend": "Visit /static/index.html or http://localhost:8000/static/index.html"
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RealTaxi Backend"
    }


@app.get("/health/storage")
async def storage_health_check():
    """Storage health check endpoint"""
    storage = get_memory_storage()
    stats = storage.get_stats()
    
    return {
        "service": "Memory Storage Health Check",
        "storage": stats,
        "status": "active"
    }


@app.get("/debug/data")
async def debug_data():
    """Debug endpoint to view all stored data"""
    storage = get_memory_storage()
    
    return {
        "passengers": storage.passengers,
        "drivers": storage.drivers,
        "bookings": storage.bookings,
        "locations": storage.locations,
        "stats": storage.get_stats()
    }


@app.get("/config/maps")
async def get_maps_config():
    """
    Get Maps API configuration status
    Returns OpenRouteService API key for frontend use
    """
    from config import Config
    return {
        "ors_api_key": Config.OPENROUTESERVICE_API_KEY if Config.OPENROUTESERVICE_API_KEY else "",
        "ors_configured": bool(Config.OPENROUTESERVICE_API_KEY and Config.OPENROUTESERVICE_API_KEY.strip()),
        "google_maps_configured": bool(Config.GOOGLE_MAPS_API_KEY and Config.GOOGLE_MAPS_API_KEY.strip()),
        "note": "OpenRouteService API key is used for map visualization and routing"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)