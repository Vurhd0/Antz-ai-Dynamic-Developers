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
    
    const data = {
        user_id: document.getElementById('search-user-id').value || appState.currentUser,
        latitude: parseFloat(document.getElementById('search-lat').value),
        longitude: parseFloat(document.getElementById('search-lon').value)
    };

    try {
        const response = await fetch(`${API_BASE}/passenger/nearby-taxis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.drivers && result.drivers.length > 0) {
            let html = `<div class="status-box status-success" style="margin-bottom: 20px;">
                ✅ Found ${result.drivers.length} nearby driver${result.drivers.length > 1 ? 's' : ''}! Select one to continue.
            </div>`;
            html += `<div style="display: grid; gap: 15px; margin-top: 20px;">`;
            result.drivers.forEach((driver, index) => {
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
                            <p><strong>📏 Distance:</strong> ${driver.distance_text || driver.distance_km + ' km'}</p>
                            <p><strong>⏱️ ETA:</strong> ${driver.eta_text || driver.eta_minutes + ' min'}</p>
                            <p><strong>⚡ Surge:</strong> ${driver.surge_multiplier || 1.0}x</p>
                        </div>
                        <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%); padding: 15px; border-radius: 8px; margin: 10px 0;">
                            <p style="margin: 0; font-size: 1.3em; font-weight: 700; color: var(--taxi-black);">
                                💰 Estimated Fare: <span style="color: var(--taxi-yellow-dark);">₹${driver.estimated_fare || 'N/A'}</span>
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
            showStatus('booking-status', 
                `✅ Booking Created!<br>
                <strong>Booking ID:</strong> ${result.booking_id}<br>
                <strong>Fare:</strong> ₹${result.booking.fare || 'N/A'}<br>
                <strong>Distance:</strong> ${result.booking.distance_km ? (typeof result.booking.distance_km === 'number' ? result.booking.distance_km.toFixed(2) : result.booking.distance_km) + ' km' : 'Calculating...'}<br>
                <strong>ETA:</strong> ${result.booking.estimated_time_minutes || 'N/A'} min<br>
                <p style="margin-top: 15px;">⏳ Waiting for driver to accept...</p>`, 
                'success');
            
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
            
            if (booking.status === 'driver_accepted' && !booking.passenger_confirmed) {
                stopBookingStatusPolling();
                showStep('passenger-confirm');
                showStatus('confirm-status', 
                    `✅ Driver has accepted! Please confirm to proceed.`, 
                    'success');
            } else if (booking.status === 'confirmed') {
                stopBookingStatusPolling();
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'in_progress') {
                stopBookingStatusPolling();
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'completed') {
                stopBookingStatusPolling();
                showStep('passenger-ride-status');
                updateRideStatus(booking);
            } else if (booking.status === 'cancelled') {
                stopBookingStatusPolling();
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

// Initialize
window.onload = function() {
    showScreen('role-selection');
};
