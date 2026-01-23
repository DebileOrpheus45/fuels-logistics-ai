# Fuels Logistics AI Coordinator

An intelligent platform that automates fuel delivery logistics coordination using AI agents powered by Claude.

## Quick Start

### Prerequisites
- Docker Desktop
- Python 3.10+
- Node.js 18+
- Anthropic API Key

### Installation

```bash
# 1. Start database
docker-compose up -d

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Seed database
python seed_data.py

# 5. Start backend (in a new terminal)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Choose and start a frontend (in another terminal)
# Option A: Base_v1 (modern design)
cd ../frontend
npm install
npm run dev
# Access: http://localhost:5173

# Option B: MGClone_v1 (MercuryGate TMS style)
cd ../MGClone_v1
npm install
npm run dev
# Access: http://localhost:5174
```

**Login:** coordinator / fuel2024

---

## Two Frontends Available

This project includes **two hotswappable frontends** that connect to the same backend:

### Base_v1 (`frontend/` - Port 5173)
- Modern, card-based SaaS interface
- Mobile-friendly responsive design
- Best for daily operations

### MGClone_v1 (`MGClone_v1/` - Port 5174)
- MercuryGate TMS-inspired control tower
- Enterprise table-based interface
- Best for executive dashboards and users familiar with TMS software

**See [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) for detailed comparison and switching instructions.**

---

## Documentation

- **[USER-GUIDE.md](USER-GUIDE.md)** - User-friendly guide for non-technical users
  - How to start/stop the system
  - Daily workflows
  - Understanding the dashboard
  - Common tasks and troubleshooting

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture documentation
  - System architecture diagrams
  - Database schema
  - API endpoints
  - AI agent system details
  - Frontend architecture (both versions)

- **[FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md)** - Frontend switching guide
  - Comparison table
  - How to run both simultaneously
  - When to use each frontend
  - Troubleshooting

---

## Features

### Core Capabilities
- ✅ Real-time inventory monitoring across multiple sites
- ✅ Automated ETA requests to carriers
- ✅ Predictive escalation of runout scenarios
- ✅ Human-in-the-Loop (HITL) supervision dashboard
- ✅ Batch site constraint management via CSV
- ✅ AI agent scheduling and automation
- ✅ Site-specific notes and constraints
- ✅ Multi-agent site assignment

### Tech Stack

**Backend:**
- FastAPI + PostgreSQL + SQLAlchemy
- Anthropic Claude API for AI agents
- APScheduler for automated checks
- Docker for database containerization

**Frontend (Both Versions):**
- React 18 + Vite
- TanStack Query (React Query)
- TailwindCSS
- Lucide React icons

---

## Project Structure

```
fuels-logistics-ai/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI agent system
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   └── routers/          # API endpoints
│   ├── seed_data.py          # Database seeding
│   └── requirements.txt
├── frontend/                  # Base_v1 - Modern design (port 5173)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js
│   │   └── index.css
│   └── package.json
├── MGClone_v1/               # MercuryGate-style (port 5174)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js
│   │   └── index.css
│   └── package.json
├── docker-compose.yml
├── ARCHITECTURE.md
├── USER-GUIDE.md
└── FRONTEND-SWITCHER.md
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
- See [USER-GUIDE.md](USER-GUIDE.md) for usage help
- See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) for frontend questions

---

## Recent Updates (January 22, 2026)

**New Features:**
- ✅ **Gmail SMTP Integration** - Real email sending to carriers (optional)
- ✅ **Snapshot Ingestion API** - Hourly state updates separate from configuration
- ✅ **Staleness Detection** - Tracks when data stops updating
- ✅ **Overnight Awareness** - Time-based escalation urgency
- ✅ **Decision Logging** - Lightweight token-efficient action tracking
- ✅ **Redesigned UI** - Tabs on top, sidebar metrics, better UX
- ✅ **Loads Tab** - Dedicated view with delayed loads filtering

See [PROJECT-ROADMAP.md](PROJECT-ROADMAP.md) for complete feature list and plans.

---

**Version:** 0.2.0 (MVP+)
**Last Updated:** January 22, 2026
