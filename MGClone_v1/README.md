# MGClone_v1 - MercuryGate TMS-Inspired Frontend

This is an alternative frontend for the Fuels Logistics AI Coordinator, styled after MercuryGate's ezVision Control Tower interface.

## Key Features

### MercuryGate-Inspired Design
- **Control Tower View**: Dashboard-style overview with prioritized actions
- **Stacked Thematic Columns**: Related data grouped together vertically (no horizontal scrolling)
- **Left Sidebar Navigation**: Convenient menu positioned on the left (MercuryGate style)
- **Professional Color Scheme**: Deep blues with gradient headers
- **Contextual Information**: Data displayed in primary/secondary stacks for quick scanning
- **Status Badges**: Color-coded badges for loads, agents, and escalations
- **Priority Indicators**: Left-border color bars for escalations

### Views Available
1. **Control Tower** - Priority actions dashboard with critical alerts
2. **Load Board** - Searchable/filterable table of all loads
3. **Sites** - Organized by health status (Critical/At Risk/Healthy)
4. **AI Agents** - Monitor and control agents
5. **Escalations** - Issue management with priority sorting

## Installation

```bash
# Install dependencies
npm install

# Start dev server (runs on port 5174 to avoid conflict with Base_v1)
npm run dev

# Build for production
npm run build
```

## Usage

The MGClone_v1 frontend runs on **port 5174** by default (Base_v1 uses 5173).

**Access:** http://localhost:5174
**Login:** coordinator / fuel2024

## Differences from Base_v1

| Feature | Base_v1 | MGClone_v1 |
|---------|---------|------------|
| **Layout** | Top tabs | Left sidebar navigation |
| **Style** | Card-based, modern | Table-based, enterprise TMS |
| **Port** | 5173 | 5174 |
| **Color Scheme** | Blue/gray | Deep blue gradients |
| **Dashboard** | Stats + tabs | Control tower with priority view |
| **Data Display** | Cards | Stacked columns in tables |
| **Feel** | Startup SaaS | Enterprise TMS |

## Design Inspiration

Based on MercuryGate's ezVision Experience:
- Report Dashboard portal with control-tower view
- Intelligent information displays with custom iconography
- Stacked, thematic columns to eliminate horizontal scrolling
- Speed and simplicity as core design principles

## API Compatibility

Both frontends use the same backend API. You can switch between them without any backend changes.

## Switching Frontends

See the main README.md and FRONTEND-SWITCHER.md for instructions on hotswapping between Base_v1 and MGClone_v1.
