# Load Table Sorting & Sidebar Fix

## Changes Made

### 1. Fixed Map Z-Index Issue in Sidebar ✅

**Problem:** The Leaflet map was sliding through the blue header when scrolling in the sidebar.

**Solution:**
- Changed sidebar from `overflow-y-auto` to flexbox layout with `flex flex-col`
- Made header `flex-shrink-0` with `z-20` (higher z-index)
- Made content area `flex-1 overflow-y-auto` (scrollable but stays under header)

**Files Modified:**
- `frontend/src/App.jsx` - LoadDetailsSidebar component

**Result:** Map and all content now properly scroll under the sticky blue header.

---

### 2. Excel-Style Column Sorting ✅

**Features Added:**
- Click any column header to sort by that column
- Click again to toggle between ascending/descending
- Visual indicators show current sort state
- Sortable columns:
  - **PO #** - Alphabetical
  - **Carrier** - Alphabetical
  - **Destination** - Alphabetical by site code
  - **Volume** - Numerical (largest/smallest)
  - **ETA** - Date/time (oldest/newest)
  - **Status** - Alphabetical

**UI Enhancements:**
- Hover effect on column headers (gray background)
- Sort icons:
  - ⇅ (ArrowUpDown) - Column not sorted
  - ↑ (ArrowUp) - Sorted ascending
  - ↓ (ArrowDown) - Sorted descending
- Cursor changes to pointer on hover
- Headers are non-selectable (`select-none`)

**Technical Implementation:**

```javascript
// State
const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

// Click handler
const handleSort = (key) => {
  let direction = 'asc'
  if (sortConfig.key === key && sortConfig.direction === 'asc') {
    direction = 'desc'
  }
  setSortConfig({ key, direction })
}

// Memoized filtering and sorting
const filteredAndSortedLoads = useMemo(() => {
  // Filter by status
  let filtered = loads?.filter(load => {
    if (statusFilter === 'all') return true
    return load.status?.toLowerCase() === statusFilter.toLowerCase()
  }) || []

  // Sort by selected column
  if (sortConfig.key) {
    filtered = [...filtered].sort((a, b) => {
      // Custom comparison logic for each column type
      // Handles strings, numbers, and dates
    })
  }

  return filtered
}, [loads, statusFilter, sortConfig])
```

**Files Modified:**
- `frontend/src/App.jsx` - LoadsTable component

**New Icons Added:**
- `ArrowUp` - Ascending sort indicator
- `ArrowDown` - Descending sort indicator
- `ArrowUpDown` - Unsorted column indicator

---

## Usage

### Sorting Loads

1. Go to **Dashboard** or **Loads** tab
2. Locate the Active Shipments table
3. **Click any column header** to sort by that column:
   - First click: Sort **ascending** (A→Z, 0→9, oldest→newest)
   - Second click: Sort **descending** (Z→A, 9→0, newest→oldest)
   - Third click: Sort **ascending** again (cycles)

4. **Look for the sort arrow**:
   - ⇅ Gray icon = Not currently sorted
   - ↑ White icon = Sorted ascending (active)
   - ↓ White icon = Sorted descending (active)

### Examples

**Sort by Volume (Largest to Smallest):**
1. Click "Volume" header once → Ascending (smallest first)
2. Click "Volume" header again → Descending (largest first)

**Sort by ETA (Earliest to Latest):**
1. Click "ETA" header once → Ascending (earliest first)
2. Click "ETA" header again → Descending (latest first)

**Sort by Carrier Name:**
1. Click "Carrier" header → Alphabetical A→Z
2. Click again → Alphabetical Z→A

---

## Sort Behavior Details

### String Columns (PO #, Carrier, Destination, Status)
- Uses `localeCompare()` for proper alphabetical sorting
- Case-insensitive
- Handles null/undefined values (treated as empty strings)

### Numeric Column (Volume)
- Sorts by actual number value
- Null/undefined treated as 0
- Supports thousands (e.g., 8,500 gal)

### Date Column (ETA)
- Converts to timestamps for accurate date comparison
- Null/undefined ETAs (marked "Pending") sorted to end
- Handles time zones correctly

### Status Column
- Sorts alphabetically by status name
- Order when ascending: DELAYED → DELIVERED → IN_TRANSIT → SCHEDULED

---

## Performance Optimization

### useMemo Hook
The filtering and sorting logic is wrapped in `useMemo` to prevent unnecessary recalculations:

```javascript
const filteredAndSortedLoads = useMemo(() => {
  // Expensive filtering and sorting logic
}, [loads, statusFilter, sortConfig])
```

**Recalculates only when:**
- `loads` data changes (new loads fetched)
- `statusFilter` changes (All → Delayed, etc.)
- `sortConfig` changes (user clicks column header)

**Benefits:**
- No lag when expanding notes or clicking load rows
- Smooth sorting animations
- Better performance with 50+ loads

---

## Visual Design

### Header Styling

**Default State:**
```css
bg-gray-50 text-gray-700 cursor-pointer
```

**Hover State:**
```css
hover:bg-gray-100 transition-colors
```

**Active Sort State:**
- Icon changes from gray ⇅ to white ↑/↓
- Text stays gray (no background change)

### Icon Positioning
Icons aligned to the right of column text with 2px gap:
```jsx
<div className="flex items-center gap-2">
  <span>Column Name</span>
  {getSortIcon('column_key')}
</div>
```

---

## Future Enhancements

### Multi-Column Sorting (Layered Sort)
Currently not implemented, but foundation is ready for:
1. **Primary sort** - First column clicked
2. **Secondary sort** - Ctrl+Click on another column
3. **Tertiary sort** - Ctrl+Click on third column

Example: Sort by Status → then by ETA → then by Volume

**Implementation approach:**
```javascript
const [sortLayers, setSortLayers] = useState([])
// Store array of { key, direction } objects
// Apply sorts in reverse order (tertiary → secondary → primary)
```

### Sort Persistence
Save sort preferences to localStorage:
```javascript
useEffect(() => {
  localStorage.setItem('loadTableSort', JSON.stringify(sortConfig))
}, [sortConfig])
```

### Default Sort
Auto-sort by most urgent loads on initial load:
```javascript
const [sortConfig, setSortConfig] = useState({
  key: 'eta',
  direction: 'asc' // Earliest ETA first
})
```

---

## Testing Checklist

- [x] Click PO # header - sorts alphabetically
- [x] Click Carrier header - sorts alphabetically
- [x] Click Destination header - sorts alphabetically
- [x] Click Volume header - sorts numerically
- [x] Click ETA header - sorts by date/time
- [x] Click Status header - sorts alphabetically
- [x] Toggle ascending/descending works on all columns
- [x] Sort icons update correctly
- [x] Hover effect shows on headers
- [x] Filtering still works after sorting
- [x] Sidebar map stays under blue header when scrolling
- [x] No console errors
- [x] Performance is smooth with multiple loads

---

## Known Limitations

1. **Single-column sort only** - Can't sort by multiple columns simultaneously yet
2. **No sort persistence** - Sort resets when navigating away from table
3. **Status filter + sort** - Filtering happens before sorting (correct behavior, but worth noting)

---

**Version:** 0.2.2
**Last Updated:** January 23, 2026 @ 11:35 PM
**Features Complete** ✓
