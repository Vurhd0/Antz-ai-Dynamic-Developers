const API_BASE = 'http://localhost:8000';

// Application State
let appState = {
    currentRole: null,
    currentUser: null,
    currentDriver: null,
    currentBooking: null
};

// Screen Management
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
}

function showStep(stepId) {
    // Hide all steps in current flow
    const currentFlow = appState.currentRole === 'passenger' ? 'passenger-flow' : 'driver-flow';
    document.querySelectorAll(`#${currentFlow} .flow-step`).forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById(stepId).classList.add('active');
    
    // Clear all status messages when changing steps
    clearAllStatusMessages();
}

function clearAllStatusMessages() {
    // Clear passenger status messages
    clearStatus('passenger-register-status');
    clearStatus('nearby-taxis');
    clearStatus('booking-status');
    clearStatus('confirm-status');
    clearStatus('ride-status-message');
    
    // Clear driver status messages
    clearStatus('driver-register-status');
    clearStatus('online-status');
    clearStatus('location-status');
    clearStatus('driver-bookings');
    clearStatus('accept-status');
    clearStatus('ride-action-status');
}

// Role Selection
function selectRole(role) {
    appState.currentRole = role;
    if (role === 'passenger') {
        showScreen('passenger-flow');
        showStep('passenger-register');
    } else {
        showScreen('driver-flow');
        showStep('driver-register');
    }
}

function goToRoleSelection() {
    appState.currentRole = null;
    appState.currentUser = null;
    appState.currentDriver = null;
    appState.currentBooking = null;
    
    // Stop all polling intervals
    stopBookingStatusPolling();
    stopDriverBookingsPolling();
    stopDriverBookingStatusPolling();
    
    showScreen('role-selection');
}

