# Fuels Logistics AI Coordinator - Project Roadmap

**Last Updated:** 2026-01-22

This living document tracks completed work, current tasks, and future priorities for the Fuels Logistics AI Coordinator platform.

---

## ✅ Completed (Phase 1 - MVP Foundation)

### Core Platform
- [x] PostgreSQL database with Docker Compose
- [x] FastAPI backend with SQLAlchemy models
- [x] React frontend with Vite
- [x] Database models: Sites, Loads, Carriers, Lanes, Agents, Activities, Escalations
- [x] CRUD APIs for all resources
- [x] Dashboard with real-time stats

### Multi-Customer Support
- [x] Customer enum (Stark Industries, Wayne Enterprises, LuthorCorp)
- [x] ERP source tracking (Fuel Shepherd, FuelQuest, Manual)
- [x] Service type levels (Inventory & Tracking vs Tracking Only)
- [x] Customer filtering in Sites view
- [x] Upload audit logging

### Staleness Detection (NEW)
- [x] Staleness tracking fields on Sites (`last_inventory_update_at`, `inventory_staleness_threshold_hours`)
- [x] Staleness tracking fields on Loads (`last_eta_update_at`, `eta_staleness_threshold_hours`)
- [x] Computed properties: `is_inventory_stale`, `is_eta_stale`, staleness hours
- [x] Foundation for "staleness is the signal" philosophy

### Overnight Awareness (NEW)
- [x] Time-aware agent configuration (`time_aware_escalation`, `overnight_escalation_multiplier`)
- [x] Configurable overnight hours (`overnight_start_hour`, `overnight_end_hour`)
- [x] Coverage tracking (`coverage_hours`: 24/7, business hours, overnight only)

### Decision Visibility (NEW)
- [x] Lightweight decision logging in Activity model
- [x] Decision codes (e.g., "STALE_ETA_LOW_INVENTORY")
- [x] Decision metrics (JSON with key values that triggered action)
- [x] Optional reasoning summary field

### AI Agent System
- [x] Claude API integration
- [x] APScheduler for automated checks
- [x] Site assignment to agents
- [x] Agent start/stop/pause controls
- [x] Activity logging

### Mock Integrations
- [x] Mock email service (logs emails to console)
- [x] Mock TMS service (simulates Macropoint tracking)
- [x] Ready for real integration swaps

---

## 🔨 In Progress (Current Sprint)

### Snapshot Ingestion Architecture
- [ ] **Convert CSV upload to snapshot ingestion** (constraints vs state separation)
  - Current CSV upload → Snapshot state endpoint
  - New admin endpoint → Site constraints configuration
  - Separate "what tanks CAN hold" from "what's IN them now"

### Gmail Integration (Quick Send)
- [ ] **SMTP-based Gmail sending** (outbound only, no OAuth needed)
  - Use app password for authentication
  - Demo-ready: agent can send real emails to carriers
  - Foundation for full inbox polling later

### Documentation Updates
- [ ] **Update ARCHITECTURE.md** with staleness tracking, overnight awareness, decision logging
- [ ] **Update USER-GUIDE.md** with new features and workflows
- [ ] **Document snapshot vs constraints mental model**

---

## 📋 Next Up (Priority Queue)

### Snapshot Workflow Improvements
1. **Snapshot metadata tracking** - `snapshot_time`, `source`, `notes` on ingestion
2. **Historical snapshots table** - Audit trail of all state updates over time
3. **Staleness alerts in dashboard** - Visual indicators for stale data

### Gmail Full Integration
4. **OAuth setup for Gmail inbox reading**
5. **Email polling service** - Check for carrier ETA replies
6. **ETA parsing logic** - Extract structured data from email responses
7. **Load updates from emails** - Automatically update ETAs when dispatcher replies

### Google Sheets Integration
8. **Google Sheets reader** (primary integration surface)
   - OAuth setup for Sheets API
   - Configurable sheet URL per customer
   - Hourly automated pull (cron job or Cloud Function trigger)
   - CSV export simulation → Sheets direct read

9. **Sheet template generator**
   - Per-ERP column mapping templates
   - One-click "generate my template sheet" for customers
   - Auto-formatting and validation

### Enhanced Agent Logic
10. **Staleness-aware decisions**
    - "ETA hasn't changed in 6 hours but truck should be moving → send email"
    - "Site hasn't updated in 3 hours → check if system issue"
    - "Runout window shrinking but no new loads → escalate"

11. **Time-aware escalation logic**
    - More aggressive overnight thresholds
    - Escalation urgency multipliers by time of day
    - "Blind spot" detection (no updates overnight)

