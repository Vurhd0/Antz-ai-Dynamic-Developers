# Fare & Cancellation Fee Calculation - Complete Explanation

## 📊 Fare Calculation

### Formula
```
Fare = (Base Fare + (Distance × Rate per KM) + (Time × Rate per Minute)) × Surge Multiplier
```

### Components

#### 1. Base Fare
- **Fixed amount**: ₹50 (from `Config.BASE_FARE`)
- Charged regardless of distance/time

#### 2. Distance Component
- **Rate**: ₹10 per kilometer (from `Config.RATE_PER_KM`)
- **Calculation**: Uses Haversine formula to calculate straight-line distance between:
  - **For booking**: Driver's current location → Passenger pickup location
  - **For completion**: Pickup location → Dropoff location (if different)

#### 3. Time Component
- **Rate**: ₹2 per minute (from `Config.RATE_PER_MIN`)
- **Time**: Estimated time based on distance and average speed (40 km/h)
- Formula: `Time (minutes) = (Distance / 40 km/h) × 1.3 × 60`
- The 1.3 multiplier accounts for traffic delays

#### 4. Surge Multiplier
Dynamic pricing based on demand/supply ratio:

**Ratio = Number of Passengers / Number of Available Drivers**

| Ratio Range | Surge Multiplier | Description |
|------------|------------------|-------------|
| < 1.0 | 1.0x | No surge (more drivers than passengers) |
| 1.0 - 1.5 | 1.2x - 1.4x | Mild surge (gradual increase) |
| 1.5 - 1.8 | 1.5x - 1.8x | Medium surge |
| ≥ 1.8 | 2.0x | High surge (maximum allowed by government) |

**Example Calculation:**
- Base Fare: ₹50
- Distance: 15 km → ₹150 (15 × ₹10)
- Time: 30 minutes → ₹60 (30 × ₹2)
- Subtotal: ₹260
- Surge: 1.5x (medium demand)
- **Final Fare: ₹390** (₹260 × 1.5)

---

## ❌ Cancellation Fee Calculation

### Formula
```
Cancellation Fee = Max(Base Fee, Category Fee) × (1 + GST)
```

### Step-by-Step Process

#### Step 1: Calculate Base Fee
```
Base Fee = Min(10% of Total Fare, ₹100)
```
- Takes 10% of the booking fare
- Capped at maximum ₹100
- Example: If fare is ₹500, base fee = ₹50 (10% of 500)
- Example: If fare is ₹2000, base fee = ₹100 (capped at max)

#### Step 2: Determine Category Fee (Time-Based)
Based on vehicle type and time elapsed since booking:

| Vehicle Type | Category Fee | Time Threshold |
|-------------|--------------|----------------|
| Hatchback | ₹60 | After 5 minutes |
| Sedan | ₹90 | After 5 minutes |
| SUV | ₹100 | After 5 minutes |
| Premium | ₹90 | After 5 minutes |

**Time Calculation:**
- Time elapsed = Current time - Booking creation time
- If time < 5 minutes: Category fee = ₹0
- If time ≥ 5 minutes: Category fee applies

#### Step 3: Select Higher Fee
```
Final Fee Before GST = Max(Base Fee, Category Fee)
```
- Takes whichever is higher
- Example: Base fee ₹50, Category fee ₹90 → Use ₹90

#### Step 4: Add GST
```
Final Cancellation Fee = Final Fee Before GST × (1 + 0.06)
```
- Adds 6% GST to the fee
- Example: ₹90 × 1.06 = ₹95.40

### Complete Example

**Scenario:** Passenger cancels a Sedan booking after 6 minutes
- Original Fare: ₹300
- Base Fee: Min(10% of ₹300, ₹100) = ₹30
- Category Fee: ₹90 (Sedan, after 5 minutes)
- Fee Before GST: Max(₹30, ₹90) = ₹90
- **Final Cancellation Fee: ₹95.40** (₹90 + 6% GST)

---

## 📏 Distance Calculation

### Method: Haversine Formula
Calculates the great-circle distance between two points on Earth using their latitude and longitude.

**Formula:**
```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
Distance = R × c
```
Where:
- R = Earth's radius (6,371 km)
- lat1, lon1 = Pickup location coordinates
- lat2, lon2 = Dropoff location coordinates

### When Distance is Calculated

1. **During Booking Creation:**
   - Calculates: Driver location → Passenger pickup location
   - Used for: Initial fare estimation

2. **During Ride Completion:**
   - Calculates: Pickup location → Actual dropoff location
   - Used for: Final fare calculation (if dropoff differs from original)

3. **For Nearby Taxis:**
   - Calculates: Passenger location → Each driver's location
   - Used for: Sorting drivers by ETA

---

## 🔧 Current Issues & Fixes

### Issue: "N/A km" Display
**Problem:** Some bookings show "N/A" for distance because:
- Distance wasn't calculated during booking creation
- Dropoff location wasn't provided initially
- Booking was created before distance calculation was implemented

**Solution:**
- Always calculate distance from pickup to dropoff locations when displaying
- If dropoff is missing, calculate from pickup to driver location
- Fallback to stored distance_km if available

---

## 📝 Configuration Values

All values are configurable in `config.py`:

```python
BASE_FARE = 50.0              # ₹50
RATE_PER_KM = 10.0            # ₹10/km
RATE_PER_MIN = 2.0            # ₹2/min

# Cancellation
CANCELLATION_FARE_PERCENTAGE = 0.10  # 10%
CANCELLATION_FARE_MAX = 100.0        # ₹100 max
CANCELLATION_FEE_HATCHBACK = 60.0    # ₹60
CANCELLATION_FEE_SEDAN = 90.0        # ₹90
CANCELLATION_FEE_SUV = 100.0          # ₹100
CANCELLATION_FEE_PREMIUM = 90.0      # ₹90
CANCELLATION_TIME_THRESHOLD = 5      # 5 minutes
GST_RATE = 0.06                      # 6% GST
```

---

## 🎯 Summary

1. **Fare** = Base + (Distance × Rate) + (Time × Rate) × Surge
2. **Cancellation Fee** = Max(10% of Fare or ₹100, Category Fee) × 1.06
3. **Distance** = Calculated using Haversine formula from GPS coordinates
4. **Surge** = Based on passenger/driver ratio (1.0x to 2.0x)

All calculations are done server-side to ensure accuracy and prevent manipulation.