// Helper Functions
function clearStatus(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

function showStatus(elementId, message, type = 'info') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="status-box status-${type}">${message}</div>`;
    }
}

function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// Passenger Functions
async function registerPassenger() {
    // Clear previous status messages
    clearStatus('passenger-register-status');
    
    const user_id = `passenger_${Date.now()}`;
    const data = {
        user_id: user_id,
        latitude: parseFloat(document.getElementById('passenger-lat').value),
        longitude: parseFloat(document.getElementById('passenger-lon').value),
        phone_number: document.getElementById('passenger-phone').value,
        name: document.getElementById('passenger-name').value,
        vehicle_preference: document.getElementById('passenger-vehicle').value
    };

    try {
        const response = await fetch(`${API_BASE}/passenger/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            appState.currentUser = user_id;
            document.getElementById('search-user-id').value = user_id;
            document.getElementById('book-user-id').value = user_id;
            document.getElementById('confirm-user-id').value = user_id;
            showStatus('passenger-register-status', 
                `✅ Registered successfully! User ID: ${user_id}`, 
                'success');
            setTimeout(() => {
                showStep('passenger-find-taxis');
            }, 1500);
        } else {
            showStatus('passenger-register-status', `❌ ${result.message || 'Registration failed'}`, 'error');
        }
    } catch (error) {
        showStatus('passenger-register-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function findNearbyTaxis() {
    // Clear previous status messages
    clearStatus('nearby-taxis');
    
    // Get pickup location
    const pickupLat = parseFloat(document.getElementById('search-lat').value);
    const pickupLon = parseFloat(document.getElementById('search-lon').value);
    
    // Get destination location from search form
    const destLatEl = document.getElementById('search-dest-lat');
    const destLonEl = document.getElementById('search-dest-lon');
    const destLat = destLatEl ? parseFloat(destLatEl.value || '') : NaN;
    const destLon = destLonEl ? parseFloat(destLonEl.value || '') : NaN;
    
    // Also sync to booking form if provided
    if (!isNaN(destLat) && !isNaN(destLon)) {
        const bookDestLat = document.getElementById('book-dropoff-lat');
        const bookDestLon = document.getElementById('book-dropoff-lon');
        if (bookDestLat) bookDestLat.value = destLat;
        if (bookDestLon) bookDestLon.value = destLon;
    }
    
    if (isNaN(pickupLat) || isNaN(pickupLon)) {
        showStatus('nearby-taxis', '❌ Please enter valid pickup location (latitude and longitude).', 'error');
        return;
    }
    
    const data = {
        user_id: document.getElementById('search-user-id').value || appState.currentUser,
        latitude: pickupLat,
        longitude: pickupLon
    };
    
    // Add destination if provided
    if (!isNaN(destLat) && !isNaN(destLon)) {
        data.destination_latitude = destLat;
        data.destination_longitude = destLon;
    }

    try {
        const response = await fetch(`${API_BASE}/passenger/nearby-taxis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.drivers && result.drivers.length > 0) {
            // Show pickup → destination route on map with nearby drivers
            if (!isNaN(destLat) && !isNaN(destLon)) {
                setTimeout(() => {
                    showPickupToDestination(
                        { lat: pickupLat, lon: pickupLon },
                        { lat: destLat, lon: destLon },
                        result.drivers // Pass driver data to display on map
                    );
                }, 500);
            } else {
                // No destination provided, show only pickup location
                // (we could show driver → pickup routes here if needed)
                const mapWrapper = document.getElementById('map-container-wrapper');
                if (mapWrapper) {
                    mapWrapper.style.display = 'block';
                    if (!map) {
                        initializeMap(pickupLat, pickupLon);
                    }
                }
            }
            let html = `<div class="status-box status-success" style="margin-bottom: 20px;">
                ✅ Found ${result.drivers.length} nearby driver${result.drivers.length > 1 ? 's' : ''}! Select one to continue.
            </div>`;
            
            // Show ride distance if destination was provided
            if (result.drivers[0].ride_distance_km) {
                html += `<div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid var(--success-green);">
                    <p style="margin: 0; font-weight: 600; color: var(--taxi-black);">
                        📍 <strong>Ride Distance:</strong> ${result.drivers[0].ride_distance_km.toFixed(2)} km 
                        <span style="margin-left: 15px;">⏱️ <strong>Ride Time:</strong> ${Math.round(result.drivers[0].ride_eta_minutes)} min</span>
                    </p>
                </div>`;
            }
            
            html += `<div style="display: grid; gap: 15px; margin-top: 20px;">`;
            result.drivers.forEach((driver, index) => {
                // Driver distance is from driver to pickup (for ETA)
                // Ride distance is from pickup to destination (for fare)
                html += `
                    <div class="driver-card" style="cursor: pointer; transition: all 0.3s;" 
                         onmouseover="this.style.transform='scale(1.02)'" 
                         onmouseout="this.style.transform='scale(1)'"
                         onclick="selectDriver('${driver.driver_id}')">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h3 style="margin: 0;">${driver.driver_name || 'Driver'} <span class="badge badge-available">Available</span></h3>
                            <span style="font-size: 0.9em; color: #666;">#${index + 1}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                            <p><strong>🚗 Driver ID:</strong> <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 4px;">${driver.driver_id}</code></p>
                            <p><strong>📍 To Pickup:</strong> ${driver.distance_text || driver.distance_km?.toFixed(2) + ' km' || 'N/A'}</p>
                            <p><strong>⏱️ Pickup ETA:</strong> ${driver.eta_text || Math.round(driver.eta_minutes) + ' min' || 'N/A'}</p>
                            <p><strong>⚡ Surge:</strong> ${driver.surge_multiplier || 1.0}x</p>
                        </div>
                        ${driver.ride_distance_km ? `
                        <div style="background: #e3f2fd; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
                            <p style="margin: 0; font-size: 0.9em; color: #1565c0;">
                                📍 <strong>Ride Distance:</strong> ${driver.ride_distance_km.toFixed(2)} km 
                                <span style="margin-left: 10px;">⏱️ <strong>Ride Time:</strong> ${Math.round(driver.ride_eta_minutes)} min</span>
                            </p>
                        </div>
                        ` : ''}
                        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%); padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <p style="margin: 0; font-size: 1.3em; font-weight: 700; color: var(--taxi-black);">
                                💰 Estimated Fare: <span style="color: var(--taxi-yellow-dark);">₹${driver.estimated_fare?.toFixed(2) || 'N/A'}</span>
                            </p>
                            <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #856404;">
                                * Based on ride distance (${driver.ride_distance_km?.toFixed(2) || 'N/A'} km)
                            </p>
                        </div>
                        <button onclick="selectDriver('${driver.driver_id}')" class="primary-btn" style="width: 100%; margin-top: 10px; padding: 15px; font-size: 16px;">
                            ✓ Select This Driver
                        </button>
                    </div>
                `;
            });
            html += `</div>`;
            document.getElementById('nearby-taxis').innerHTML = html;
            // Don't auto-advance - let user select a driver first
        } else {
            showStatus('nearby-taxis', '❌ No nearby drivers found. Please try again or check your location.', 'error');
        }
    } catch (error) {
        showStatus('nearby-taxis', `❌ Error: ${error.message}`, 'error');
    }
}

function selectDriver(driverId) {
    // Set the driver ID in the booking form
    document.getElementById('book-driver-id').value = driverId;
    
    // Get driver location and show on map
    const passengerLat = parseFloat(document.getElementById('search-lat').value);
    const passengerLon = parseFloat(document.getElementById('search-lon').value);
    
    // Find driver data to get location
    fetch(`${API_BASE}/driver/bookings/${driverId}`)
        .then(res => res.json())
        .then(result => {
            // Try to get driver location from storage
            fetch(`${API_BASE}/debug/data`)
                .then(res => res.json())
                .then(debugData => {
                    const drivers = debugData.drivers || {};
                    const driver = drivers[driverId];
                    if (driver && driver.current_location) {
                        const driverLat = driver.current_location.latitude;
                        const driverLon = driver.current_location.longitude;
                        
                        // Show driver → passenger route (before booking)
                        setTimeout(() => {
                            showMapWithLocations(passengerLat, passengerLon, driverLat, driverLon);
                        }, 500);
                    }
                })
                .catch(err => console.error('Error getting driver location:', err));
        })
        .catch(err => console.error('Error getting driver data:', err));
    
    // Show selected driver info
    const selectedDriverInfo = document.getElementById('selected-driver-info');
    const selectedDriverDisplay = document.getElementById('selected-driver-display');
    if (selectedDriverInfo && selectedDriverDisplay) {
        selectedDriverDisplay.textContent = driverId;
        selectedDriverInfo.style.display = 'block';
    }
    
    // Show success message
    showStatus('nearby-taxis', 
        `✅ Driver ${driverId} selected! Moving to booking step...`, 
        'success');
    
    // Move to booking step after a short delay
    setTimeout(() => {
        showStep('passenger-book');
        // Highlight the selected driver ID field
        const driverIdField = document.getElementById('book-driver-id');
        if (driverIdField) {
            driverIdField.style.background = '#fff3cd';
            driverIdField.style.borderColor = 'var(--taxi-yellow)';
            setTimeout(() => {
                driverIdField.style.background = '#f5f5f5';
                driverIdField.style.borderColor = '';
            }, 2000);
        }
    }, 1000);
}

async function bookTaxi() {
    // Clear previous status messages
    clearStatus('booking-status');
    
    // Get and validate input values
    const user_id = document.getElementById('book-user-id').value || appState.currentUser;
    const driver_id = document.getElementById('book-driver-id').value.trim();
    const pickup_lat = parseFloat(document.getElementById('book-pickup-lat').value);
    const pickup_lon = parseFloat(document.getElementById('book-pickup-lon').value);
    const dropoff_lat = parseFloat(document.getElementById('book-dropoff-lat').value);
    const dropoff_lon = parseFloat(document.getElementById('book-dropoff-lon').value);
    
    // Validate required fields
    if (!user_id) {
        showStatus('booking-status', `❌ User ID is missing. Please register first.`, 'error');
        return;
    }
    
    if (!driver_id) {
        showStatus('booking-status', `❌ Please select a driver first. Click "Select This Driver" from the nearby taxis list.`, 'error');
        return;
    }
    
    if (isNaN(pickup_lat) || isNaN(pickup_lon)) {
        showStatus('booking-status', `❌ Invalid pickup location. Please enter valid latitude and longitude.`, 'error');
        return;
    }
    
    if (isNaN(dropoff_lat) || isNaN(dropoff_lon)) {
        showStatus('booking-status', `❌ Invalid dropoff location. Please enter valid latitude and longitude.`, 'error');
        return;
    }
    
    const data = {
        user_id: user_id,
        driver_id: driver_id,
        pickup_latitude: pickup_lat,
        pickup_longitude: pickup_lon,
        dropoff_latitude: dropoff_lat,
        dropoff_longitude: dropoff_lon
    };

    console.log('Booking request data:', data);
    
    try {
        const response = await fetch(`${API_BASE}/passenger/book`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        console.log('Response status:', response.status, response.statusText);
        
        let result;
        try {
            result = await response.json();
            console.log('Response data:', result);
        } catch (jsonError) {
            // If response is not JSON, get text
            const text = await response.text();
            console.error('JSON parse error:', jsonError, 'Response text:', text);
            showStatus('booking-status', `❌ Server Error (${response.status}): ${text || 'Booking failed'}`, 'error');
            return;
        }
        
        if (!response.ok) {
            // Handle HTTP error responses
            const errorMsg = result.detail || result.message || `HTTP ${response.status}: Booking failed`;
            console.error('Booking failed:', errorMsg);
            showStatus('booking-status', `❌ ${errorMsg}`, 'error');
            return;
        }
        
        if (result.success) {
            appState.currentBooking = result.booking_id;
            document.getElementById('confirm-booking-id').value = result.booking_id;
            
            // Initially show driver → passenger (pickup) location route
            const booking = result.booking;
            const driverId = booking.driver_id;
            if (driverId && booking.pickup_location) {
                fetch(`${API_BASE}/debug/data`)
                    .then(res => res.json())
                    .then(debugData => {
                        const drivers = debugData.drivers || {};
                        const driver = drivers[driverId];
                        if (driver && driver.current_location) {
                            const driverLat = driver.current_location.latitude;
                            const driverLon = driver.current_location.longitude;
                            
                            // Show driver → passenger (pickup) route initially
                            setTimeout(() => {
                                showMapWithLocations(
                                    booking.pickup_location.latitude, 
                                    booking.pickup_location.longitude, 
                                    driverLat, driverLon,
                                    null, // Distance will be calculated by showMapWithLocations
                                    null   // ETA will be calculated by showMapWithLocations
                                );
                            }, 500);
                        }
                    })
                    .catch(err => console.error('Error getting driver location for map:', err));
            }
            
            showStatus('booking-status', 
                `✅ Booking Created!<br>
                <strong>Booking ID:</strong> ${result.booking_id}<br>
                <strong>Fare:</strong> ₹${result.booking.fare || 'N/A'}<br>
                <strong>Distance:</strong> ${result.booking.distance_km ? (typeof result.booking.distance_km === 'number' ? result.booking.distance_km.toFixed(2) : result.booking.distance_km) + ' km' : 'Calculating...'}<br>
                <strong>ETA:</strong> ${result.booking.estimated_time_minutes || 'N/A'} min<br>
                <p style="margin-top: 15px;">⏳ Waiting for driver to accept...</p>`, 
                'success');
            
            // Reset route switch flag for new booking
            hasSwitchedToPickupRoute = false;
            
            // Start continuous polling for driver acceptance
            startBookingStatusPolling();
        } else {
            showStatus('booking-status', `❌ ${result.message || result.detail || 'Booking failed'}`, 'error');
        }
    } catch (error) {
        console.error('Booking error:', error);
        showStatus('booking-status', `❌ Network Error: ${error.message}. Please check if the server is running.`, 'error');
    }
}

let bookingStatusInterval = null;

function startBookingStatusPolling() {
    // Clear any existing interval
    if (bookingStatusInterval) {
        clearInterval(bookingStatusInterval);
    }
    
    // Poll every 2 seconds
    bookingStatusInterval = setInterval(async () => {
        await checkBookingStatus();
    }, 2000);
    
    // Also check immediately
    checkBookingStatus();
}

function stopBookingStatusPolling() {
    if (bookingStatusInterval) {
        clearInterval(bookingStatusInterval);
        bookingStatusInterval = null;
    }
}

// Calculate haversine distance between two coordinates (in meters)
function calculateDistanceMeters(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
}

// Track whether we've switched to pickup→destination route
let hasSwitchedToPickupRoute = false;

async function checkBookingStatus() {
    if (!appState.currentBooking) {
        stopBookingStatusPolling();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/passenger/booking/${appState.currentBooking}`);
        const result = await response.json();
        
        if (result.success && result.booking) {
            const booking = result.booking;
            
            // Monitor driver distance and switch routes when driver is within 100m
            if (booking.status === 'pending' || booking.status === 'driver_accepted' || booking.status === 'confirmed') {
                if (booking.pickup_location && booking.dropoff_location && !hasSwitchedToPickupRoute) {
                    // Check driver location
                    fetch(`${API_BASE}/debug/data`)
                        .then(res => res.json())
                        .then(debugData => {
                            const drivers = debugData.drivers || {};
                            const driver = drivers[booking.driver_id];
                            
                            if (driver && driver.current_location) {
                                const driverLat = driver.current_location.latitude;
                                const driverLon = driver.current_location.longitude;
                                const pickupLat = booking.pickup_location.latitude;
                                const pickupLon = booking.pickup_location.longitude;
                                
                                // Calculate distance in meters
                                const distanceMeters = calculateDistanceMeters(
                                    driverLat, driverLon,
                                    pickupLat, pickupLon
                                );
                                
                                console.log(`📏 Driver distance from pickup: ${distanceMeters.toFixed(0)}m`);
                                
                                // If driver is within 100m, switch to pickup → destination route
                                if (distanceMeters <= 100 && !hasSwitchedToPickupRoute) {
                                    console.log('✅ Driver reached pickup location! Switching to pickup → destination route');
                                    hasSwitchedToPickupRoute = true;
                                    
                                    showPickupToDestination(
                                        { lat: pickupLat, lon: pickupLon },
                                        { lat: booking.dropoff_location.latitude, lon: booking.dropoff_location.longitude }
                                    );
                                } else if (distanceMeters > 100 && !hasSwitchedToPickupRoute) {
                                    // Still showing driver → pickup, update it
                                    showMapWithLocations(
                                        pickupLat, pickupLon,
                                        driverLat, driverLon,
                                        null, null
                                    );
                                }
                            }
                        })
                        .catch(err => console.error('Error checking driver distance:', err));
                }
            }
            
            if (booking.status === 'driver_accepted' && !booking.passenger_confirmed) {
                stopBookingStatusPolling();
                showStep('passenger-confirm');
                showStatus('confirm-status', 
                    `✅ Driver has accepted! Please confirm to proceed.`, 
                    'success');
            } else if (booking.status === 'confirmed') {
                // Continue monitoring - don't stop polling yet
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'in_progress') {
                stopBookingStatusPolling();
                hasSwitchedToPickupRoute = true; // Reset flag for next booking
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'completed') {
                stopBookingStatusPolling();
                hasSwitchedToPickupRoute = false; // Reset flag for next booking
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'cancelled') {
                stopBookingStatusPolling();
                hasSwitchedToPickupRoute = false; // Reset flag for next booking
                showStatus('booking-status', '❌ Booking was cancelled.', 'error');
            }
            // If still pending, continue polling
        }
    } catch (error) {
        console.error('Error checking booking status:', error);
    }
}

