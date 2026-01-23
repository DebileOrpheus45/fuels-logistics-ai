# Frontend Comparison: Base_v1 vs MGClone_v1

Quick visual comparison of the two available frontends.

---

## At a Glance

| Feature | Base_v1 | MGClone_v1 |
|---------|---------|------------|
| **Port** | 5173 | 5174 |
| **Folder** | `frontend/` | `MGClone_v1/` |
| **Style** | Modern SaaS | Enterprise TMS |
| **Navigation** | Top tabs | Left sidebar |
| **Layout** | Card-based | Table-based |
| **Colors** | Blue/gray, bright | Deep blue gradients |
| **Best For** | Daily ops, mobile | Dashboards, presentations |
| **Learning Curve** | Easy | Moderate |
| **Data Density** | Lower (more whitespace) | Higher (compact tables) |
| **Mobile Friendly** | ✅ Yes | ⚠️ Desktop-optimized |

---

## Visual Design Comparison

### Color Schemes

**Base_v1:**
```
Primary: #3b82f6 (bright blue)
Background: White with light gray (#f9fafb)
Accents: Green, orange, red for status
Cards: White with subtle shadows
Feel: Clean, modern, airy
```

**MGClone_v1:**
```
Primary: #1e3a8a (deep blue)
Gradients: Blue to darker blue
Background: Light gray (#f9fafb)
Accents: TMS-style status colors
Tables: Striped rows, bordered
Feel: Professional, enterprise, command center
```

---

## Navigation Comparison

### Base_v1 - Top Tabs
```
┌─────────────────────────────────────────────────────────┐
│  [Dashboard] [Sites] [Loads] [Agents] [Escalations]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Content area with cards and stats                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### MGClone_v1 - Left Sidebar
```
┌────────┬──────────────────────────────────────────────┐
│ 📊 CT  │  [Header with gradient]                     │
│ 🚚 Load│                                              │
│ 🏢 Site│  Content area with tables and KPIs          │
│ 🤖 Agnt│                                              │
│ ⚠️  Esc │                                              │
│        │                                              │
│ [User] │                                              │
└────────┴──────────────────────────────────────────────┘
```

---

## Dashboard Comparison

### Base_v1 Dashboard
**Layout:**
- Top: Stats cards in a row (6 cards)
- Below: Tab content (Dashboard/Sites/Loads/Agents/Escalations)
- Dashboard tab: Recent activity feed, agent cards, site cards grid

**Stats Display:**
- Large cards with icons
- Numbers centered
- Click to filter relevant tab

**Activity Feed:**
- Vertical timeline
- Grouped by agent
- Expandable email content

### MGClone_v1 Control Tower
**Layout:**
- Top: KPI cards in a row (6 cards, smaller)
- Always visible across all views
- Main area: Priority-based sections
  1. Priority Actions Required (critical items first)
  2. Active Loads table
  3. View-specific content below

**Stats Display:**
- Compact KPI cards
- Trend indicators (↑ ↓)
- Click to switch view

**Priority View:**
- Critical escalations at top
- At-risk sites next
- Everything organized by urgency

---

## Sites View Comparison

### Base_v1
```
Filter: [All] [At Risk] [Critical] [OK]

┌─────────┐ ┌─────────┐ ┌─────────┐
│ Site 1  │ │ Site 2  │ │ Site 3  │
│ ⭕ 65%   │ │ ⭕ 30%   │ │ ⭕ 85%   │
│ 36 hrs  │ │ 18 hrs  │ │ 96 hrs  │
│ [Edit]  │ │ [Edit]  │ │ [Edit]  │
└─────────┘ └─────────┘ └─────────┘
```
- Grid layout (3-4 columns)
- Large fuel gauges
- Lots of whitespace
- Edit button on each card

### MGClone_v1
```
┌─────────────────────────────────────┐
│ Critical Sites (2)                  │
├─────────────────────────────────────┤
│ ┌───────────────────────────────┐   │
│ │ Site 1  | 30% | 18 hrs        │   │
│ │ [Progress bar]                │   │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ At Risk Sites (3)                   │
├─────────────────────────────────────┤
│ [Similar layout]                    │
└─────────────────────────────────────┘
```
- Sectioned by health status
- Smaller cards, more per row
- Progress bars instead of gauges
- Auto-grouped by severity

---

## Loads View Comparison

### Base_v1
```
Status Filter: [All] [In Transit] [Scheduled]

PO-001  | Site A    | Carrier X  | 10,000 gal | Jan 18, 3pm
PO-002  | Site B    | Carrier Y  | 8,500 gal  | Jan 18, 5pm
PO-003  | Site C    | Carrier X  | 12,000 gal | Jan 19, 9am
```
- Simple list/cards
- Status badges
- Less dense
- Easier to scan for specific load

### MGClone_v1 (Load Board)
```
Search: [______________________] [Filter]

