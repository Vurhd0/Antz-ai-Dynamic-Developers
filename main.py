from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import passenger_router, driver_router

# Create FastAPI app instance
app = FastAPI(
    title="RealTaxi Backend API",
    description="Backend API for RealTaxi - Taxi Booking Application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(passenger_router)
app.include_router(driver_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to RealTaxi Backend API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RealTaxi Backend"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

