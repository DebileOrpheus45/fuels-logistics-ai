# Load Details Sidebar - Feature Update

## What Was Added

### Interactive Load Details Sidebar
- **Click any load** in the Active Shipments table to view detailed information
- **Slide-in sidebar** from the right (covers 1/3 of screen width)
- **Interactive route map** using Leaflet.js with GPS tracking visualization
- **Comprehensive load information** including:
  - Current status & ETA
  - Interactive route map with truck location
  - Origin & destination addresses
  - Carrier and driver contact info
  - Product details (volume, type, TMS load number)
  - Collaborative notes (human + AI)
  - Timeline of events

### Sleeker Sidebar Stats Cards
- **Reduced padding**: p-6 → p-4
- **Smaller borders**: rounded-xl → rounded-lg
- **Compact icons**: h-6 w-6 → h-5 w-5
- **Tighter text**: text-3xl → text-2xl
- **Better spacing**: More condensed overall layout

### Mock GPS Tracking Data
- Added realistic GPS coordinates for in-transit loads
- Route visualization with polyline on map
- Speed and timestamp for each tracking point
- Origin and destination addresses

## Backend Changes

### Database Schema Updates
**New fields added to `loads` table:**
```python
tracking_points = Column(JSON, default=list)  # GPS tracking history
origin_address = Column(String(500))
destination_address = Column(String(500))
shipped_at = Column(DateTime)
```

**Files Modified:**
- `backend/app/models.py` - Added new columns
- `backend/app/schemas.py` - Updated LoadResponse schema

**New File Created:**
- `backend/add_tracking_data.py` - Script to populate mock GPS data

### Data Population
Mock GPS tracking data generated for all loads:
- **In-transit loads**: 30-80% route completion with realistic GPS points
- **Scheduled loads**: 0% completion (not yet shipped)
- **Speed simulation**: 55-70 mph (typical highway speeds)
- **Timestamp interpolation**: Points spaced 30 minutes apart

## Frontend Changes

### New Dependencies
```bash
npm install leaflet react-leaflet@^4.2.1 --legacy-peer-deps
```

### New Components

**LoadDetailsSidebar Component:**
- Full-screen sidebar overlay with backdrop
- Animated slide-in from right
- Interactive Leaflet map showing:
  - Route polyline (blue line)
  - GPS tracking points as markers
  - Click markers for timestamp & speed details
  - OpenStreetMap tiles
- Color-coded sections:
  - Blue: Current Status/ETA
  - White: Route Map
  - Green: Origin
  - Red: Destination
  - Purple: Carrier Info
  - Orange: Product Details
  - Gray: Notes & Timeline

**Files Modified:**
- `frontend/src/App.jsx` - Added LoadDetailsSidebar component, updated LoadsTable
- `frontend/index.html` - Added Leaflet CSS link
- `frontend/src/index.css` - Already has animation utilities

### New Icons
Added from lucide-react:
- `MapPin` - Location markers
- `Navigation` - Origin indicator
- `Phone` - Contact info
- `Package` - Product details
- `Calendar` - Timeline
- `ArrowRight` - Route direction

## Usage

### How to View Load Details
1. Go to the **Dashboard** or **Loads** tab
2. **Click anywhere on a load row** in the Active Shipments table
3. The sidebar will slide in from the right
4. **Explore the interactive map** - click on markers to see tracking details
5. **Scroll down** to see all sections
6. **Click the X button** or **click the backdrop** to close

### Map Interaction
- **Pan**: Click and drag
- **Zoom**: Scroll wheel or +/- buttons
- **View tracking details**: Click any marker on the route
- **See route**: Blue line connects all tracking points

## Technical Details

### Leaflet Map Configuration
```javascript
<MapContainer
  center={[lat, lng]}  // Dynamic based on last tracking point
  zoom={6}
  style={{ height: '256px', width: '100%' }}
>
  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
  <Polyline positions={routeLine} color="blue" weight={3} />
  {/* Markers for each tracking point */}
</MapContainer>
```

### GPS Data Structure
```json
{
  "tracking_points": [
    {
      "lat": 33.7490,
      "lng": -84.3880,
      "timestamp": "2026-01-23T18:30:00",
      "speed": 65
    }
  ],
  "origin_address": "1234 Port Blvd, Houston, TX 77002",
  "destination_address": "100 Peachtree St NE, Atlanta, GA 30303"
}
```

### Animations Used
- **Sidebar**: `animate-slideInRight` - smooth entrance
- **Backdrop**: `animate-fadeIn` - gradual overlay
- **Cards**: `hover-lift` - subtle elevation on hover
- All defined in `frontend/src/index.css`

## Sidebar Sections (Top to Bottom)

1. **Header** - PO number, status badge, close button
2. **Current Status & ETA** - Blue card with timing info
3. **Route Map** - Interactive Leaflet map (256px height)
4. **Origin** - Green card with departure details
5. **Destination** - Red card with arrival details
6. **Carrier Information** - Purple card with driver/contact
7. **Product Details** - Orange card with volume/type
8. **Collaborative Notes** - Gray card (if notes exist)
9. **Timeline** - Event history with color-coded dots

## Stats Card Updates

**Before:**
- Padding: 24px (p-6)
- Border radius: 12px (rounded-xl)
- Icon size: 24px (h-6 w-6)
- Value size: 30px (text-3xl)

**After:**
- Padding: 16px (p-4) - **33% less**
- Border radius: 8px (rounded-lg) - sleeker
- Icon size: 20px (h-5 w-5) - more proportional
- Value size: 24px (text-2xl) - better fit
- Shadow: lg → md - softer

**Result:** Cards are now **~25% more compact** while maintaining readability.

## Testing Checklist

- [x] Leaflet installed and CSS loaded
- [x] Database reset with new schema
- [x] Mock tracking data populated
- [x] Backend serving new fields
- [x] Frontend loads without errors
- [x] Click load row opens sidebar
- [x] Sidebar slides in smoothly
- [x] Map renders with OpenStreetMap tiles
- [x] Route line displays correctly
- [x] Markers show tracking points
- [x] Click markers shows popup
- [x] All sections display data
- [x] Close button works
- [x] Backdrop click closes sidebar
- [x] Stats cards are more compact
- [x] Responsive layout maintained

## Known Limitations

1. **Mock Data Only** - GPS coordinates are simulated, not real Macropoint data
2. **Linear Routes** - Route line is straight interpolation, not following actual roads
3. **Map Performance** - May be slow with 50+ tracking points (current max is 20)
4. **Mobile View** - Sidebar covers full screen on mobile (intentional for now)

## Future Enhancements

### Short Term
- Add real-time position updates (WebSocket)
- Polyline that follows actual roads (using routing API)
- Driver photo/profile
- ETA confidence indicator
- Weather along route

### Long Term
- Multiple loads on same map
- Traffic overlay
- Geofencing alerts
- Historical route playback
- Export PDF report of load details

---

**Version:** 0.2.1
**Last Updated:** January 23, 2026 @ 11:30 PM
**Feature Complete** ✓
