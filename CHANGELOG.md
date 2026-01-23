# Changelog

All notable changes to the Fuels Logistics AI Coordinator project.

## [0.1.0] - 2026-01-18

### Added - Dual Frontend System

#### New Frontend: MGClone_v1
- Created MercuryGate TMS-inspired frontend (`MGClone_v1/`)
- Runs on port 5174 (Base_v1 remains on 5173)
- Features:
  - Left sidebar navigation (MercuryGate style)
  - Control Tower View with priority actions dashboard
  - Load Board with searchable/filterable table
  - Sites view organized by health status (Critical/At Risk/Healthy)
  - AI Agents management interface
  - Escalations view with priority sorting
  - MercuryGate-inspired color scheme (deep blues, gradients)
  - Stacked thematic columns for data display
  - Status badges matching TMS conventions
  - KPI cards with trend indicators
  - Professional enterprise TMS aesthetic

#### Design Inspiration
- Based on MercuryGate's ezVision Experience
- Control tower view for prioritized workflow
- Eliminates horizontal scrolling with stacked columns
- Intelligent information displays with custom iconography
- Speed and simplicity as core principles

#### Documentation Updates
- Created `FRONTEND-SWITCHER.md` - Complete guide for switching between frontends
- Created `MGClone_v1/README.md` - MGClone-specific documentation
- Updated `ARCHITECTURE.md` - Added dual frontend architecture section
- Updated `USER-GUIDE.md` - Added frontend selection and switching instructions
- Created `README.md` - Main project README with quick start
- Created `CHANGELOG.md` - This file

### Changed
- Original frontend remains as-is in `frontend/` directory (now referred to as Base_v1)
- Both frontends use the same backend API (no backend changes required)
- Updated all startup instructions to support frontend choice

### Technical Details

**MGClone_v1 Implementation:**
- File: `MGClone_v1/src/App.jsx` (~1200 lines)
- Custom CSS: `MGClone_v1/src/index.css` (~500 lines of MercuryGate-inspired styles)
- Same dependencies as Base_v1 (React 18, TanStack Query, Axios, Lucide icons)
- Port: 5174 (configured in `package.json`)

**CSS Features:**
- Custom classes: `.control-tower-table`, `.mg-sidebar`, `.kpi-card`, `.stacked-column`
- MercuryGate color variables (--mg-primary, --mg-secondary, --mg-accent)
- Status badge styles for TMS conventions
- Priority indicators with color bars
- Gradient headers and backgrounds
- Custom scrollbar styling

**Component Architecture:**
- View components: ControlTowerView, LoadBoardView, SitesView, AgentsView, EscalationsView
- UI components: KPICard, SiteSection, LoadDetailModal, EscalationModal, LoginScreen
- Left sidebar navigation with active state tracking
- Priority-based information hierarchy

### Resources Used

**Research:**
- MercuryGate ezVision documentation and design principles
- Web searches for MercuryGate TMS UI patterns and control tower views
- Articles on TMS design evolution

**Sources:**
- [Realizing a New Vision for TMS Design - Supply Chain 24/7](https://www.supplychain247.com/article/realizing_a_new_vision_for_tms_design/mercurygate)
- [MercuryGate Launches ezVision User Experience](https://mercurygate.com/ezvision/)
- [MercuryGate ezVision Load Board](https://mercurygate.com/blog-posts/what-is-ezvision-load-board/)

### Usage

**Starting Both Frontends:**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload

# Terminal 2: Base_v1
cd frontend && npm run dev
# Access: http://localhost:5173

# Terminal 3: MGClone_v1
cd MGClone_v1 && npm run dev
# Access: http://localhost:5174
```

**When to Use Each:**
- **Base_v1**: Daily operations, mobile-friendly, modern SaaS feel
- **MGClone_v1**: Executive dashboards, control tower monitoring, users familiar with TMS

---

## [0.0.9] - 2026-01-18 (Earlier today)

### Added
- Site constraint management (consumption_rate, min_delivery_quantity, notes)
- Batch CSV upload for site updates
- AI agent site assignment interface
- Site notes feature for coordinator annotations
- Export site template functionality

### Changed
- Database schema: Added fields to Site and AIAgent models
- API endpoints: Added batch-update, export-template, assign-sites
- Frontend modals: SiteDetailsModal, BatchUploadModal, AgentAssignmentModal

---

## [0.0.8] - 2026-01-18 (Earlier today)

### Fixed
- Database schema synchronization issues
- Backend startup and process management
- ECONNRESET errors from crashed backend

### Changed
- Reset database workflow documented
- Process lifecycle explained in USER-GUIDE.md

---

## [0.0.7] - 2026-01-18

### Added
- Cross-linkages in dashboard (clickable stat cards)
- Agent Monitor tab for HITL supervision
- Email detail viewing
- Escalation management interface

---

## [0.0.6] - 2026-01-17

### Added
- Initial MVP implementation
- FastAPI backend with PostgreSQL
- React frontend with TailwindCSS
- AI agent system with Claude integration
- Database seeding
- Docker Compose setup

---

**Format:** [Version] - YYYY-MM-DD
**Types:** Added, Changed, Deprecated, Removed, Fixed, Security
