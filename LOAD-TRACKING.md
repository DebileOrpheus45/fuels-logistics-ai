# Interactive Load Tracking Documentation

## Overview

The fuels logistics platform now includes a comprehensive interactive load tracking system that allows users to visualize shipment routes, view GPS tracking data, and access detailed load information through a slide-in sidebar interface.

## Features

### 1. Interactive Load Details Sidebar

Click any shipment in the Active Shipments table to open a detailed view that covers 1/3 of the right side of the screen.

**Sidebar Contents:**
- Customer badge (color-coded: Stark=red, Wayne=dark gray, Luthor=green)
- Interactive GPS route map
- Origin and destination addresses
- Ship time and current ETA
- Load status and details
- Collaborative notes with AI/human indicators
- Compact stats cards

**User Experience:**
- Slides in smoothly from the right
- Click backdrop to close
- Header stays fixed while content scrolls
- Map interactions (zoom, pan, marker popups)

### 2. GPS Route Visualization

**Map Technology:**
- Powered by Leaflet.js (free, open-source)
- OpenStreetMap tiles for base maps
- react-leaflet v4.2.1 for React integration

**Map Features:**
- Blue polyline showing complete route
- Clickable GPS tracking point markers
- Marker popups display:
  - Tracking point number
  - Timestamp
  - Speed (mph)
- Auto-center on current location
- Interactive zoom and pan controls

**Data Representation:**
- In-transit loads show 30-80% route completion
- Scheduled loads show route preview only
- Real US city coordinates for realistic visualization

### 3. Excel-Style Table Sorting

**Sorting Capabilities:**
- Click column headers to sort ascending/descending
- Visual indicators (↑↓) show active sort column
- Supported columns:
  - PO Number (alphabetical)
  - Carrier (alphabetical)
  - Destination (alphabetical)
  - Volume (numeric, largest/smallest)
  - ETA (chronological, oldest/newest)
  - Status (alphabetical)
  - Customer (alphabetical)

**User Interface:**
- Only active column shows arrow indicator
- Toggle between ascending/descending
- Clear visual feedback on sorted column

### 4. Multi-Field Search

Search across all load fields simultaneously:
- PO Number
- Carrier name
- Destination site code
- Status
- Volume
- Customer

**Features:**
- Real-time filtering as you type
- Case-insensitive search
- Works in combination with sorting
- Clear search with "Clear Filters" button

### 5. Customer Tagging

**Three Customers:**
- **Stark Industries** - Red badge
- **Wayne Enterprises** - Dark gray badge
- **Luthor Corp** - Green badge

**Display Locations:**
- Table row badges
- Sidebar header badge
- Color-coded for quick identification

### 6. Collaborative Notes Display

**Notes Features:**
- Always visible scrollable container
- Purple/pink gradient styling
- Individual note cards with:
  - Author name (AI agent or human user)
  - Type indicator icon (robot or user)
  - Timestamp
  - Full note text
  - Color-coded borders (purple=AI, green=human)
- Empty state message when no notes exist
- Maximum height with scrolling for long note lists

### 7. Animated Refresh

**Refresh Button:**
- Located in dashboard header
- Spinning animation during data fetching
- Animation tied to actual API request status
- Disabled during refresh to prevent double-clicks
- Shows "Refreshing..." text during operation

**Data Synchronization:**
- Automatic background refresh every 30 seconds
- Manual refresh invalidates all query caches
- Fresh data fetched from API
- No stale cache issues (forced cache busting)

## Technical Implementation

### Database Schema Extensions

**Load Model Additions:**
```python
# GPS tracking data (JSON array)
tracking_points = Column(JSON, default=list)
# [{"lat": 33.7, "lng": -84.4, "timestamp": "2024-01-24T10:30:00", "speed": 65}]

# Address information
origin_address = Column(String(500), nullable=True)
destination_address = Column(String(500), nullable=True)

# Shipment timing
shipped_at = Column(DateTime, nullable=True)

# Collaborative notes (JSON array)
notes = Column(JSON, default=list)
# [{"author": "Agent 1", "type": "ai", "text": "...", "timestamp": "..."}]
```

### Mock GPS Data Generation

**Script:** `backend/add_tracking_data.py`

**Locations Included:**

*Fuel Terminals (Origins):*
- Houston Terminal (29.7604°N, -95.3698°W)
- Atlanta Terminal (33.7490°N, -84.3880°W)
- Dallas Terminal (32.7767°N, -96.7970°W)
- Memphis Terminal (35.1495°N, -90.0490°W)
- Chicago Terminal (41.8781°N, -87.6298°W)
- Los Angeles Terminal (33.7701°N, -118.1937°W)

*Gas Station Sites (Destinations):*
- SITE001 - Downtown Atlanta
- SITE002 - Fort Worth Highway Stop
- SITE003 - Houston Suburban Center
- SITE004 - Los Angeles Airport Depot
- SITE005 - Chicago Industrial Park

**Route Interpolation:**
- Linear interpolation between origin and destination
- Random coordinate variation (±0.02°) for realistic road following
- Highway speeds (55-70 mph)
- Half-hour timestamp intervals
- Progress percentage based on load status

### API Endpoint

**GET `/api/loads/active`**

