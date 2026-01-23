# Fuels Logistics AI Coordinator - System Architecture

**Last Updated:** January 18, 2026
**Version:** 0.1.0 (MVP)

---

## Table of Contents
1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [AI Agent System](#ai-agent-system)
7. [Frontend Architecture](#frontend-architecture)
8. [Development Workflow](#development-workflow)
9. [Key Implementation Details](#key-implementation-details)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The Fuels Logistics AI Coordinator is an intelligent platform designed to automate fuel delivery logistics coordination. It replaces manual dispatcher work by using AI agents (powered by Claude) to monitor inventory levels, track shipments, communicate with carriers, and escalate critical issues to human supervisors.

**Core Capabilities:**
- Real-time inventory monitoring across multiple gas station sites
- Automated ETA requests to carriers via email
- Predictive escalation of potential runout scenarios
- Human-in-the-Loop (HITL) supervision dashboard
- Batch site constraint management

---

## Tech Stack

### Backend
- **Framework:** FastAPI 0.109.0
- **Database:** PostgreSQL 15 (via Docker)
- **ORM:** SQLAlchemy 2.0.25
- **AI:** Anthropic Claude API (anthropic >= 0.39.0)
- **Scheduler:** APScheduler 3.10.4
- **Migrations:** Alembic 1.13.1

### Frontend (Dual Options)

**Two frontends available for hotswapping:**

#### Base_v1 (Original - `frontend/`)
- **Framework:** React 18 with Vite
- **Data Fetching:** TanStack Query (React Query) v5
- **Styling:** TailwindCSS
- **Icons:** Lucide React
- **HTTP Client:** Axios
- **Port:** 5173
- **Style:** Modern, card-based SaaS interface

#### MGClone_v1 (MercuryGate-inspired - `MGClone_v1/`)
- **Framework:** React 18 with Vite
- **Data Fetching:** TanStack Query (React Query) v5
- **Styling:** TailwindCSS with custom MercuryGate-inspired CSS
- **Icons:** Lucide React
- **HTTP Client:** Axios
- **Port:** 5174
- **Style:** Enterprise TMS, table-based control tower

**Note:** Both frontends use the same backend API. See [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) for switching instructions.

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Development Server:** Uvicorn with hot-reload
- **Database Client:** psycopg2-binary

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  - Dashboard UI with tabs (Sites, Loads, Agents, etc.)     │
│  - Modal-based editing (Sites, Batch Upload, Assignment)   │
│  - Real-time stats with clickable filters                  │
│  - Agent Monitor (HITL supervision)                         │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/JSON (localhost:5173 → :8000/api)
                 ↓
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Routers                                        │   │
│  │  - /api/sites      - /api/loads                     │   │
│  │  - /api/agents     - /api/escalations               │   │
│  │  - /api/carriers   - /api/dashboard                 │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  AI Agent System                                     │   │
│  │  - CoordinatorAgent (decision-making loop)          │   │
│  │  - AgentScheduler (APScheduler jobs)                │   │
│  │  - Tool Functions (send_email, create_escalation)   │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  Integration Services (Mocked for MVP)              │   │
│  │  - EmailService (logs to Activity table)            │   │
│  │  - TMSService (simulated tracking data)             │   │
│  │  - SheetsService (future Google Sheets integration) │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────┘
                 │ SQLAlchemy ORM
                 ↓
┌─────────────────────────────────────────────────────────────┐
│           PostgreSQL Database (Docker Container)             │
│  Tables: sites, ai_agents, loads, carriers, lanes,          │
│          activities, escalations                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

#### **sites**
Represents gas stations or fuel depots being monitored.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `consignee_code` | VARCHAR(50) | Unique site identifier (e.g., "SITE001") |
| `consignee_name` | VARCHAR(255) | Human-readable name |
| `address` | TEXT | Physical location |
| `tank_capacity` | FLOAT | Total tank capacity in gallons - **CONSTRAINT** |
| `current_inventory` | FLOAT | Current fuel level in gallons - **STATE** |
| `consumption_rate` | FLOAT | Gallons consumed per hour - **CONSTRAINT** |
| `hours_to_runout` | FLOAT | Calculated time until tank is empty - **STATE** |
| `runout_threshold_hours` | FLOAT | Alert threshold (default: 48 hours) - **CONSTRAINT** |
| `min_delivery_quantity` | FLOAT | Minimum gallons per delivery - **CONSTRAINT** |
| `notes` | TEXT | Coordinator notes (e.g., "often understaffed") |
| `assigned_agent_id` | INTEGER | FK to ai_agents |
| `customer` | ENUM | Customer owner (Stark Industries, Wayne Enterprises, LuthorCorp) |
| `erp_source` | ENUM | Source system (Fuel Shepherd, FuelQuest, Manual) |
| `service_level` | ENUM | Service type (INVENTORY_AND_TRACKING, TRACKING_ONLY) |
| `last_upload_at` | DATETIME | Last time site data was updated via CSV |
| `last_inventory_update_at` | DATETIME | Last time inventory state changed - **STALENESS** |
| `inventory_staleness_threshold_hours` | INTEGER | Hours before inventory is considered stale (default: 2) |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

**Indexes:** `consignee_code` (unique), `id`

**Computed Properties (Python `@property`):**
- `is_inventory_stale` - True if `last_inventory_update_at` is older than threshold
- `inventory_staleness_hours` - Hours since last inventory update

---

#### **ai_agents**
AI coordinator instances that monitor and act on behalf of sites.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `agent_name` | VARCHAR(255) | Display name |
| `persona_type` | VARCHAR(100) | Agent type (e.g., "coordinator") |
| `status` | ENUM | ACTIVE, STOPPED, PAUSED |
| `last_activity_at` | DATETIME | Last action timestamp |
| `check_interval_minutes` | INTEGER | How often to run checks (default: 15) |
| `configuration` | JSON | Agent-specific settings (email templates, thresholds) |
| `time_aware_escalation` | BOOLEAN | Enable time-of-day escalation logic (default: True) |
| `overnight_escalation_multiplier` | FLOAT | Urgency multiplier during overnight hours (default: 1.5) |
| `overnight_start_hour` | INTEGER | When overnight period begins, 0-23 (default: 22) |
| `overnight_end_hour` | INTEGER | When overnight period ends, 0-23 (default: 6) |
| `coverage_hours` | VARCHAR(255) | Coverage pattern (e.g., "24/7", "Business Hours", "Overnight Only") |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

**Relationships:**
- `assigned_sites` → many Sites
- `activities` → many Activities
- `escalations` → many Escalations

---

#### **loads**
Fuel shipments/deliveries in the system.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `po_number` | VARCHAR(100) | Purchase order number (unique) |
| `tms_load_number` | VARCHAR(100) | Transport management system ID |
| `lane_id` | INTEGER | FK to lanes |
| `carrier_id` | INTEGER | FK to carriers |
| `destination_site_id` | INTEGER | FK to sites |
| `origin_terminal` | VARCHAR(255) | Pickup location |
| `product_type` | VARCHAR(100) | Fuel type (e.g., "Diesel", "Unleaded") |
| `volume` | FLOAT | Gallons being delivered |
| `status` | ENUM | SCHEDULED, IN_TRANSIT, DELIVERED, DELAYED, CANCELLED |
| `current_eta` | DATETIME | Latest estimated arrival time - **STATE** |
| `last_eta_update` | DATETIME | When ETA was last updated (legacy field) |
| `last_eta_update_at` | DATETIME | When ETA actually changed - **STALENESS** |
| `eta_staleness_threshold_hours` | INTEGER | Hours before ETA is considered stale (default: 4) |
| `has_macropoint_tracking` | BOOLEAN | GPS tracking available |
| `driver_name` | VARCHAR(255) | |
| `driver_phone` | VARCHAR(50) | |
| `last_email_sent` | DATETIME | Last ETA request timestamp |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | |

**Indexes:** `po_number` (unique)

**Computed Properties (Python `@property`):**
- `is_eta_stale` - True if `last_eta_update_at` is older than threshold
- `eta_staleness_hours` - Hours since last ETA update

---

#### **carriers**
Fuel transport companies.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `carrier_name` | VARCHAR(255) | Company name |
| `dispatcher_email` | VARCHAR(255) | Contact email |
| `dispatcher_phone` | VARCHAR(50) | |
| `response_time_sla_hours` | INTEGER | Expected response time (default: 4) |

---

#### **lanes**
Predefined routes between terminals and sites, assigned to specific carriers.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `site_id` | INTEGER | FK to sites |
| `carrier_id` | INTEGER | FK to carriers |
| `origin_terminal` | VARCHAR(255) | Fuel pickup location |
| `is_active` | BOOLEAN | Active route |

---

#### **activities**
Audit log of all AI agent actions with lightweight decision tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `agent_id` | INTEGER | FK to ai_agents |
| `activity_type` | ENUM | CHECK_RUN, EMAIL_SENT, ESCALATION_CREATED, STATUS_UPDATE |
| `load_id` | INTEGER | FK to loads (optional) |
| `details` | JSON | Structured data (e.g., email content, analysis) |
| `decision_code` | VARCHAR(100) | Short code describing why agent acted (e.g., "STALE_ETA_LOW_INVENTORY") |
| `decision_metrics` | JSON | Key values that triggered action (token-efficient, <100 tokens) |
| `reasoning_summary` | TEXT | Optional human-readable reasoning (generated on-demand) |
| `created_at` | DATETIME | |

**Example `details` JSON:**
```json
{
  "recipient": "dispatcher@carrier.com",
  "subject": "ETA Request for PO #12345",
  "body": "Hi, can you provide ETA update?",
  "sites_checked": 5,
  "escalations_created": 1
}
```

**Example `decision_metrics` JSON:**
```json
{
  "hours_to_runout": 18.5,
  "eta_staleness_hours": 6.2,
  "threshold_hours": 24,
  "overnight_multiplier": 1.5
}
```

---

#### **escalations**
Critical issues requiring human intervention.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `issue_type` | ENUM | RUNOUT_RISK, LATE_DELIVERY, NO_CARRIER_RESPONSE, CAPACITY_ISSUE |
| `description` | TEXT | Human-readable explanation |
| `priority` | ENUM | LOW, MEDIUM, HIGH, CRITICAL |
| `status` | ENUM | OPEN, IN_PROGRESS, RESOLVED |
| `load_id` | INTEGER | FK to loads (optional) |
| `site_id` | INTEGER | FK to sites (optional) |
| `created_by_agent_id` | INTEGER | FK to ai_agents |
| `assigned_to` | VARCHAR(255) | Human coordinator name |
| `resolution_notes` | TEXT | How the issue was resolved |
| `created_at` | DATETIME | |
| `resolved_at` | DATETIME | |
| `updated_at` | DATETIME | |

---

## Core Architecture Patterns

### Snapshot vs Constraints Philosophy

**Problem:** Traditional logistics platforms conflate configuration (what tanks CAN hold) with operational state (what's IN them now). This creates confusion when hourly exports overwrite capacity settings.

**Solution:** Separate CONSTRAINTS (static configuration) from STATE (hourly updates).

**CONSTRAINTS (Static Configuration):**
- Set once during site setup, rarely changed
- Edited via admin interface or separate configuration endpoint
- Examples: `tank_capacity`, `consumption_rate`, `runout_threshold_hours`, `min_delivery_quantity`
- Represent physical/business rules about the site

**STATE (Hourly Snapshots):**
- Updated every hour via `/api/snapshots/ingest` endpoint
- Sourced from ERP exports (Fuel Shepherd, FuelQuest, etc.)
- Examples: `current_inventory`, `hours_to_runout`, `current_eta`, `status`
- Represent current operational reality

**Implementation:**
```python
# Snapshot ingestion ONLY updates state fields
snapshot = SnapshotIngestion(
    snapshot_time=datetime.utcnow(),
    source="Fuel Shepherd CSV Export",
    customer=Customer.STARK_INDUSTRIES,
    sites=[
        SiteSnapshotState(
            site_id="SITE001",
            current_inventory=5200.0,  # STATE
            hours_to_runout=18.5       # STATE
            # tank_capacity NOT included - that's a constraint
        )
    ]
)

# Admin updates constraints separately
site.tank_capacity = 8000.0  # CONSTRAINT (via admin interface)
site.consumption_rate = 280.0  # CONSTRAINT
```

**Benefits:**
- ERP exports can't accidentally break site configuration
- Hourly ingestion is simple (just current values, no metadata)
- Staleness detection works (can tell when inventory hasn't updated)
- Google Sheets integration becomes trivial (one tab for snapshots, one for config)

---

### Staleness as Signal

**Philosophy:** In batch-first logistics, **missing updates matter more than fresh data**.

**Traditional approach:** "Site has 18 hours of fuel" → send alert
**Staleness-first approach:** "Site inventory hasn't updated in 6 hours" → investigate why

**Staleness Tracking:**

**For Sites (Inventory):**
- `last_inventory_update_at` - Timestamp of last snapshot that changed inventory
- `inventory_staleness_threshold_hours` - Site-specific threshold (default: 2 hours)
- `is_inventory_stale` - Computed property: is data older than threshold?
- `inventory_staleness_hours` - How many hours since last update

**For Loads (ETA):**
- `last_eta_update_at` - Timestamp when ETA value actually changed
- `eta_staleness_threshold_hours` - Load-specific threshold (default: 4 hours)
- `is_eta_stale` - Computed property
- `eta_staleness_hours` - How many hours since last ETA change

**Agent Decision Logic Examples:**
```python
# Bad: Just checking current values
if site.hours_to_runout < 24:
    escalate()

# Good: Checking staleness + values
if site.is_inventory_stale and site.hours_to_runout < 24:
    escalate(reason="Site data stale AND low inventory - possible system issue")

if load.is_eta_stale and load.status == "IN_TRANSIT":
    send_eta_request(reason="Truck should be moving but ETA hasn't updated in 4+ hours")
```

**Use Cases:**
- Overnight blind spot: No inventory updates between 11pm-6am? Normal for some customers
- Stuck loads: ETA unchanged for 6 hours on in-transit load? Send email
- System outages: All sites stale at once? Alert human, don't spam carriers
- Selective monitoring: Only track staleness for INVENTORY_AND_TRACKING service level

---

### Overnight Awareness

**Problem:** Traditional alerting treats 3am the same as 3pm. But overnight is when humans are blind.

**Solution:** Time-aware escalation with configurable overnight multipliers.

**Overnight Fields (AIAgent model):**
- `time_aware_escalation` - Boolean to enable/disable (default: True)
- `overnight_escalation_multiplier` - Urgency multiplier (default: 1.5x)
- `overnight_start_hour` - When overnight begins, 0-23 (default: 22 = 10pm)
- `overnight_end_hour` - When overnight ends, 0-23 (default: 6 = 6am)
- `coverage_hours` - Coverage pattern ("24/7", "Business Hours", "Overnight Only")

**Example Logic:**
```python
current_hour = datetime.now().hour
is_overnight = (current_hour >= agent.overnight_start_hour or
                current_hour < agent.overnight_end_hour)

effective_threshold = base_threshold
if agent.time_aware_escalation and is_overnight:
    effective_threshold = base_threshold * agent.overnight_escalation_multiplier

# Example: 24-hour threshold becomes 36 hours during overnight
# (because human won't see it for 8 hours anyway)
```

**Use Cases:**
- Overnight blind spot: Site runs low at 2am → escalate immediately (human can't monitor)
- Business hours: Same situation at 2pm → send email, wait for response
- Coverage gaps: Agent configured for "Overnight Only" → only acts between 10pm-6am
- Reduced noise: During business hours, agent is more patient (human is watching)

---

### Lightweight Decision Logging

**Problem:** Full LLM reasoning costs 500-1000 tokens per decision. At scale, this is expensive.

**Solution:** Log decision codes + metrics (~50-100 tokens), generate reasoning on-demand.

**Decision Logging Fields (Activity model):**
- `decision_code` - Short code (e.g., "STALE_ETA_LOW_INVENTORY")
- `decision_metrics` - JSON with key values that triggered action
- `reasoning_summary` - Optional field (generated on-demand when user clicks "explain")

**Example:**
```python
# Logged immediately (token-efficient)
activity = Activity(
    decision_code="OVERNIGHT_RUNOUT_RISK",
    decision_metrics={
        "hours_to_runout": 18.5,
        "overnight_multiplier": 1.5,
        "effective_threshold": 36.0,
        "current_hour": 23,
        "is_overnight": True
    }
)

# Generated later when user asks "why did you do this?"
# (Only costs tokens when actually needed)
reasoning_summary = generate_explanation(activity.decision_code, activity.decision_metrics)
```

**Benefits:**
- Transparency: Can always explain why agent acted
- Cost efficiency: Only pay for full reasoning when human requests it
- Debugging: Metrics show exact values that triggered decision
- Auditability: Decision codes can be aggregated for analytics

---

## API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - Summary stats (total sites, at-risk sites, active loads, etc.)

### Sites
- `GET /api/sites/` - List all sites (query params: `skip`, `limit`, `at_risk_only`)
- `GET /api/sites/{site_id}` - Get single site with loads
- `GET /api/sites/inventory-status` - Inventory summary for all sites
- `POST /api/sites/` - Create new site
- `PATCH /api/sites/{site_id}` - Update site
- `DELETE /api/sites/{site_id}` - Delete site
- `POST /api/sites/batch-update` - Bulk update site constraints from CSV
- `GET /api/sites/export-template` - Download current site data as JSON

### Agents
- `GET /api/agents/` - List all agents (query params: `status`)
- `GET /api/agents/{agent_id}` - Get agent with assigned sites
- `POST /api/agents/` - Create new agent
- `PATCH /api/agents/{agent_id}` - Update agent config
- `DELETE /api/agents/{agent_id}` - Delete agent
- `POST /api/agents/{agent_id}/start` - Start agent (set status to ACTIVE)
- `POST /api/agents/{agent_id}/stop` - Stop agent
- `POST /api/agents/{agent_id}/pause` - Pause agent
- `POST /api/agents/{agent_id}/run-check` - Manually trigger one check cycle
- `POST /api/agents/{agent_id}/assign-sites` - Bulk assign sites to agent
- `GET /api/agents/{agent_id}/activities` - Get activity log
- `POST /api/agents/{agent_id}/schedule` - Add to scheduler
- `POST /api/agents/{agent_id}/unschedule` - Remove from scheduler

### Loads
- `GET /api/loads/` - List all loads
- `GET /api/loads/active` - Get in-transit/scheduled loads
- `GET /api/loads/{load_id}` - Get single load with details
- `POST /api/loads/` - Create new load
- `PATCH /api/loads/{load_id}` - Update load
- `DELETE /api/loads/{load_id}` - Delete load

### Escalations
- `GET /api/escalations/` - List all escalations
- `GET /api/escalations/open` - Get open escalations only
- `GET /api/escalations/{id}` - Get single escalation
- `POST /api/escalations/` - Create escalation
- `PATCH /api/escalations/{id}` - Update/resolve escalation

### Carriers
- `GET /api/carriers/` - List all carriers
- `POST /api/carriers/` - Create carrier
- `PATCH /api/carriers/{id}` - Update carrier

### Emails
- `GET /api/emails/sent` - Get sent email log (from activities)

### Snapshots
- `POST /api/snapshots/ingest` - Ingest hourly snapshot of site and load state
  - **Purpose:** Update CURRENT STATE separate from configuration/constraints
  - **Request body:** `SnapshotIngestion` schema (snapshot_time, source, customer, sites[], loads[])
  - **Updates:** `current_inventory`, `hours_to_runout`, `last_inventory_update_at` for sites
  - **Updates:** `current_eta`, `status`, `driver_name`, `driver_phone`, `last_eta_update_at` for loads
  - **Staleness logic:** Only updates `last_eta_update_at` if ETA actually changed

---

## AI Agent System

### Agent Architecture

**File:** `backend/app/agents/coordinator_agent.py`

The CoordinatorAgent uses Claude's Tool Use API to:
1. Query database for site inventory and load status
2. Analyze runout risks and delivery delays
3. Decide on actions (send ETA request, create escalation, update dashboard)
4. Execute actions via tool functions

**Agent Decision Loop:**
```python
def run_agent_check(agent_id: int):
    1. Fetch agent's assigned sites from database
    2. Build context (current inventory, hours to runout, active loads)
    3. Send context to Claude with tools available:
       - send_eta_request_email(load_id, carrier_email, po_number)
       - create_escalation(issue_type, description, priority, site_id/load_id)
       - update_dashboard_note(site_id, note)
    4. Claude responds with tool calls based on analysis
    5. Execute tool calls (log to Activity table, create Escalations)
    6. Update agent's last_activity_at timestamp
    7. Return summary of actions taken
```

**Tools Available to Agent:**
- `send_eta_request_email` - Sends email to carrier (mocked, logs to activities)
- `create_escalation` - Creates escalation record in database
- `update_dashboard_note` - Adds coordinator note to site

**Escalation Triggers:**
- Site with `hours_to_runout < 12` and no active loads → CRITICAL
- Site with `hours_to_runout < 24` and no active loads → HIGH
- Load with no ETA update in 4+ hours → MEDIUM
- Carrier not responding to ETA requests → MEDIUM

---

### Agent Scheduler

**File:** `backend/app/agents/agent_scheduler.py`

Uses APScheduler to run agent checks at configured intervals.

**Key Functions:**
- `start_scheduler()` - Called on FastAPI startup
- `add_agent_job(agent_id, interval_minutes)` - Schedule an agent
- `remove_agent_job(agent_id)` - Unschedule an agent
- `get_scheduled_jobs()` - List all active jobs

**Startup Behavior:**
- On backend startup, scheduler starts
- Agents with status=ACTIVE are automatically scheduled
- Each agent runs independently at its `check_interval_minutes`

---

## Frontend Architecture

### File Structure

#### Base_v1 Frontend (`frontend/`)
```
frontend/src/
├── App.jsx              # Main application (2000+ lines)
├── api/
│   └── client.js        # Axios API client with all endpoints
├── main.jsx             # React app entry point
└── index.css            # Tailwind imports
```

**Component Breakdown (in App.jsx):**

**Utility Components:**
- `FuelGauge` - Circular gauge showing tank fill percentage
- `StatCard` - Clickable dashboard stat cards
- `LoadCard` - Display individual load with status badge
- `SiteCard` - Site inventory card with edit button and notes display
- `EscalationBanner` - Alert banner for critical escalations

**Tab Components:**
- `DashboardOverview` - Main stats and recent activity
- `SitesTab` - Grid of site cards with filtering (All, At Risk, Critical)
- `LoadsTab` - List of all loads with status filtering
- `AgentMonitorTab` - HITL supervision interface with activity logs
- `EscalationsTab` - Escalation management

**Modal Components:**
- `EscalationDetailModal` - View/resolve escalations
- `EmailDetailModal` - View sent email content
- `SiteDetailsModal` - Edit site constraints and notes
- `BatchUploadModal` - CSV upload with preview and validation
- `AgentAssignmentModal` - Multi-select site assignment to agents

---

#### MGClone_v1 Frontend (`MGClone_v1/`)
```
MGClone_v1/src/
├── App.jsx              # Main application with control tower design
├── api/
│   └── client.js        # Same Axios API client (copied from Base_v1)
├── main.jsx             # React app entry point
└── index.css            # MercuryGate-inspired custom CSS
```

**Component Breakdown (in App.jsx):**

**View Components:**
- `ControlTowerView` - Priority actions dashboard with critical alerts first
- `LoadBoardView` - Searchable table of loads (MercuryGate style)
- `SitesView` - Sites organized by health status sections
- `AgentsView` - Agent cards with control buttons
- `EscalationsView` - Priority-sorted escalations with color indicators

**UI Components:**
- `KPICard` - Dashboard KPI cards with trend indicators
- `SiteSection` - Grouped site cards by status
- `LoadDetailModal` - Load details in modal
- `EscalationModal` - Escalation details with resolution form
- `LoginScreen` - Branded login with FuelTMS ezVision theming

**Design Features:**
- Left sidebar navigation (MercuryGate style)
- Stacked thematic columns in tables (no horizontal scrolling)
- Control tower header with gradient
- Priority color bars for escalations
- Status badges matching TMS conventions
- Contextual hover tooltips (planned)

### State Management

Uses React Query for server state:
- Queries: `dashboard-stats`, `sites`, `loads`, `agents`, `escalations`, `emails`
- Mutations: `assignSite`, `resolveMutation`, `updateSite`, `batchUpload`, `assignSitesToAgent`
- Cache invalidation on mutations

Local state with `useState`:
- `activeTab` - Current tab selection
- `siteFilter` - Filter sites (all, at-risk, critical, ok)
- `selectedEscalation`, `selectedEmail`, `selectedSiteForEdit` - Modal state
- `selectedAgentForAssignment` - Agent for site assignment

### Key Features

**1. Clickable Stats Filtering**
```javascript
handleStatClick('at-risk', 'sites')
// → Sets siteFilter to 'at-risk' and switches to Sites tab
```

**2. Batch CSV Upload**
- Frontend parses CSV (comma-separated, headers required)
- Validates columns: consignee_code, tank_capacity, consumption_rate, etc.
- Shows preview table before submitting
- Backend matches by `consignee_code` and updates fields

**3. Site Assignment Interface**
- Multi-select checkboxes for assigning sites to agents
- Search/filter sites by code or name
- "Select All" / "Deselect All" buttons
- Replaces all current assignments on save

---

## Development Workflow

### Initial Setup
```bash
# 1. Clone/navigate to project
cd fuels-logistics-ai

# 2. Start PostgreSQL
docker-compose up -d

# 3. Install Python dependencies
cd backend
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 5. Seed database (first time only)
python seed_data.py

# 6. Start backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Install frontend dependencies
cd ../frontend
npm install

# 8. Start frontend
npm run dev
```

### Daily Development
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend (choose one)
# Option A - Base_v1 (original design)
cd frontend
npm run dev
# Access: http://localhost:5173

# Option B - MGClone_v1 (MercuryGate style)
cd MGClone_v1
npm install  # first time only
npm run dev
# Access: http://localhost:5174

# Login: coordinator / fuel2024
```

**See [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) for detailed frontend switching instructions.**

### Database Management

**Reset Database (drops all data):**
```bash
docker-compose down -v
docker-compose up -d
cd backend
python seed_data.py
```

**Check Database Directly:**
```bash
docker exec -it fuels-logistics-ai-db-1 psql -U fueluser -d fueldb
\dt  # List tables
SELECT * FROM sites;
\q  # Exit
```

**Database Migrations (Alembic):**
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

---

## Key Implementation Details

### 1. Agent Configuration JSON
Stored in `ai_agents.configuration`:
```json
{
  "email_templates": {
    "eta_request": "Hi, can you please provide an updated ETA for PO #{po_number}?"
  },
  "escalation_thresholds": {
    "critical_hours": 12,
    "high_hours": 24
  }
}
```

### 2. Activity Details JSON
Stored in `activities.details`:
```json
{
  "action": "eta_request_sent",
  "recipient": "dispatcher@carrier.com",
  "subject": "ETA Request for PO #12345",
  "body": "Hi, can you provide an ETA update?",
  "po_number": "PO-12345"
}
```

### 3. CORS Configuration
Backend allows `http://localhost:5173` (Vite dev server):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Frontend API Proxy (Vite)
Not currently used - frontend calls `http://localhost:8000/api` directly.

### 5. Authentication (Mock)
Simple username/password check in frontend:
- Username: `coordinator`
- Password: `fuel2024`
- Token stored in `localStorage`

**Note:** This is NOT production-ready. Future: implement JWT tokens with backend validation.

### 6. Gmail SMTP Integration

**Status:** ✅ Implemented (SMTP send only, no inbox polling yet)

**Purpose:** Allow agents to send real ETA request emails to carrier dispatchers.

**Implementation:** `backend/app/integrations/email_service.py`

**Configuration:**
```python
# app/config.py
gmail_user: str = ""  # Your Gmail address
gmail_app_password: str = ""  # 16-character app password (NOT regular password)
gmail_enabled: bool = False  # Set to True to enable real sending
```

**Setup Steps:**
1. Enable 2FA on Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Set `GMAIL_ENABLED=true` in `.env`
5. Set `GMAIL_USER=your@gmail.com` and `GMAIL_APP_PASSWORD=<16-char-password>`

**Email Service Modes:**
- **Mock mode (default):** Logs emails to console and `sent_emails` array
- **SMTP mode:** Sends real emails via `smtp.gmail.com:465` (SSL)

**Example Usage:**
```python
from app.integrations.email_service import email_service

result = email_service.send_eta_request(
    to_email="dispatcher@carrier.com",
    carrier_name="ABC Trucking",
    po_number="PO-12345",
    site_name="Station 42",
    hours_to_runout=18.5  # Adds urgency note to email
)

if result["success"]:
    print(f"Email sent: {result['message_id']}")
```

**Email Content:**
```
Subject: ETA Request - PO #12345

Hi ABC Trucking Dispatch,

Can you please provide an updated ETA for the following shipment?

PO Number: PO-12345
Destination: Station 42
URGENT: Site has only 18 hours of fuel remaining.

Please reply with the expected arrival time.

Thank you,
Fuels Logistics AI Coordinator
```

**Limitations (current):**
- Outbound only (no inbox polling)
- No reply parsing (future enhancement)
- No attachment support (plain text only)
- Gmail rate limits apply (~500 emails/day)

**Future Enhancements:**
- OAuth for inbox reading
- Email thread tracking
- Parse ETA replies automatically
- SMS fallback for urgent escalations

### 7. Environment Variables

**Backend `.env`:**
```env
DATABASE_URL=postgresql://fueluser:fuelpass@localhost:5432/fueldb
ANTHROPIC_API_KEY=sk-ant-xxx...
ENVIRONMENT=development

# Gmail SMTP (optional - for real email sending)
GMAIL_ENABLED=false
GMAIL_USER=
GMAIL_APP_PASSWORD=
```

**Frontend `.env` (optional):**
```env
VITE_API_URL=http://localhost:8000
```

---

## Future Enhancements

### Phase 2: Real Integrations
- [x] Gmail SMTP integration for outbound emails ✅ **COMPLETED**
- [ ] Gmail OAuth + inbox polling for ETA reply parsing
- [ ] Google Sheets integration for hourly snapshot ingestion (primary surface)
- [ ] Macropoint API for real-time GPS tracking
- [ ] TMS system integration (REST API or webhook)

### Phase 3: Advanced Features
- [ ] Multi-agent orchestration (specialized agents per region)
- [ ] Predictive analytics (ML model for consumption forecasting)
- [ ] SMS/text notifications for critical escalations
- [ ] Mobile app for on-the-go monitoring
- [ ] Advanced reporting (PDF exports, charts)

### Phase 4: Production Readiness
- [ ] JWT authentication with role-based access control
- [ ] HTTPS/TLS certificates
- [ ] Docker deployment with nginx reverse proxy
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring/observability (Prometheus, Grafana)
- [ ] Rate limiting and API security
- [ ] Database backups and disaster recovery

---

## Troubleshooting

### Backend won't start
**Error:** `psycopg2.OperationalError: could not connect to server`
- **Fix:** Ensure Docker is running: `docker ps`
- Check database is up: `docker-compose up -d`

### Database schema out of sync
**Error:** `column sites.consumption_rate does not exist`
- **Fix:** Reset database:
  ```bash
  docker-compose down -v
  docker-compose up -d
  cd backend && python seed_data.py
  ```

### Frontend shows zero data
- **Fix:** Check backend is running: `curl http://localhost:8000/api/agents/`
- Restart backend if needed
- Check browser console for CORS errors

### Agent check fails
**Error:** "Agent has no assigned sites"
- **Fix:** Assign sites to agent via "Manage Sites" button in UI
- Or run SQL:
  ```sql
  UPDATE sites SET assigned_agent_id = 1 WHERE id IN (1,2,3);
  ```

### ECONNRESET errors
- **Symptom:** Frontend shows `Error: read ECONNRESET`
- **Cause:** Backend process crashed or restarted
- **Fix:** Restart backend:
  ```bash
  taskkill //F //IM python.exe
  cd backend
  python -m uvicorn app.main:app --reload
  ```

---

## Contact & Support

**Project Repository:** (add if applicable)
**Claude API Documentation:** https://docs.anthropic.com
**FastAPI Docs:** https://fastapi.tiangolo.com

---

**End of Architecture Document**