12. **Decision explanation generation**
    - On-demand LLM explanation when viewing Activity log
    - "Why did the agent take this action?" transparency
    - Token-efficient (only generate when user clicks "explain")

### Admin & Configuration UI
13. **Admin area for site constraints**
    - Batch configure: capacity, consumption rate, thresholds
    - Import/export site configuration
    - Separate from hourly snapshot updates

14. **Agent configuration UI**
    - Set overnight hours and multipliers
    - Configure coverage patterns
    - Assign/unassign sites with drag-and-drop

15. **ERP template management**
    - View/edit column mappings
    - Test CSV parsing before upload
    - Custom field mappings per customer

### Demo Environment
16. **Isolated demo sandbox**
    - Separate demo database
    - Demo-only Gmail inbox (no production email leakage)
    - Recipient allowlist and rate limits
    - Full activity replay capability

17. **Interactive demo features**
    - Real carrier email loop (AI → carrier → AI)
    - Visible reasoning in real-time
    - Human override controls
    - "Rewind and replay" for demos

---

## 🔮 Future (Post-MVP)

### Scale & Performance
- Snapshot compression and archival
- Multi-tenant customer isolation
- Agent capacity monitoring (500-1000 sites per agent)
- Distributed agent scheduling

### Advanced Integrations
- EDI ingestion (when customers have it)
- TMS vendor-specific connectors (when needed)
- Macropoint real-time tracking integration
- Billing/invoicing system hooks

### Intelligence Enhancements
- Predictive runout modeling (ML-based consumption forecasting)
- Route optimization suggestions
- Historical pattern analysis
- Anomaly detection (unusual consumption spikes)

### Enterprise Features
- SSO/SAML authentication
- Role-based access control (RBAC)
- Multi-region deployments
- SLA monitoring and guarantees

### Product Expansion
- Mobile app for drivers/dispatchers
- SMS/WhatsApp notifications
- Voice call integration (Twilio)
- Full NLP for unstructured email parsing

---

## 🚫 Explicit Non-Goals (For Now)

These are intentionally out of scope until post-pilot:

- ❌ Full TMS replacement (we're a coordinator, not a planner)
- ❌ Vendor-specific portal integrations (batch exports are fine)
- ❌ Real-time API requirements (hourly snapshots sufficient)
- ❌ Pricing, billing, invoicing features
- ❌ Inbound free-text NLP (structured parsing only)
- ❌ Complex EDI handling (future integration, not MVP)
- ❌ Multi-region data residency (single region MVP)

---

## 📊 Success Metrics (Pilot Goals)

**Customer can:**
1. Export data once per hour (from any system)
2. Paste into Google Sheet (or upload CSV)
3. Let AI watch overnight
4. Wake up only when something matters (not every alert)

**Agent effectiveness:**
- 80%+ of routine emails sent automatically
- 70%+ reduction in "checking if everything is okay" overhead
- 90%+ escalation accuracy (human agrees with urgency)
- <5 min response time for critical issues (even overnight)

**Integration reality:**
- Zero IT friction for small customers
- Works with any fuel system (via export)
- No custom vendor integrations required for MVP

---

## 🎯 Current Focus

**This Week:**
1. Snapshot ingestion architecture
2. Quick Gmail send
3. Documentation updates

**This Month:**
4. Google Sheets integration
5. Staleness-aware agent logic
6. Interactive demo environment

**This Quarter:**
7. Full Gmail inbox polling
8. Historical snapshot analytics
9. First pilot customer (real data, real emails)

---

## 📝 Notes & Decisions

### Architecture Decisions
- **Batch-first, integration-light** - No real-time requirements
- **Google Sheets as primary hub** - Matches existing workflows
- **Staleness is the signal** - Missing updates matter more than fresh data
- **Lightweight logging** - Token-efficient, explain on-demand
- **Separate constraints from state** - Configuration vs snapshots

### Customer Insights
- No internal engineering teams at small-mid fuel operators
- Heavy reliance on vendor portals and manual exports
- Overnight blind spot is critical use case
- Email is primary communication channel
- Spreadsheets are universal integration layer

### Technical Constraints
- Agent capacity: ~500-1000 sites per agent (organizational limit, not technical)
- Snapshot frequency: Hourly is sufficient (not real-time)
- Decision logging: <100 tokens per activity (cost optimization)
- Email safety: Allowlists, rate limits, demo-only prefixes

---

**For questions or suggestions, see:** [ARCHITECTURE.md](ARCHITECTURE.md) | [USER-GUIDE.md](USER-GUIDE.md)