function updateRideStatus(booking) {
    // Format distance properly
    const distance = booking.distance_km ? 
        (typeof booking.distance_km === 'number' ? booking.distance_km.toFixed(2) : booking.distance_km) : 
        'Calculating...';
    
    // Format fare properly
    const fare = booking.fare ? 
        (typeof booking.fare === 'number' ? booking.fare.toFixed(2) : booking.fare) : 
        'N/A';
    
    const statusHtml = `
        <div class="ride-status-card">
            <h3>Booking ${booking.booking_id}</h3>
            <p><strong>Status:</strong> <span class="badge badge-${booking.status === 'completed' ? 'available' : 'online'}">${booking.status}</span></p>
            <p><strong>Driver ID:</strong> ${booking.driver_id || 'N/A'}</p>
            <p><strong>Fare:</strong> ₹${fare}</p>
            <p><strong>Distance:</strong> ${distance} km</p>
            <p><strong>Estimated Time:</strong> ${booking.estimated_time_minutes ? Math.round(booking.estimated_time_minutes) + ' min' : 'N/A'}</p>
            ${booking.surge_multiplier && booking.surge_multiplier > 1 ? `<p><strong>Surge:</strong> ${booking.surge_multiplier}x</p>` : ''}
        </div>
    `;
    document.getElementById('ride-status-content').innerHTML = statusHtml;
    
    // Show appropriate map based on ride status
    if (booking.status === 'in_progress') {
        // After ride starts: show driver → destination
        if (booking.dropoff_location) {
            // Get current driver location
            fetch(`${API_BASE}/debug/data`)
                .then(res => res.json())
                .then(debugData => {
                    const drivers = debugData.drivers || {};
                    const driver = drivers[booking.driver_id];
                    if (driver && driver.current_location) {
                        showRideInProgress(
                            { lat: driver.current_location.latitude, lon: driver.current_location.longitude },
                            { lat: booking.dropoff_location.latitude, lon: booking.dropoff_location.longitude }
                        );
                    } else if (booking.pickup_location) {
                        // Fallback: use pickup location as driver location
                        showRideInProgress(
                            { lat: booking.pickup_location.latitude, lon: booking.pickup_location.longitude },
                            { lat: booking.dropoff_location.latitude, lon: booking.dropoff_location.longitude }
                        );
                    }
                })
                .catch(err => console.error('Error getting driver location:', err));
        }
    } else if (booking.status === 'confirmed') {
        // If confirmed but not started yet, continue monitoring
        // Route switching is handled in checkBookingStatus() based on driver distance
    }
    // For pending/driver_accepted, route is managed by checkBookingStatus()
}

