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

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture documentation
  - System architecture diagrams
  - Database schema
  - API endpoints
  - AI agent system details

- **[LOAD-TRACKING.md](LOAD-TRACKING.md)** - Interactive load tracking guide
  - GPS route visualization
  - Load details sidebar
  - Table sorting and search
  - Customer tagging

- **[GMAIL-SETUP.md](GMAIL-SETUP.md)** - Gmail SMTP integration guide
  - 5-minute setup for sending emails
  - App password generation
  - Environment configuration

- **[backend/EMAIL_POLLER_SETUP.md](backend/EMAIL_POLLER_SETUP.md)** - Gmail IMAP polling guide
  - Automated carrier ETA reply processing
  - Email parser capabilities
  - Troubleshooting IMAP connection issues

- **[INGESTION-ROADMAP.md](INGESTION-ROADMAP.md)** - Email automation roadmap
  - Current email parsing features
  - Future automation plans

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

### Production Features (New)
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
- SendGrid / Gmail for email delivery
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
├── ARCHITECTURE.md
├── GMAIL-SETUP.md
└── INGESTION-ROADMAP.md
```

---

## Key Workflows

### Starting the System
1. Start Docker database: `docker-compose up -d`
2. Start backend: `cd backend && uvicorn app.main:app --reload`
3. Start frontend: `cd frontend && npm run dev` (or `cd MGClone_v1 && npm run dev`)
4. Access dashboard in browser

### Stopping the System
1. Press `Ctrl+C` in frontend terminal(s)
2. Press `Ctrl+C` in backend terminal
3. Stop database: `docker-compose down`

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
- Agents can send ETA requests (mocked in MVP) and create escalations
- All actions are logged to the Activity table
- Human coordinators supervise via the HITL dashboard

### Agent Tools
- `send_eta_request_email` - Request delivery updates from carriers
- `create_escalation` - Flag critical issues for human attention
- `update_dashboard_note` - Add notes to site records

---

## Contributing

This is currently a private MVP project.

---

## License

Proprietary - All rights reserved

---

## Support

For questions or issues:
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [LOAD-TRACKING.md](LOAD-TRACKING.md) for GPS tracking features
- See [backend/EMAIL_POLLER_SETUP.md](backend/EMAIL_POLLER_SETUP.md) for email automation

---

## Recent Updates (February 2026)

**Week 6 - Production Observability:**
- ✅ **Structured JSON Logging** - Production-ready logging with structlog
- ✅ **Agent Run History** - Track execution metrics (duration, sites checked, emails sent, API calls, tokens used)
- ✅ **Agent Monitor UI** - Real-time run history panel with collapsible metrics view
- ✅ **CSV Export** - Download run history data for analysis

**Week 5 - Agent Safety:**
- ✅ **Execution Modes** - Graduated autonomy (Draft Only / Auto Email / Full Auto)
- ✅ **UI Mode Toggle** - Admin control of agent autonomy level

**Week 3 - Email Integration:**
- ✅ **SendGrid Integration** - Production email sending with audit trail
- ✅ **Gmail IMAP Poller** - Automated carrier ETA reply processing

**Earlier Updates:**
- ✅ **JWT Authentication** - Secure API with role-based access
- ✅ **Google Sheets Integration** - Sync dashboard to external spreadsheets
- ✅ **Interactive Load Tracking** - GPS route visualization with Leaflet.js
- ✅ **Staleness Detection** - Automated monitoring of data freshness
- ✅ **Overnight-Aware Escalations** - Time-based urgency logic

See [INGESTION-ROADMAP.md](INGESTION-ROADMAP.md) for email automation roadmap.

---

**Version:** 0.4.0 (Production Ready)
**Last Updated:** February 6, 2026