┌──────────────────────────────────────────────────────────┐
│ Status | PO    | Dest     | Carrier  | Vol    | ETA     │
├──────────────────────────────────────────────────────────┤
│ 🟡 TRN | PO001 | Site A   | Carrier  | 10,000 | 3pm     │
│        |       | Terminal | X        |        | Upd:1pm │
├──────────────────────────────────────────────────────────┤
│ 🔵 SCH | PO002 | Site B   | Carrier  | 8,500  | 5pm     │
│        |       | Terminal | Y        |        | Upd:2pm │
└──────────────────────────────────────────────────────────┘
```
- Searchable table
- Stacked columns (no horizontal scroll)
- More data visible at once
- Primary/secondary info stacked

---

## Escalations View Comparison

### Base_v1
```
Open Escalations (4)

⚠️  CRITICAL | Runout Risk
    Site A will run out in 8 hours
    [View Details]

🟧 HIGH | Late Delivery
    PO-123 ETA delayed 4 hours
    [View Details]
```
- Card-based list
- Large priority badges
- Vertical layout
- More spacing

### MGClone_v1
```
Open Escalations (4)

│ ⚠️  CRITICAL | Runout Risk | Site A will run...  | Jan 18 →
├──────────────────────────────────────────────────────────┤
│ 🟧 HIGH     | Late Del    | PO-123 ETA delay... | Jan 18 →
├──────────────────────────────────────────────────────────┤
```
- Table with left border colors
- Compact rows
- More escalations visible
- Priority color bar on left edge

---

## Agent Monitor Comparison

### Base_v1
```
┌─────────────────────────────┐
│ Agent 1                     │
│ Status: Active              │
│ Sites: 5                    │
│                             │
│ [Start] [Stop] [Run Check]  │
│ [Manage Sites]              │
│                             │
│ Activity Log:               │
│ - Email sent at 2pm         │
│ - Check completed at 1:45pm │
│ - Escalation created 1:30pm │
└─────────────────────────────┘
```
- Large agent cards
- Activity timeline below
- Separate cards per agent
- More visual hierarchy

### MGClone_v1
```
┌──────────────────────────────────────────────────┐
│ 🤖 Agent 1              [ACTIVE]                 │
├──────────────────────────────────────────────────┤
│ Sites: 5  | Interval: 15min | Last: Jan 18 2pm  │
│                                                  │
│                    [⏸️ Stop] [🔄 Run Check Now]  │
└──────────────────────────────────────────────────┘
```
- Compact agent summary
- KPI-style metrics
- Buttons on the right
- Less scrolling needed

---

## Use Case Recommendations

### Use Base_v1 When:
✅ First time using the system
✅ Working on mobile/tablet
✅ Need to see fewer items at once (less overwhelming)
✅ Prefer modern SaaS aesthetics
✅ Training new users
✅ Quick tasks and spot checks
✅ Team prefers visual simplicity

### Use MGClone_v1 When:
✅ Monitoring many items simultaneously
✅ Presenting to executives or stakeholders
✅ Users are familiar with MercuryGate or similar TMS
✅ Working on large desktop monitors
✅ Need "control tower" / NOC view
✅ Want professional enterprise look
✅ Data density is important (see more at once)
✅ Managing high-volume operations

---

## Performance

Both frontends have identical performance characteristics:
- Same React Query caching
- Same API calls
- Same data refresh intervals
- ~Equal bundle size
- No measurable speed difference

**Winner:** Tie

---

## Feature Parity

Both frontends support:
- ✅ Dashboard stats and KPIs
- ✅ Site viewing and editing
- ✅ Load tracking
- ✅ AI agent management
- ✅ Escalation handling
- ✅ Site assignment to agents
- ✅ Batch CSV upload
- ✅ Real-time data updates

**Winner:** Tie

---

## Switching Between Frontends

### Live Switching (Both Running)
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload

# Terminal 2: Base_v1
cd frontend && npm run dev

# Terminal 3: MGClone_v1
cd MGClone_v1 && npm run dev

# Browser:
# Tab 1: http://localhost:5173 (Base_v1)
# Tab 2: http://localhost:5174 (MGClone_v1)
```

Toggle between browser tabs to compare live!

### One at a Time
Just start whichever frontend you want to use. Stop it (Ctrl+C) and start the other if you want to switch.

---

## Summary

**Base_v1 = Modern & Friendly**
- Best for daily operations
- Easier learning curve
- Mobile-friendly
- Consumer SaaS feel

**MGClone_v1 = Professional & Dense**
- Best for monitoring at scale
- Control tower aesthetics
- Enterprise TMS feel
- More data visible

**Both are fully functional. Choose based on your preference and use case!**

---

**See Also:**
- [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) - Detailed switching instructions
- [USER-GUIDE.md](USER-GUIDE.md) - User guide with frontend selection
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture for both