Returns all active loads with:
- Standard load fields (PO#, carrier, volume, etc.)
- GPS tracking points array
- Origin and destination addresses
- Shipped timestamp
- Collaborative notes array
- Customer information
- Related carrier and site details

**Response Format:**
```json
{
  "id": 1,
  "po_number": "PO-2024-001",
  "status": "in_transit",
  "tracking_points": [
    {
      "lat": 29.7604,
      "lng": -95.3698,
      "timestamp": "2024-01-24T08:00:00",
      "speed": 65
    }
  ],
  "origin_address": "1234 Port Blvd, Houston, TX 77002",
  "destination_address": "100 Peachtree St NE, Atlanta, GA 30303",
  "shipped_at": "2024-01-24T07:30:00",
  "notes": [
    {
      "author": "Agent 1",
      "type": "ai",
      "text": "Requested ETA update from carrier",
      "timestamp": "2024-01-24T09:00:00"
    }
  ]
}
```

### Frontend Components

**LoadDetailsSidebar (App.jsx:1726+)**
- Main sidebar component
- Leaflet map integration
- Fixed z-index layering with flexbox
- Scrollable content area
- Customer badge display
- Notes visualization

**LoadsTable (App.jsx)**
- Sortable table headers
- Search input integration
- Customer badge rendering
- Click handler for sidebar
- Clear filters functionality

**Dashboard (App.jsx:2597+)**
- React Query data fetching
- Animated refresh button
- isFetching state management
- Query cache invalidation
- Multiple query coordination

### React Query Configuration

**Cache Strategy:**
```javascript
const { data: loads, isFetching: isLoadsFetching } = useQuery({
  queryKey: ['active-loads-v2'], // Versioned for cache busting
  queryFn: getActiveLoads,
  refetchInterval: 30000,  // Auto-refresh every 30 seconds
  staleTime: 0,            // Always consider stale
  cacheTime: 0             // Don't cache between queries
})
```

**Benefits:**
- No stale data issues
- Background auto-refresh
- Manual refresh on demand
- Fresh data on component mount

## Usage Guide

### Viewing Load Details

1. Navigate to Active Shipments table on dashboard
2. Click any row in the table
3. Sidebar slides in from the right showing:
   - GPS map with route (if tracking data available)
   - Load details (PO#, carrier, volume, etc.)
   - Origin and destination addresses
   - Collaborative notes
4. Interact with map:
   - Zoom with mouse wheel or zoom controls
   - Pan by clicking and dragging
   - Click markers to see timestamp and speed
5. Click backdrop (gray area) or X button to close sidebar

### Sorting Loads

1. Click any column header in the table
2. First click: sort ascending (↑ arrow)
3. Second click: sort descending (↓ arrow)
4. Third click: remove sort (return to default)
5. Only one column sorted at a time
6. Arrow appears only on active sorted column

### Searching Loads

1. Use search box in table header
2. Type any text to filter across all fields
3. Results update in real-time
4. Search works with sorting
5. Click "Clear Filters" to reset search and sort

### Refreshing Data

1. Click refresh button in dashboard header
2. Button shows spinning animation during fetch
3. All data queries refresh simultaneously
4. Animation stops when all data loaded
5. Automatic refresh every 30 seconds in background

## Troubleshooting

### Map Not Displaying

**Symptom:** Sidebar shows "No tracking data available yet"

**Solutions:**
1. Run `python add_tracking_data.py` to generate GPS data
2. Restart backend server
3. Hard refresh browser (Ctrl+Shift+R)
4. Check browser console for errors

**Verification:**
```bash
# Test API endpoint
curl "http://localhost:8000/api/loads/active" | jq '.[0].tracking_points'
# Should return array of GPS points
```

### Leaflet Icons Not Loading

**Symptom:** Map markers appear as broken images

**Cause:** Leaflet default icon paths incorrect

**Solution:** Already fixed in code with CDN URLs:
```javascript
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})
```

### Sidebar Scrolling Over Header

**Symptom:** Map scrolls on top of blue header

**Cause:** Z-index layering issue

**Solution:** Already fixed with flexbox layout:
- Sidebar: `flex flex-col`
- Header: `flex-shrink-0 z-20`
- Content: `flex-1 overflow-y-auto`

### Stale Data After Updates

**Symptom:** Changes not appearing after refresh

**Solutions:**
1. Click refresh button (manual invalidation)
2. Wait 30 seconds (automatic refresh)
3. Hard refresh browser (Ctrl+Shift+R)
4. Check React Query dev tools

**Prevention:** Query key versioning (`active-loads-v2`) prevents persistent cache issues

### React Leaflet Version Conflict

**Symptom:** `npm install` fails with peer dependency errors

**Cause:** react-leaflet v5 requires React 19, project uses React 18

**Solution:**
```bash
npm install leaflet react-leaflet@^4.2.1 --legacy-peer-deps
```

## Performance Considerations

### Map Rendering

- Maps only render when sidebar opens
- Component unmounts when sidebar closes
- `key={load.id}` forces re-render on load change
- Prevents memory leaks from multiple map instances

### Search and Sort

- `useMemo` hook prevents unnecessary recalculations
- Only re-computes when dependencies change:
  - loads data
  - statusFilter
  - sortConfig
  - searchQuery
- Efficient for large load lists

### Data Fetching

- Background refresh every 30 seconds
- Multiple queries run in parallel
- `isFetching` state for each query
- Combined loading state for UI feedback
- No redundant API calls

## Future Enhancements

**Potential Additions:**
- [ ] Real-time GPS updates via WebSocket
- [ ] ELD integration with actual tracking providers
- [ ] Route deviation alerts
- [ ] Traffic layer overlay
- [ ] Satellite view option
- [ ] Multi-load route comparison
- [ ] Historical route playback
- [ ] Estimated vs actual route comparison
- [ ] Weather overlay on routes
- [ ] Geofencing for pickup/delivery zones

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [USER-GUIDE.md](USER-GUIDE.md) - General user guide
- [README.md](README.md) - Project overview and setup
- [GMAIL-SETUP.md](GMAIL-SETUP.md) - Email integration

---

**Last Updated:** January 24, 2026
**Version:** 0.3.0