async function confirmBooking() {
    // Clear previous status messages
    clearStatus('confirm-status');
    
    const data = {
        user_id: document.getElementById('confirm-user-id').value || appState.currentUser,
        booking_id: document.getElementById('confirm-booking-id').value || appState.currentBooking
    };

    try {
        const response = await fetch(`${API_BASE}/passenger/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            showStatus('confirm-status', 
                `✅ Booking confirmed! Your ride is ready.`, 
                'success');
            setTimeout(() => {
                showStep('passenger-ride-status');
                checkRideStatus();
            }, 1500);
        } else {
            showStatus('confirm-status', `❌ ${result.message || 'Confirmation failed'}`, 'error');
        }
    } catch (error) {
        showStatus('confirm-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function checkRideStatus() {
    if (!appState.currentBooking) return;
    await checkBookingStatus();
}

async function cancelBooking() {
    const data = {
        user_id: appState.currentUser,
        booking_id: appState.currentBooking
    };

    try {
        const response = await fetch(`${API_BASE}/passenger/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        showStatus('ride-status-message', 
            `✅ ${result.message}<br>
            <strong>Cancellation Fee:</strong> ₹${result.cancellation_fee || 0}`, 
            result.success ? 'success' : 'error');
    } catch (error) {
        showStatus('ride-status-message', `❌ Error: ${error.message}`, 'error');
    }
}

// Driver Functions
async function registerDriver() {
    // Clear previous status messages
    clearStatus('driver-register-status');
    
    const driver_id = `driver_${Date.now()}`;
    const data = {
        driver_id: driver_id,
        name: document.getElementById('driver-name').value,
        phone_number: document.getElementById('driver-phone').value,
        vehicle_type: document.getElementById('driver-vehicle-type').value,
        vehicle_number: document.getElementById('driver-vehicle-number').value
    };

    try {
        const response = await fetch(`${API_BASE}/driver/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            appState.currentDriver = driver_id;
            document.getElementById('online-driver-id').value = driver_id;
            document.getElementById('bookings-driver-id').value = driver_id;
            document.getElementById('accept-driver-id').value = driver_id;
            document.getElementById('start-driver-id').value = driver_id;
            showStatus('driver-register-status', 
                `✅ Registered successfully! Driver ID: ${driver_id}`, 
                'success');
            setTimeout(() => {
                showStep('driver-online');
            }, 1500);
        } else {
            showStatus('driver-register-status', `❌ ${result.message || 'Registration failed'}`, 'error');
        }
    } catch (error) {
        showStatus('driver-register-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function goOnline() {
    // Clear previous status messages
    clearStatus('online-status');
    
    const data = {
        driver_id: document.getElementById('online-driver-id').value || appState.currentDriver,
        is_available: true
    };

    try {
        const response = await fetch(`${API_BASE}/driver/setavailability`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            // Update location
            await updateLocation();
            showStatus('online-status', `✅ You're now online! Waiting for ride requests...`, 'success');
            setTimeout(() => {
                showStep('driver-requests');
                startDriverBookingsPolling();
            }, 1500);
        } else {
            showStatus('online-status', `❌ ${result.message || 'Failed to go online'}`, 'error');
        }
    } catch (error) {
        showStatus('online-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function goOffline() {
    const data = {
        driver_id: document.getElementById('online-driver-id').value || appState.currentDriver,
        is_available: false
    };

    try {
        const response = await fetch(`${API_BASE}/driver/setavailability`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        showStatus('online-status', `✅ You're now offline.`, 'info');
    } catch (error) {
        showStatus('online-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function updateLocation() {
    const data = {
        driver_id: appState.currentDriver,
        latitude: parseFloat(document.getElementById('location-lat').value),
        longitude: parseFloat(document.getElementById('location-lon').value)
    };

    try {
        const response = await fetch(`${API_BASE}/driver/updatelocation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        // Silent update
    } catch (error) {
        console.error('Error updating location:', error);
    }
}

let driverBookingsInterval = null;

async function getDriverBookings() {
    const driver_id = document.getElementById('bookings-driver-id').value || appState.currentDriver;

    try {
        const response = await fetch(`${API_BASE}/driver/bookings/${driver_id}`);
        const result = await response.json();
        
        if (result.success && result.bookings && result.bookings.length > 0) {
            // Filter to show only active bookings (pending, driver_accepted, confirmed, in_progress)
            const activeBookings = result.bookings.filter(b => 
                ['pending', 'driver_accepted', 'confirmed', 'in_progress'].includes(b.status)
            );
            
            if (activeBookings.length > 0) {
                let html = `<h3 style="color: var(--taxi-black); margin-bottom: 15px;">📋 You have ${activeBookings.length} active booking(s):</h3>`;
                activeBookings.forEach(booking => {
                    const statusBadge = booking.status === 'completed' ? 'available' : 
                                       booking.status === 'in_progress' ? 'online' : 
                                       booking.status === 'confirmed' ? 'available' : 
                                       booking.status === 'driver_accepted' ? 'online' : 'unavailable';
                    html += `
                        <div class="booking-card">
                            <h3>Booking ${booking.booking_id} 
                                <span class="badge badge-${statusBadge}">${booking.status}</span>
                            </h3>
                            <p><strong>👤 Passenger:</strong> ${booking.passenger_id}</p>
                            <p style="font-size: 1.1em; margin: 8px 0;"><strong>💰 Fare:</strong> <span style="color: var(--taxi-yellow-dark); font-weight: 700;">₹${booking.fare || 'N/A'}</span></p>
                            <p><strong>📏 Distance:</strong> ${booking.distance_km ? (typeof booking.distance_km === 'number' ? booking.distance_km.toFixed(2) : booking.distance_km) + ' km' : 'Calculating...'}</p>
                            <p><strong>📊 Status:</strong> ${booking.status}</p>
                            ${booking.status === 'pending' ? `
                                <button onclick="selectBookingForAccept('${booking.booking_id}')" class="success-btn" style="margin-top: 10px; margin-right: 10px;">✓ Accept</button>
                                <button onclick="declineBooking('${booking.booking_id}')" class="danger-btn" style="margin-top: 10px;">✕ Decline</button>
                            ` : booking.status === 'driver_accepted' ? `
                                <p style="color: var(--taxi-blue); margin-top: 10px; font-weight: 600;">⏳ Waiting for passenger confirmation...</p>
                            ` : booking.status === 'confirmed' ? `
                                <button onclick="selectBookingForRide('${booking.booking_id}')" class="primary-btn" style="margin-top: 10px;">▶ Start Ride</button>
                            ` : booking.status === 'in_progress' ? `
                                <p style="color: var(--success-green); margin-top: 10px; font-weight: 600;">🚗 Ride in progress...</p>
                                <button onclick="selectBookingForRide('${booking.booking_id}')" class="success-btn" style="margin-top: 10px;">🏁 Complete Ride</button>
                            ` : ''}
                        </div>
                    `;
                });
                document.getElementById('driver-bookings').innerHTML = html;
            } else {
                document.getElementById('driver-bookings').innerHTML = '<div class="status-box status-info">No active booking requests. Waiting for new requests...</div>';
            }
        } else {
            document.getElementById('driver-bookings').innerHTML = '<div class="status-box status-info">No booking requests at the moment. Waiting for requests...</div>';
        }
    } catch (error) {
        showStatus('driver-bookings', `❌ Error: ${error.message}`, 'error');
    }
}

function startDriverBookingsPolling() {
    // Clear any existing interval
    if (driverBookingsInterval) {
        clearInterval(driverBookingsInterval);
    }
    
    // Poll every 3 seconds
    driverBookingsInterval = setInterval(() => {
        getDriverBookings();
    }, 3000);
    
    // Also check immediately
    getDriverBookings();
}

function stopDriverBookingsPolling() {
    if (driverBookingsInterval) {
        clearInterval(driverBookingsInterval);
        driverBookingsInterval = null;
    }
}

function selectBookingForAccept(bookingId) {
    // Clear previous status messages
    clearStatus('accept-status');
    clearStatus('driver-bookings');
    
    document.getElementById('accept-booking-id').value = bookingId;
    showStep('driver-accept');
}

function selectBookingForRide(bookingId) {
    appState.currentBooking = bookingId;
    document.getElementById('start-booking-id').value = bookingId;
    showStep('driver-ride');
}

async function acceptBooking() {
    // Clear previous status messages
    clearStatus('accept-status');
    
    const data = {
        driver_id: document.getElementById('accept-driver-id').value || appState.currentDriver,
        booking_id: document.getElementById('accept-booking-id').value
    };

    // Validate booking ID
    if (!data.booking_id) {
        showStatus('accept-status', `❌ Please select a booking to accept`, 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/driver/accept`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            appState.currentBooking = data.booking_id;
            showStatus('accept-status', 
                `✅ Booking accepted!<br>
                <strong>Passenger:</strong> ${result.passenger?.name || 'N/A'}<br>
                <strong>Phone:</strong> ${result.passenger?.phone_number || 'N/A'}<br>
                <p style="margin-top: 10px;">⏳ Waiting for passenger confirmation...</p>`, 
                'success');
            
            // Start polling for passenger confirmation
            startDriverBookingStatusPolling();
        } else {
            showStatus('accept-status', `❌ ${result.message || 'Failed to accept booking'}`, 'error');
        }
    } catch (error) {
        showStatus('accept-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function declineBooking(bookingId) {
    // For now, just show a message. You can implement decline endpoint if needed
    showStatus('driver-bookings', `Booking ${bookingId} declined.`, 'info');
    setTimeout(() => getDriverBookings(), 1000);
}

let driverBookingStatusInterval = null;

function startDriverBookingStatusPolling() {
    // Clear any existing interval
    if (driverBookingStatusInterval) {
        clearInterval(driverBookingStatusInterval);
    }
    
    // Poll every 2 seconds
    driverBookingStatusInterval = setInterval(async () => {
        await checkDriverBookingStatus();
    }, 2000);
    
    // Also check immediately
    checkDriverBookingStatus();
}

function stopDriverBookingStatusPolling() {
    if (driverBookingStatusInterval) {
        clearInterval(driverBookingStatusInterval);
        driverBookingStatusInterval = null;
    }
}

async function checkDriverBookingStatus() {
    if (!appState.currentBooking || !appState.currentDriver) {
        stopDriverBookingStatusPolling();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/driver/bookings/${appState.currentDriver}`);
        const result = await response.json();
        
        if (result.success && result.bookings) {
            const booking = result.bookings.find(b => b.booking_id === appState.currentBooking);
            if (booking) {
                if (booking.status === 'confirmed') {
                    stopDriverBookingStatusPolling();
                    showStep('driver-ride');
                    showStatus('ride-action-status', '✅ Passenger confirmed! You can start the ride.', 'success');
                } else if (booking.status === 'in_progress') {
                    stopDriverBookingStatusPolling();
                    showStep('driver-ride');
                    showStatus('ride-action-status', '🚗 Ride is in progress.', 'success');
                } else if (booking.status === 'completed') {
                    stopDriverBookingStatusPolling();
                    showStep('driver-ride');
                    showStatus('ride-action-status', '✅ Ride completed!', 'success');
                } else if (booking.status === 'cancelled') {
                    stopDriverBookingStatusPolling();
                    showStatus('accept-status', '❌ Booking was cancelled by passenger.', 'error');
                }
                // If still driver_accepted, continue polling
            }
        }
    } catch (error) {
        console.error('Error checking booking status:', error);
    }
}

async function startRide() {
    // Clear previous status messages
    clearStatus('ride-action-status');
    
    const data = {
        driver_id: document.getElementById('start-driver-id').value || appState.currentDriver,
        booking_id: document.getElementById('start-booking-id').value || appState.currentBooking
    };

    try {
        const response = await fetch(`${API_BASE}/driver/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            showStatus('ride-action-status', `✅ Ride started!`, 'success');
            
            // Get booking details to show driver → destination route
            try {
                const bookingResponse = await fetch(`${API_BASE}/passenger/booking/${data.booking_id}`);
                const bookingResult = await bookingResponse.json();
                
                if (bookingResult.success && bookingResult.booking) {
                    const booking = bookingResult.booking;
                    
                    // Get current driver location
                    fetch(`${API_BASE}/debug/data`)
                        .then(res => res.json())
                        .then(debugData => {
                            const drivers = debugData.drivers || {};
                            const driver = drivers[data.driver_id];
                            
                            if (booking.dropoff_location) {
                                if (driver && driver.current_location) {
                                    // Show driver → destination route
                                    showRideInProgress(
                                        { lat: driver.current_location.latitude, lon: driver.current_location.longitude },
                                        { lat: booking.dropoff_location.latitude, lon: booking.dropoff_location.longitude }
                                    );
                                } else if (booking.pickup_location) {
                                    // Fallback: use pickup as driver location
                                    showRideInProgress(
                                        { lat: booking.pickup_location.latitude, lon: booking.pickup_location.longitude },
                                        { lat: booking.dropoff_location.latitude, lon: booking.dropoff_location.longitude }
                                    );
                                }
                            }
                        })
                        .catch(err => console.error('Error getting driver location:', err));
                }
            } catch (err) {
                console.error('Error fetching booking details:', err);
            }
        } else {
            showStatus('ride-action-status', `❌ ${result.message || 'Failed to start ride'}`, 'error');
        }
    } catch (error) {
        showStatus('ride-action-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function completeRide() {
    // Clear previous status messages
    clearStatus('ride-action-status');
    
    const data = {
        driver_id: appState.currentDriver,
        booking_id: appState.currentBooking,
        dropoff_latitude: 28.7041, // You can add input for this
        dropoff_longitude: 77.1025
    };

    try {
        const response = await fetch(`${API_BASE}/driver/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            showStatus('ride-action-status', 
                `✅ Ride completed!<br>
                <strong>Final Fare:</strong> ₹${result.final_fare || 'N/A'}`, 
                'success');
        } else {
            showStatus('ride-action-status', `❌ ${result.message || 'Failed to complete ride'}`, 'error');
        }
    } catch (error) {
        showStatus('ride-action-status', `❌ Error: ${error.message}`, 'error');
    }
}

// Leaflet Map Integration with OpenRouteService
let map = null;
let passengerMarker = null;
let driverMarker = null;
let routeLayer = null;

// Initialize Leaflet Map
function initializeMap(centerLat = 28.6139, centerLon = 77.2090) {
    const mapContainer = document.getElementById('google-map');
    if (!mapContainer || typeof L === 'undefined') {
        console.warn('Leaflet.js not available');
        return;
    }
    
    if (map) {
        // Map already initialized, just update center
        map.setView([centerLat, centerLon], 13);
        return;
    }
    
    try {
        // Initialize Leaflet map
        map = L.map(mapContainer).setView([centerLat, centerLon], 13);
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);
        
        console.log('Leaflet map initialized');
    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

// Wait for API key to be loaded (with timeout)
async function waitForApiKey(maxWait = 3000) {
    const startTime = Date.now();
    while (!window.ORS_API_KEY && (Date.now() - startTime) < maxWait) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    return !!window.ORS_API_KEY;
}

/**
 * Shows the route from pickup to destination, and optionally plots nearby drivers.
 * @param {Object} pickup - {lat, lon} of the passenger/pickup point.
 * @param {Object} destination - {lat, lon} of the final destination.
 * @param {Array} [nearbyDrivers=[]] - Array of driver objects returned by the API.
 */
async function showPickupToDestination(pickup, destination, nearbyDrivers = []) {
    const mapWrapper = document.getElementById('map-container-wrapper');
    if (!mapWrapper) return;
    
    mapWrapper.style.display = 'block';
    
    // Wait for API key to be loaded
    if (!window.ORS_API_KEY) {
        await waitForApiKey();
    }
    
    // Initialize map if not already done
    if (!map) {
        const centerLat = (pickup.lat + destination.lat) / 2;
        const centerLon = (pickup.lon + destination.lon) / 2;
        initializeMap(centerLat, centerLon);
    }
    
    if (!map || typeof L === 'undefined') {
        return;
    }
    
    try {
        // Clear existing route and destination marker
        if (routeLayer) map.removeLayer(routeLayer);
        
        // Clear old markers for dynamic update
        if (window.taxiMarkers) {
            window.taxiMarkers.forEach(m => map.removeLayer(m));
            window.taxiMarkers = [];
        }
        
        // Clear existing passenger and driver markers
        if (passengerMarker) map.removeLayer(passengerMarker);
        if (driverMarker) map.removeLayer(driverMarker);
        
        // 1. Create Pickup Marker (Green Pin)
        const pickupIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #4CAF50; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">📍</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        passengerMarker = L.marker([pickup.lat, pickup.lon], { icon: pickupIcon })
            .addTo(map)
            .bindPopup('<strong>📍 Pickup Location</strong>');
        
        // 2. Create Destination Marker (Red Flag)
        const destinationIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #F44336; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🏁</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        // Use driverMarker variable for the Destination Marker
        driverMarker = L.marker([destination.lat, destination.lon], { icon: destinationIcon })
            .addTo(map)
            .bindPopup('<strong>🏁 Destination</strong>');
        
        // 3. Draw Route from pickup to destination
        await drawRouteWithORS(pickup.lat, pickup.lon, destination.lat, destination.lon);
        
        // 4. Plot Nearby Drivers (NEW)
        window.taxiMarkers = [];
        const taxiIcon = L.divIcon({
            className: 'custom-taxi-marker',
            html: '<div style="background-color: #FFC107; width: 40px; height: 40px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🚕</div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        // Fetch driver locations from /debug/data endpoint
        if (nearbyDrivers && nearbyDrivers.length > 0) {
            try {
                const debugResponse = await fetch(`${API_BASE}/debug/data`);
                const debugData = await debugResponse.json();
                
                if (debugData && debugData.drivers) {
                    nearbyDrivers.forEach(driver => {
                        const driverLocation = debugData.drivers[driver.driver_id];
                        
                        if (driverLocation && driverLocation.current_location) {
                            const driverLat = driverLocation.current_location.latitude;
                            const driverLon = driverLocation.current_location.longitude;
                            
                            const marker = L.marker([driverLat, driverLon], { icon: taxiIcon })
                                .addTo(map)
                                .bindPopup(`<strong>🚕 ${driver.driver_name || 'Driver'}</strong><br>
                                    ID: ${driver.driver_id}<br>
                                    To Pickup: ${driver.distance_text || 'N/A'}<br>
                                    Pickup ETA: ${driver.eta_text || 'N/A'}`);
                            
                            window.taxiMarkers.push(marker);
                        }
                    });
                    
                    // Recalculate bounds to include all markers (pickup, destination, and drivers)
                    const allMarkers = [passengerMarker, driverMarker, ...window.taxiMarkers];
                    if (allMarkers.length > 0) {
                        const group = new L.featureGroup(allMarkers);
                        map.fitBounds(group.getBounds().pad(0.1));
                    }
                }
            } catch (error) {
                console.error('Error fetching driver locations:', error);
                // Fallback: fit map to show pickup and destination only
                const group = new L.featureGroup([passengerMarker, driverMarker]);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        } else {
            // No drivers to show, just fit map to pickup and destination
            const group = new L.featureGroup([passengerMarker, driverMarker]);
            map.fitBounds(group.getBounds().pad(0.1));
        }
        
    } catch (error) {
        console.error('Error showing pickup to destination:', error);
    }
}

// Show driver → destination route (after ride starts)
async function showRideInProgress(driver, destination) {
    const mapWrapper = document.getElementById('map-container-wrapper');
    if (!mapWrapper) return;
    
    mapWrapper.style.display = 'block';
    
    // Wait for API key to be loaded
    if (!window.ORS_API_KEY) {
        await waitForApiKey();
    }
    
    // Initialize map if not already done
    if (!map) {
        const centerLat = (driver.lat + destination.lat) / 2;
        const centerLon = (driver.lon + destination.lon) / 2;
        initializeMap(centerLat, centerLon);
    }
    
    if (!map || typeof L === 'undefined') {
        return;
    }
    
    try {
        // Clear existing markers and route
        if (passengerMarker) map.removeLayer(passengerMarker);
        if (driverMarker) map.removeLayer(driverMarker);
        if (routeLayer) map.removeLayer(routeLayer);
        
        // Remove pickup marker (passenger already picked up)
        passengerMarker = null;
        
        // Create driver marker (yellow circle with taxi icon)
        const driverIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #FFC107; width: 40px; height: 40px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🚕</div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        driverMarker = L.marker([driver.lat, driver.lon], { icon: driverIcon })
            .addTo(map)
            .bindPopup('<strong>🚕 Driver Location</strong>');
        
        // Create destination marker (red circle with flag)
        const destinationIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #F44336; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🏁</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const destMarker = L.marker([destination.lat, destination.lon], { icon: destinationIcon })
            .addTo(map)
            .bindPopup('<strong>🏁 Destination</strong>');
        
        // Draw route from driver to destination
        await drawRouteWithORS(driver.lat, driver.lon, destination.lat, destination.lon);
        
        // Fit map to show both markers
        const group = new L.featureGroup([driverMarker, destMarker]);
        map.fitBounds(group.getBounds().pad(0.1));
        
    } catch (error) {
        console.error('Error showing ride in progress:', error);
    }
}

// Show map with passenger and driver locations using Leaflet and OpenRouteService
// This is used for driver → passenger route (before pickup)
async function showMapWithLocations(passengerLat, passengerLon, driverLat, driverLon, distance = null, eta = null) {
    const mapWrapper = document.getElementById('map-container-wrapper');
    if (!mapWrapper) return;
    
    mapWrapper.style.display = 'block';
    
    // Wait for API key to be loaded (if not already)
    if (!window.ORS_API_KEY) {
        await waitForApiKey();
    }
    
    // Initialize map if not already done
    if (!map) {
        const centerLat = (passengerLat + driverLat) / 2;
        const centerLon = (passengerLon + driverLon) / 2;
        initializeMap(centerLat, centerLon);
    }
    
    if (!map || typeof L === 'undefined') {
        // Fallback: show static message
        document.getElementById('google-map').innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f0f0f0; border-radius: 16px;">
                <div style="text-align: center; padding: 20px;">
                    <p style="color: #666; margin-bottom: 10px;">🗺️ Interactive Map</p>
                    <p style="color: #999; font-size: 12px;">Map loading...</p>
                    <p style="color: #999; font-size: 12px; margin-top: 10px;">
                        Distance: ${distance ? distance.toFixed(2) + ' km' : 'Calculating...'}<br>
                        ETA: ${eta ? Math.round(eta) + ' min' : 'Calculating...'}
                    </p>
                </div>
            </div>
        `;
        return;
    }
    
    try {
        // Clear existing markers and route
        if (passengerMarker) map.removeLayer(passengerMarker);
        if (driverMarker) map.removeLayer(driverMarker);
        if (routeLayer) map.removeLayer(routeLayer);
        
        // Create passenger marker (green circle with person icon)
        const passengerIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #4CAF50; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">👤</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        passengerMarker = L.marker([passengerLat, passengerLon], { icon: passengerIcon })
            .addTo(map)
            .bindPopup('<strong>👤 Your Location</strong>');
        
        // Create driver marker (yellow circle with taxi icon)
        const driverIcon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color: #FFC107; width: 40px; height: 40px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🚕</div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        driverMarker = L.marker([driverLat, driverLon], { icon: driverIcon })
            .addTo(map)
            .bindPopup('<strong>🚕 Driver Location</strong>');
        
        // Draw route using OpenRouteService (this will follow roads)
        await drawRouteWithORS(passengerLat, passengerLon, driverLat, driverLon, distance, eta);
        
        // Fit map to show both markers
        const group = new L.featureGroup([passengerMarker, driverMarker]);
        map.fitBounds(group.getBounds().pad(0.1));
        
    } catch (error) {
        console.error('Error showing map:', error);
        // Fallback: draw straight line
        drawStraightLine(passengerLat, passengerLon, driverLat, driverLon);
    }
}

// Draw route using OpenRouteService Directions API
async function drawRouteWithORS(startLat, startLon, endLat, endLon, distance = null, eta = null) {
    // Check if map is available before proceeding with routing
    if (!map || typeof L === 'undefined') {
        console.warn('⚠ Leaflet map not initialized, cannot request route.');
        drawStraightLine(startLat, startLon, endLat, endLon);
        return;
    }
    
    try {
        // FRONTEND FIX: Call the new backend proxy endpoint. 
        // We do NOT include the API Key in the headers here.
        const url = `${API_BASE}/api/maps/directions`;
        
        // ORS expects [lon, lat], so we prepare the body correctly
        const requestBody = {
            coordinates: [
                [startLon, startLat],  // Start: [longitude, latitude]
                [endLon, endLat]       // End: [longitude, latitude]
            ]
        };
        
        console.log('🗺️ Requesting route from backend proxy...');
        console.log('Start:', `[${startLon}, ${startLat}]`, 'End:', `[${endLon}, ${endLat}]`);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, application/geo+json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const responseText = await response.text();
        console.log('Proxy Response Status:', response.status);
        
        if (!response.ok) {
            console.error('❌ Backend Proxy Error or ORS Call Failed:', response.status);
            console.error('Error response:', responseText);
            throw new Error(`Route request failed. Status: ${response.status}. Detail: ${responseText}`);
        }
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse JSON response from proxy:', e);
            throw new Error('Invalid JSON response from map service');
        }
        
        console.log('✅ Route GeoJSON received from proxy.');
        console.log('GeoJSON structure:', JSON.stringify(data).substring(0, 500)); // Log first 500 chars for debugging
        
        // --- GeoJSON Parsing Logic ---
        // OpenRouteService GET endpoint returns GeoJSON FeatureCollection format:
        // {
        //   "type": "FeatureCollection",
        //   "features": [
        //     {
        //       "type": "Feature",
        //       "geometry": {
        //         "type": "LineString",
        //         "coordinates": [[lon, lat], [lon, lat], ...]
        //       },
        //       "properties": {
        //         "segments": [...],
        //         "summary": {
        //           "distance": ... (in meters),
        //           "duration": ... (in seconds)
        //         }
        //       }
        //     }
        //   ]
        // }
        
        let route = null;
        let geometry = null;
        let properties = null;
        
        // Handle GeoJSON FeatureCollection format (from GET endpoint)
        if (data.type === 'FeatureCollection' && data.features && Array.isArray(data.features) && data.features.length > 0) {
            route = data.features[0];
            geometry = route.geometry;
            properties = route.properties;
            console.log('✅ Parsed GeoJSON FeatureCollection format');
        }
        // Handle single Feature format
        else if (data.type === 'Feature' && data.geometry) {
            route = data;
            geometry = data.geometry;
            properties = data.properties;
            console.log('✅ Parsed GeoJSON Feature format');
        }
        // Handle direct geometry (fallback)
        else if (data.geometry) {
            geometry = data.geometry;
            properties = data.properties || {};
            route = { geometry, properties };
            console.log('✅ Parsed direct geometry format');
        }
        else {
            console.error('❌ Unexpected GeoJSON response format:', data);
            console.error('Response type:', data.type);
            console.error('Has features:', !!data.features);
            console.error('Has geometry:', !!data.geometry);
            throw new Error('Unexpected GeoJSON format - expected FeatureCollection, Feature, or geometry');
        }
        
        // Validate and parse LineString geometry
        if (!geometry || geometry.type !== 'LineString') {
            console.error('❌ Invalid geometry type:', geometry?.type || 'missing');
            throw new Error(`Invalid geometry type: expected LineString, got ${geometry?.type || 'none'}`);
        }
        
        if (!Array.isArray(geometry.coordinates)) {
            console.error('❌ Invalid coordinates format:', geometry.coordinates);
            throw new Error('Coordinates must be an array');
        }
        
        // Convert GeoJSON coordinates [lon, lat] to Leaflet format [lat, lon]
        let latlngs = geometry.coordinates
            .filter(coord => Array.isArray(coord) && coord.length >= 2)
            .map(coord => [coord[1], coord[0]]); // Convert [lon, lat] to [lat, lon] for Leaflet
        
        if (latlngs.length === 0) {
            console.error('❌ No valid coordinates found in route geometry');
            throw new Error('No valid coordinates in route geometry');
        }
        
        console.log(`✅ Parsed ${latlngs.length} coordinate points from GeoJSON`);
        
        // Remove existing route layer if any
        if (routeLayer) {
            map.removeLayer(routeLayer);
            routeLayer = null;
        }
        
        // Draw route polyline with road-following path
        routeLayer = L.polyline(latlngs, {
            color: '#FFC107',
            weight: 5,
            opacity: 0.8,
            smoothFactor: 1.0
        }).addTo(map);
        
        console.log(`✅ Route drawn successfully following roads with ${latlngs.length} points!`);
        
        // Extract distance and duration from route properties
        let routeDistance = null;
        let routeDuration = null;
        
        if (properties) {
            // Try to get from summary first (most common format)
            if (properties.summary) {
                routeDistance = (properties.summary.distance || 0) / 1000; // Convert meters to km
                routeDuration = (properties.summary.duration || 0) / 60; // Convert seconds to minutes
                console.log('✅ Extracted distance/duration from properties.summary');
            }
            // Try segments format
            else if (properties.segments && Array.isArray(properties.segments) && properties.segments.length > 0) {
                const segment = properties.segments[0];
                if (segment.distance) routeDistance = (segment.distance || 0) / 1000;
                if (segment.duration) routeDuration = (segment.duration || 0) / 60;
                console.log('✅ Extracted distance/duration from properties.segments');
            }
        }
        
        // Update map info display
        const distanceEl = document.getElementById('map-distance');
        const etaEl = document.getElementById('map-eta');
        const mapInfo = document.getElementById('map-info');
        
        if (routeDistance !== null && distanceEl) {
            distanceEl.textContent = routeDistance.toFixed(2) + ' km';
            console.log(`✅ Distance updated: ${routeDistance.toFixed(2)} km`);
        } else if (distance !== null && distanceEl) {
            distanceEl.textContent = distance.toFixed(2) + ' km';
        }
        
        if (routeDuration !== null && etaEl) {
            etaEl.textContent = Math.round(routeDuration) + ' min';
            console.log(`✅ Duration updated: ${Math.round(routeDuration)} min`);
        } else if (eta !== null && etaEl) {
            etaEl.textContent = Math.round(eta) + ' min';
        }
        
        if (mapInfo && (routeDistance !== null || routeDuration !== null || distance !== null || eta !== null)) {
            mapInfo.style.display = 'block';
        }
    } catch (error) {
        console.error('❌ Final route drawing failed:', error);
        console.error('Error details:', error.message);
        console.warn('⚠ Falling back to straight line');
        drawStraightLine(startLat, startLon, endLat, endLon);
        
        // Show distance/ETA from parameters
        if (distance !== null) {
            const distanceEl = document.getElementById('map-distance');
            if (distanceEl) distanceEl.textContent = distance.toFixed(2) + ' km';
        }
        if (eta !== null) {
            const etaEl = document.getElementById('map-eta');
            if (etaEl) etaEl.textContent = Math.round(eta) + ' min';
        }
        const mapInfo = document.getElementById('map-info');
        if (mapInfo && (distance !== null || eta !== null)) {
            mapInfo.style.display = 'block';
        }
    }
}

// Draw straight line between two points (fallback)
function drawStraightLine(lat1, lon1, lat2, lon2) {
    if (!map || typeof L === 'undefined') return;
    
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    routeLayer = L.polyline(
        [[lat1, lon1], [lat2, lon2]],
        {
            color: '#FFC107',
            weight: 5,
            opacity: 0.8,
            dashArray: '10, 5'
        }
    ).addTo(map);
}

// Update map with new locations
function updateMapLocations(passengerLat, passengerLon, driverLat, driverLon) {
    if (map) {
        showMapWithLocations(passengerLat, passengerLon, driverLat, driverLon);
    }
}

// Hide map
function hideMap() {
    const mapWrapper = document.getElementById('map-container-wrapper');
    if (mapWrapper) {
        mapWrapper.style.display = 'none';
    }
}

// Wait for maps config to load before initializing app
async function waitForMapsConfig(maxWait = 5000) {
    const startTime = Date.now();
    // Wait for mapsLoaded flag to be set (with timeout)
    while (!window.mapsLoaded && !window.ORS_API_KEY && (Date.now() - startTime) < maxWait) {
        await new Promise(r => setTimeout(r, 50));
    }
    
    if (window.ORS_API_KEY || window.mapsLoaded) {
        console.log('✅ Maps config ready, initializing app...');
    } else {
        console.warn('⚠ Maps config wait timeout. Proceeding without API key.');
    }
}

// Initialize app after maps config is loaded
window.onload = async function() {
    // Wait for maps config to be loaded first
    await waitForMapsConfig();
    
    // Verify API key is available
    if (window.ORS_API_KEY) {
        console.log('✅ OpenRouteService API key confirmed:', window.ORS_API_KEY.substring(0, 10) + '...');
    } else {
        console.warn('⚠ OpenRouteService API key not available. Routes will use straight lines.');
    }
    
    showScreen('role-selection');
    
    // OpenRouteService API key is loaded from backend in index.html
    // Can be overridden here if needed:
    // window.ORS_API_KEY = 'your_api_key_here';
};