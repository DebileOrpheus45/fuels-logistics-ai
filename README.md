# Fuels Logistics AI Coordinator

An intelligent platform that automates fuel delivery logistics coordination using AI agents powered by Claude.

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.10+
- Node.js 18+
- Anthropic API Key
- Gmail account with App Password (optional - for email features)

### Installation

```bash
# 1. Start database
docker-compose up -d

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add:
#   - ANTHROPIC_API_KEY (required)
#   - Gmail credentials (optional - see GMAIL-SETUP.md)

# 4. Seed database with realistic demo data
python seed_data.py

# 5. Add mock GPS tracking data
python add_tracking_data.py

# 6. Start backend (in a new terminal)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Install and start frontend (in another terminal)
cd ../frontend
npm install
npm run dev
# Access: http://localhost:5173
```

**Login credentials:**
- `admin / admin123` (Admin role)
- `coordinator / fuel2024` (Operator role)

### Optional: Email Integration

To enable automated ETA email polling from carriers:

```bash
# See EMAIL_POLLER_SETUP.md for detailed setup
cd backend
python start_email_poller.py
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, DB schema, API endpoints, AI agent design |
| [USER-GUIDE.md](USER-GUIDE.md) | Non-technical user manual (startup, workflows, troubleshooting) |
| [PROJECT-ROADMAP.md](PROJECT-ROADMAP.md) | Completed/current/future phases |
| [ENTERPRISE-READINESS-ROADMAP.md](ENTERPRISE-READINESS-ROADMAP.md) | Production deployment plan (0.4 → 1.0) |
| [LOAD-TRACKING.md](LOAD-TRACKING.md) | GPS routes, load sidebar, sorting, customer tagging |
| [GMAIL-SETUP.md](GMAIL-SETUP.md) | Gmail SMTP setup for sending ETA emails |
| [backend/EMAIL_POLLER_SETUP.md](backend/EMAIL_POLLER_SETUP.md) | Gmail IMAP polling for auto-parsing carrier replies |
| [backend/AUTH-SETUP.md](backend/AUTH-SETUP.md) | JWT authentication, RBAC roles, token management |
| [INGESTION-ROADMAP.md](INGESTION-ROADMAP.md) | Email automation: completed and planned channels |

---

## Features

### Core Capabilities
- ✅ Real-time inventory monitoring across multiple sites
- ✅ AI-powered automated ETA requests to carriers
- ✅ Predictive escalation of runout scenarios
- ✅ Human-in-the-Loop (HITL) supervision dashboard
- ✅ Interactive load tracking with GPS route visualization
- ✅ Gmail IMAP email polling for automated carrier reply processing
- ✅ Excel-style sorting and multi-field search
- ✅ Customer tagging and filtering
- ✅ AI agent scheduling and automation
- ✅ Site-specific notes and constraints
- ✅ Staleness detection and overnight-aware escalations

### Intelligence & Automation
- ✅ Tiered agent architecture (Tier 1 rules engine $0/run + Tier 2 LLM on-demand)
- ✅ Knowledge graph: carrier reliability scoring, site risk profiles
- ✅ Auto-escalation of non-ETA emails (shortages, breakdowns, cancellations)
- ✅ Executive status summary generator (Agent Monitor)
- ✅ System Logic page with decision architecture explainer

### Production Features
- ✅ JWT authentication with real login flow
- ✅ Agent execution modes (Draft Only / Auto Email / Full Auto)
- ✅ Structured JSON logging with structlog
- ✅ Agent run history tracking with execution metrics
- ✅ CSV export for run history data
- ✅ Google Sheets integration for dashboard sync

### Tech Stack

**Backend:**
- FastAPI + PostgreSQL + SQLAlchemy
- Anthropic Claude API for AI agents
- APScheduler for automated checks
- Docker for database containerization
- JWT authentication with python-jose
- Structlog for production logging
- Resend for email delivery (HTTP API)
- Google Sheets API (gspread) for dashboard sync

**Frontend:**
- React 18 + Vite
- TanStack Query (React Query) for data fetching
- TailwindCSS for styling
- Lucide React icons
- Leaflet.js for interactive GPS maps
- JWT token management with localStorage
- Environment-aware API configuration

---

## Project Structure

```
fuels-logistics-ai/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI agent system
│   │   ├── integrations/        # Claude API service
│   │   ├── services/            # Email poller, OSRM routing
│   │   ├── utils/               # Email parser, timezone helpers
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   └── routers/             # API endpoints
│   ├── seed_data.py             # Realistic demo data seeding
│   ├── start_email_poller.py    # Email poller startup script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main dashboard component
│   │   ├── api/client.js        # Environment-aware API client
│   │   └── index.css
│   ├── .env.example             # Environment variable template
│   └── package.json
├── docker-compose.yml
├── start_all.ps1               # One-command startup (backend + poller + frontend)
├── ARCHITECTURE.md
├── GMAIL-SETUP.md
└── INGESTION-ROADMAP.md
```

---

## Key Workflows

### Starting the System (One Command)
```powershell
powershell -File start_all.ps1
```
This starts backend (port 8000), email poller, and frontend (port 5173) together. Press `Ctrl+C` to stop all.

**Manual start (alternative):**
1. Start Docker database: `docker-compose up -d`
2. Start backend: `cd backend && uvicorn app.main:app --reload`
3. Start email poller: `cd backend && python start_email_poller.py`
4. Start frontend: `cd frontend && npm run dev`
5. Access dashboard at http://localhost:5173

### Stopping the System
1. Press `Ctrl+C` in the `start_all.ps1` terminal (stops all services)
2. Or manually stop each process + `docker-compose down`

### Resetting Database
```bash
docker-compose down -v  # Deletes all data
docker-compose up -d
cd backend
python seed_data.py
```

---

## AI Agent System

### How It Works
- AI agents monitor assigned sites every 15 minutes (configurable)
- Agents analyze inventory levels, runout times, and active loads
- Agents send real ETA request emails via Gmail SMTP to carriers
- Creates escalations for critical inventory situations
- All actions logged to Activity table + Run History with full decision audit trail
- Human coordinators supervise via the HITL dashboard
- Inbound carrier ETA replies are auto-parsed (LLM + regex) and update load ETAs

### Agent Tools
- `send_eta_request_email` - Send real ETA request emails to carrier dispatchers
- `create_escalation` - Flag critical issues for human attention
- `update_dashboard_note` - Add notes to site records

### Run History & Decision Audit
Each agent run records:
- Duration, sites checked, loads analyzed, API calls made
- Emails sent and escalations created
- Individual decisions with type badges and summaries
- Clickable/expandable rows in the Agent Monitor UI

---

## Contributing

This is currently a private MVP project.

---

## License

Proprietary - All rights reserved

---

## Recent Updates (February 2026)

**Week 8 - Tiered Agent Intelligence:**
- ✅ **Tier 1 Rules Engine** - Zero-token threshold checks handle ~90% of routine monitoring (runout detection, stale ETAs, delayed loads)
- ✅ **Tier 2 LLM Agent** - Claude fires only on ambiguous situations flagged by Tier 1 (unreliable carriers, multi-site risk)
- ✅ **Knowledge Graph** - Passive SQL-based intelligence: carrier reliability scores, site false alarm rates, risk profiles
- ✅ **Auto-Escalation** - Non-ETA carrier emails (shortages, breakdowns, cancellations) auto-detected and escalated
- ✅ **System Logic Page** - Decision architecture explainer with live knowledge graph data
- ✅ **Executive Summary** - One-click status update on Agent Monitor from live data + knowledge graph
- ✅ **Escalation Filtering** - Open/Resolved toggle on Escalations page

**Week 7 - Email Automation & Agent Audit Trail:**
- ✅ **Real Gmail ETA Emails** - Agent sends actual ETA request emails via Gmail SMTP to carriers
- ✅ **Auto-Reply Processing** - Inbound carrier replies parsed by LLM (Claude Haiku) with regex fallback; ETAs auto-updated on loads
- ✅ **Relative Time Parsing** - "couple hours", "30 minutes out" resolved against email received time
- ✅ **Agent Run History Recording** - Every run creates an audit record with decisions, emails sent, escalations created
- ✅ **Expandable Run History UI** - Click any run to see decision cards with type badges and summaries
- ✅ **Load Notes** - Add timestamped notes to loads (persisted to Postgres JSON column)
- ✅ **One-Command Startup** - `start_all.ps1` launches backend + email poller + frontend together
- ✅ **401 Auto-Redirect** - Expired tokens auto-redirect to login

**Week 6 - Production Observability:**
- ✅ **Structured JSON Logging** - Production-ready logging with structlog
- ✅ **Agent Run History Model** - Track execution metrics (duration, sites checked, emails sent, API calls, tokens used)
- ✅ **Agent Monitor UI** - Real-time run history panel with collapsible metrics view
- ✅ **CSV Export** - Download run history data for analysis

**Week 5 - Agent Safety:**
- ✅ **Execution Modes** - Graduated autonomy (Draft Only / Auto Email / Full Auto)
- ✅ **UI Mode Toggle** - Admin control of agent autonomy level

**Week 3 - Email Integration:**
- ✅ **Resend Integration** - Production email sending with audit trail
- ✅ **Gmail IMAP Poller** - Automated carrier ETA reply processing

**Earlier Updates:**
- ✅ **JWT Authentication** - Secure API with role-based access
- ✅ **Google Sheets Integration** - Sync dashboard to external spreadsheets
- ✅ **Interactive Load Tracking** - GPS route visualization with Leaflet.js
- ✅ **Staleness Detection** - Automated monitoring of data freshness
- ✅ **Overnight-Aware Escalations** - Time-based urgency logic

---

**Version:** 0.6.0 (Tiered Agent Intelligence + Knowledge Graph)
**Last Updated:** February 14, 2026
