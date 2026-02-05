# Fuels Logistics AI Coordinator: Enterprise Readiness Roadmap

**Target Customer:** Type A - Small and Regional Fuel Station Chains
**Current Version:** 0.4.0 (Pre-Demo MVP)
**Target Version:** 1.0.0 (Type A Enterprise-Ready)
**Last Updated:** February 5, 2026

---

## Executive Summary

This roadmap transforms the Fuels Logistics AI Coordinator MVP from a demonstration system into an enterprise-ready platform for Type A customers (small and regional fuel station chains with 5-50 locations).

**Key Strategic Insight:** The most important gaps are not "more AI." They are **trust and operability** gaps that prevent daily production use:
- Real inventory and ETA ingestion (not mocked data)
- Real email communications with carrier tracking
- Role-based security and audit trails
- Durable scheduling with retries and failure handling
- Production observability and monitoring

**Why Type A First:**
1. **Material operational pain** - Manual dispatch, runout risks, spreadsheet-driven operations
2. **Manageable procurement** - Faster sales cycles than enterprise oil majors
3. **Phased integration path** - Start with CSV/email, mature to ATG APIs over time
4. **Market validation** - 151,975 US convenience stores, 122,620 selling motor fuels, 63% single-store operators

---

## Current MVP State Analysis

### ✅ Existing Strengths

**Operational Data Model:**
- Core entities: Sites, Loads, Carriers, Lanes, Activities, Escalations, AI Agents
- Agent runtime with tool functions (send ETA email, create escalation, update notes)
- APScheduler-backed agent execution cycles
- Activity audit log for AI actions

**Human-in-the-Loop Workflow:**
- Escalations table + UI for review/resolve/annotate
- Agent Monitor supervision interface
- Activity logs and agent status tracking

**Operations UI Surface:**
- Sites/Loads/Agents/Escalations tabs
- Clickable stats filters
- Batch CSV site constraint management
- Multi-site agent assignment

**Extensibility Hooks:**
- Mocked integration layer signaling future connector paths
- Clear separation of concerns in routing/services

### ⚠️ Production Blockers

**Security & Trust:**
- ❌ Frontend-only mock authentication (no backend enforcement)
- ❌ No RBAC or role separation
- ❌ No password hashing or token rotation
- ❌ localStorage token storage (insecure)

**Integration & Data Plane:**
- ❌ Email sending is mocked (logged to Activities only)
- ❌ No real ETA ingestion from carrier replies
- ❌ No real inventory ingestion (manual DB state)
- ❌ No ATG (automatic tank gauge) integration
- ❌ No data quality safeguards (staleness, plausibility)

**Operational Resilience:**
- ❌ No durable job queue (APScheduler in-memory only)
- ❌ No retry logic or idempotency
- ❌ No dead-letter queue for failed actions
- ❌ Silent failures possible

**Observability:**
- ❌ No metrics or tracing
- ❌ No health checks or alerting
- ❌ No operational dashboards
- ❌ No visibility into "why did agent not run?"

---

## Three-Phase Enterprise Readiness Roadmap

### Phase 1: Trust & Safety (8-12 weeks)

**Target Outcome:** "Operationally usable" even with partial integrations, while preventing runaway automation and building trust.

**Goal:** Type A customer can safely run system in production with CSV/email workflows and human oversight.

#### Security Baseline (2-4 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Backend JWT authentication with password hashing | 2 weeks | P0 | Very High - Procurement gate |
| RBAC system (admin, manager, dispatcher, read-only) | 2 weeks | P0 | High - Multi-user viability |
| Remove frontend-only auth, enforce server-side | 1 week | P0 | Very High - Security requirement |
| Immutable audit trails (who/what/when for all actions) | 1 week | P0 | High - Trust + accountability |

**Deliverables:**
- `/api/auth/login` endpoint with bcrypt password hashing
- JWT tokens with short TTL and refresh mechanism
- Middleware enforcing RBAC on all write endpoints
- Agent tool calls respect RBAC semantics
- Immutable activity log with user ID, timestamp, IP address

#### Operational Safety Rails (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Agent execution modes (draft-only, auto-email+manual-escalate) | 1 week | P0 | Very High - Safe rollout |
| Per-carrier throttles and idempotent email gates | 1 week | P0 | High - Prevent spam |
| "Don't email twice in X minutes" logic | 3 days | P0 | High - Carrier relations |

**Deliverables:**
- Agent config: `execution_mode` enum (DRAFT, AUTO_EMAIL, FULL_AUTO)
- Carrier config: `min_minutes_between_emails`, `max_emails_per_day`
- Idempotency key: `EmailSent(load_id, carrier_id, template_version, time_bucket)`
- UI toggles for execution mode per agent

#### Real Email Integration (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| SMTP/ESP integration (replace mocked email) | 1 week | P0 | Very High - Core workflow |
| Email template management system | 1 week | P1 | High - Professional comms |
| Outbound email logging and delivery tracking | 3 days | P1 | High - Audit trail |
| Bounce/complaint webhook handling | 3 days | P2 | Medium - Reputation mgmt |

**Deliverables:**
- SendGrid/AWS SES integration with templating
- `EmailLog` table: recipient, template_id, sent_at, delivery_status, bounce_reason
- Template editor UI (admin-only)
- Webhook endpoints for delivery events

#### Inventory Ingestion Minimum (3-4 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| CSV import API for inventory readings | 1 week | P0 | Very High - Runout logic depends on it |
| Simple push API endpoint for real-time updates | 1 week | P0 | Very High - Integration path |
| Track `inventory_last_updated_at` and freshness warnings | 1 week | P0 | High - Data quality signal |
| Canonical `InventoryObservation` schema with provenance | 1 week | P0 | High - Multi-source truth |

**Deliverables:**
- `POST /api/inventory/import` (CSV upload with validation)
- `POST /api/inventory/observations` (single/batch push API)
- Schema: `InventoryObservation(site_id, tank_id, gallons, timestamp, source, confidence)`
- UI: Staleness indicator (⚠️ "Last updated 6 hours ago")
- Provenance rules: "Manual override > API > CSV" with timestamps

#### Observability Minimum (1-2 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Health check endpoints (/health, /ready) | 2 days | P0 | High - Uptime monitoring |
| Structured logging (JSON with context) | 3 days | P0 | High - Debugging |
| Job run status tracking in DB | 3 days | P0 | Very High - Visibility |
| Basic alerting (email on agent failure) | 2 days | P1 | High - Operational awareness |

**Deliverables:**
- `/health` endpoint (DB connection, Redis if used)
- Structured logs: `{"timestamp": "...", "level": "INFO", "agent_id": 123, "action": "eta_request_sent", "load_id": 456}`
- `AgentRunHistory` table: agent_id, started_at, completed_at, status, error_message
- Alert rules: "Agent failed 3 times in a row" → email ops team

**Phase 1 Exit Criteria:**
- ✅ Backend auth + RBAC enforced on all endpoints
- ✅ Agents operate in configurable safety modes (default: draft-only)
- ✅ Real emails sent to carriers with throttling
- ✅ CSV/API inventory ingestion with freshness tracking
- ✅ Health checks and job run visibility
- ✅ **Demo-able to Type A customer with confidence**

---

### Phase 2: Integration & Reliability (10-14 weeks)

**Target Outcome:** "Credible integration story" and reliability under real operational load.

**Goal:** Type A customer replaces spreadsheets and manual dispatch with automated workflows backed by real inventory data.

#### Durable Background Execution (4-6 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Replace APScheduler with reliable job runner (Celery/RQ/Temporal) | 2 weeks | P0 | Very High - Prevents silent failures |
| Implement retries with exponential backoff | 1 week | P0 | Very High - Resilience |
| Add idempotency keys to all agent actions | 1 week | P0 | High - Exactly-once semantics |
| Dead-letter queue for failed jobs | 1 week | P1 | High - Failure visibility |

**Deliverables:**
- Celery workers with Redis broker (or Temporal for enterprise-grade)
- Retry policy: 3 attempts with exponential backoff (1min, 5min, 15min)
- Idempotency: `AgentAction(agent_id, action_type, target_id, timestamp_bucket)`
- DLQ UI: "Failed Jobs" tab with retry/discard buttons

#### First Real ATG Integration (6-8 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Research and select ATG partner (Veeder-Root, Dover, etc.) | 1 week | P0 | Very High - Differentiator |
| Implement canonical InventoryObservation schema | 1 week | P0 | Very High - Multi-source foundation |
| Build connector pattern for first ATG vendor API | 3 weeks | P0 | Very High - Real-time inventory |
| Add OAuth2/API key management for ATG credentials | 1 week | P0 | High - Security requirement |
| Polling scheduler for ATG data sync | 1 week | P0 | High - Data freshness |

**Deliverables:**
- Connector architecture: `ATGConnector` interface with `fetch_inventory()` method
- Veeder-Root API integration (or equivalent) with error handling
- `ATGCredential` model: encrypted API keys per tenant
- Polling: every 15 minutes, store observations with `source='veeder_root'`
- UI: "Integrations" tab showing ATG connection status

#### Real Load/ETA Ingestion (3-4 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Upgrade email parser with provenance tracking | 1 week | P0 | High - Reduces manual chasing |
| Add CSV ingestion for loads with validation | 1 week | P0 | High - Bulk import path |
| Implement LoadStatusEvent schema with source tracking | 1 week | P0 | High - Multi-source truth |
| Provenance resolution rules (manual > API > email > CSV) | 3 days | P0 | High - Conflict handling |

**Deliverables:**
- Email parser: extract ETA from carrier replies, create `LoadStatusEvent(load_id, eta, source='email_reply', parsed_at)`
- CSV import: `/api/loads/import` with validation (PO number, carrier, ETA)
- Schema: `LoadStatusEvent(load_id, event_type, eta, source, confidence, created_at)`
- Provenance logic: latest event wins within source tier, higher tier overrides lower

#### Data Quality Guards (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Staleness checks (flag >6hr old inventory) | 3 days | P0 | High - Avoids false alarms |
| Plausibility validation (gallons >0, <capacity) | 3 days | P0 | High - Data sanity |
| Confidence scoring for inventory observations | 1 week | P1 | High - Trust signal |
| Missing delivery detection (expected load didn't arrive) | 1 week | P1 | Medium - Exception catching |

**Deliverables:**
- Staleness: `InventoryObservation.is_stale()` property (>6 hours old)
- Plausibility: reject readings outside `[0, tank_capacity * 1.1]`
- Confidence score: `1.0` for ATG API, `0.8` for CSV, `0.6` for manual entry
- UI: ⚠️ staleness badge, 🔴 plausibility error banner

#### Audit Deepening (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Store decision inputs/outputs for escalations | 1 week | P1 | High - Explainability |
| Make escalation resolution a structured workflow | 1 week | P1 | High - Process compliance |
| Add "escalation history" view (all past escalations for site/load) | 3 days | P2 | Medium - Pattern visibility |

**Deliverables:**
- `EscalationContext` JSONB field: `{"inventory_gallons": 1200, "runout_hours": 4, "loads_in_transit": [...]}`
- Escalation workflow: `created → assigned → investigating → resolved`
- UI: "Escalation Detail" modal with context, timeline, resolution notes

#### Operator UX Hardening (3-4 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Guided onboarding flow with integration status checks | 1 week | P0 | High - Reduces support load |
| Bulk edit tools with validation | 1 week | P1 | High - Efficiency |
| Search/filter improvements (by site code, carrier, status) | 1 week | P1 | High - Usability |
| "Top exceptions" dashboard widget | 3 days | P2 | Medium - Focus attention |

**Deliverables:**
- Onboarding wizard: "1. Connect inventory → 2. Add carriers → 3. Configure agents → 4. Test email"
- Bulk edit: select multiple loads → "Update ETAs" → CSV upload or manual entry
- Search: full-text on site code, carrier name, load PO number
- Widget: "Top 5 sites at risk" with one-click escalation creation

**Phase 2 Exit Criteria:**
- ✅ Reliable job execution with retries and DLQ
- ✅ First ATG integration live with real inventory data
- ✅ Load/ETA ingestion from email + CSV with provenance
- ✅ Data quality guards prevent false positives
- ✅ Escalations have full decision context and structured workflow
- ✅ **Customer can operate 10+ sites without manual spreadsheet tracking**

---

### Phase 3: Multi-Tenant Enterprise-Ready (8-12 weeks)

**Target Outcome:** Procurement-ready for Type A chains with MSP-managed IT and multi-team operations.

**Goal:** Pass vendor risk assessments, support multi-brand/multi-location deployments, provide analytics for continuous improvement.

#### Tenant Isolation (3-4 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Implement logical tenant separation (tenant_id FK everywhere) | 2 weeks | P0 | Very High - Multi-customer foundation |
| Per-tenant configs (agents, templates, thresholds, carrier rules) | 1 week | P0 | High - Customization |
| Tenant admin UI (settings, users, integrations) | 1 week | P1 | High - Self-service |

**Deliverables:**
- All models: `tenant_id` foreign key with index
- Row-level security: queries auto-filter by `current_user.tenant_id`
- `TenantConfig` table: `{"runout_threshold_hours": 8, "email_throttle_minutes": 30}`
- UI: "Organization Settings" tab (admin-only)

#### Security Posture Completeness (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Security questionnaire responses and documentation | 1 week | P0 | Very High - Vendor risk clearance |
| Data retention policies and automated cleanup | 3 days | P0 | High - Compliance |
| Backup/restore procedures and testing | 1 week | P0 | High - Business continuity |
| Align API design with Open Retailing security/transport guides | 3 days | P1 | Medium - Standards leverage |

**Deliverables:**
- Security doc: encryption at rest/transit, password policy, session management, vulnerability scanning
- Retention: `ActivityLog` rows >90 days auto-archived, `InventoryObservation` >1 year deleted
- Backup: daily automated PostgreSQL dumps to S3, tested restore procedure
- API: HTTPS-only, rate limiting, input validation per Conexxus Open Retailing guidance

#### Advanced Observability (2-3 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| SLO monitoring (agent run latency, email delivery rate) | 1 week | P0 | High - Proactive operations |
| Operational dashboards (system health, job queue depth) | 1 week | P0 | High - Support efficiency |
| Platform-level health monitoring and alerts | 3 days | P0 | Very High - Uptime SLA |
| Distributed tracing (OpenTelemetry) | 1 week | P2 | Medium - Debugging complex flows |

**Deliverables:**
- SLOs: "95% of agent runs complete in <5min", "99% email delivery success"
- Dashboard: Grafana panels for job queue depth, DB query latency, API response times
- Alerts: "Platform health check failed 3x" → PagerDuty/Slack
- Tracing: span for each agent run with child spans for tool calls

#### Analytics & Reporting (4-6 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| KPI reporting (runout risk trend, carrier response SLA) | 2 weeks | P0 | High - Customer retention |
| Exception driver analysis (recurring pattern detection) | 2 weeks | P1 | High - Process improvement |
| Carrier performance scorecard | 1 week | P1 | Medium - Sourcing decisions |
| Export to Excel/PDF for executive reporting | 1 week | P2 | Medium - Stakeholder buy-in |

**Deliverables:**
- Reports: "Runout Risk Over Time" (line chart), "Carrier SLA Performance" (table + heatmap)
- Exception analysis: "Site X has runouts every Monday" → proactive scheduling suggestion
- Scorecard: average response time, on-time delivery %, communication quality
- Export: "Download Report" button → Excel with charts

#### Standards-Aware Schema (1-2 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Design product/terminal code tables compatible with PIDX | 1 week | P1 | Medium - Future integration leverage |
| Map internal load states to PIDX/Conexxus equivalents | 3 days | P2 | Medium - Interoperability |

**Deliverables:**
- `ProductCode` table: `code, description, pidx_mapping`
- `TerminalCode` table: `code, name, address, pidx_mapping`
- Load status enum: map `IN_TRANSIT` → PIDX "In Transit" concept
- Documentation: "Standards Alignment Guide" for future BOL integration

#### Governed Automation (1-2 weeks)

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Document escalation policies and approval workflows | 1 week | P0 | High - Safe automation |
| Add "require approval for X" config toggles | 3 days | P0 | High - Risk mitigation |
| Agent action audit report (what did agents do this week?) | 3 days | P1 | Medium - Transparency |

**Deliverables:**
- Policy doc: "Agents auto-escalate if runout <4hrs, auto-email carriers if >12hrs"
- Config: `require_approval_for_emails`, `require_approval_for_escalations` (per tenant)
- Report: "Agent Activity Summary" → CSV of all actions taken, grouped by type

**Phase 3 Exit Criteria:**
- ✅ Multi-tenant architecture with per-tenant isolation
- ✅ Security posture documentation for vendor risk assessments
- ✅ SLO monitoring and operational dashboards
- ✅ KPI reporting and exception analysis
- ✅ Standards-aligned schema for future interoperability
- ✅ **Procurement-ready for Type A chains with MSP/IT approval processes**

---

## Architecture Patterns: Data Plane vs Action Plane

**Key Principle:** Split the platform into a **data plane** (ingestion, normalization, quality) and an **action plane** (decisioning, execution, audit/HITL). This division lowers risk and improves incremental adoption.

```
DATA PLANE (truth + confidence)                   ACTION PLANE (decide + act + govern)
┌──────────────────────────────┐                 ┌──────────────────────────────────────┐
│ Inventory inputs             │                 │ Agent decision loop                  │
│ - CSV / Push API (Phase 1)   │                 │ - runout risk scoring                │
│ - ATG API (Phase 2+)         │                 │ - selects actions (email/escalate)   │
│ - Wetstock integrations (opt)│                 │ - applies safety rails + RBAC checks │
└───────────────┬──────────────┘                 └───────────────┬──────────────────────┘
                │                                                    │
                v                                                    v
┌──────────────────────────────┐                 ┌──────────────────────────────────────┐
│ Normalization & crosswalks    │                 │ Execution layer                      │
│ - site/tank/product IDs       │                 │ - email send + reply ingestion       │
│ - units + timestamps          │                 │ - escalation creation/resolution     │
│ - confidence scoring          │                 │ - activity/audit logs                │
└───────────────┬──────────────┘                 └───────────────┬──────────────────────┘
                │                                                    │
                v                                                    v
┌──────────────────────────────┐                 ┌──────────────────────────────────────┐
│ Data quality guards           │                 │ HITL operations UI                   │
│ - staleness + plausibility    │                 │ - dashboards, filters, reviews       │
│ - missing deliveries flags    │                 │ - role-based views                   │
└──────────────────────────────┘                 └──────────────────────────────────────┘
```

### Integration Complexity for Type A

**Hard Integration Surfaces:**

1. **Inventory Telemetry Heterogeneity**
   - ATG ecosystems are diverse (Veeder-Root, Dover, Gilbarco, etc.)
   - Each vendor has different API maturity levels
   - Requires IT/security approvals and device connectivity prerequisites
   - **Strategy:** Start with one ATG vendor, build connector pattern for expansion

2. **Security Scrutiny for Remote Access**
   - OT-adjacent devices raise cybersecurity concerns
   - CISA advisories emphasize minimizing exposure and VPN requirements
   - **Strategy:** Design for secure API patterns (OAuth2, API keys with rotation), document security controls

3. **Standards as Leverage, Not Immediate Requirement**
   - Open Retailing (Conexxus) API guidance shapes security/transport design
   - PIDX shapes product/terminal/BOL data modeling
   - **Strategy:** Design internal schema compatible with standards for future expansion, don't over-engineer for Day 1

---

## Deprioritizations (Anti-Roadmap)

**These features add complexity before trust is earned. Defer or avoid:**

### ❌ Deep ML Forecasting
- **Why defer:** Type A can get value from threshold-based runout risk + simple trend heuristics
- **When to revisit:** After 10+ customers with clean data for 6+ months

### ❌ Multi-Agent Orchestration Complexity
- **Why defer:** Core win is safe and reliable coordination, not agent hierarchies
- **When to revisit:** If specific customer requests hierarchical delegation (rare)

### ❌ Real-Time GPS Integrations
- **Why defer:** Many customers already have visibility vendors (FourKites, project44)
- **Strategy:** Start with email/CSV ETAs, add tracking later via partner APIs
- **When to revisit:** After Phase 2 when ETA accuracy issues are proven

### ❌ Full "Rack-to-Cash" Billing
- **Why defer:** Incumbents market this, but Type A adoption is faster if you remain an overlay
- **Strategy:** Focus on dispatch/inventory coordination, not replacing their accounting system
- **When to revisit:** If large expansion customer demands it (rare in Type A)

### ❌ Native Mobile Apps
- **Why defer:** Responsive web works for 90% of operator workflows
- **When to revisit:** After Phase 3 when field driver check-in becomes critical

---

## Technology Stack Recommendations

### Backend Infrastructure

**Current (MVP):** FastAPI + PostgreSQL + APScheduler + Docker
**Phase 1 Additions:**
- **Authentication:** `python-jose[cryptography]` for JWT, `passlib[bcrypt]` for password hashing
- **Email:** SendGrid or AWS SES SDK
- **Structured Logging:** `structlog` with JSON formatter

**Phase 2 Additions:**
- **Job Queue:** Celery + Redis (for reliability) OR Temporal (for enterprise-grade orchestration)
- **Observability:** Prometheus + Grafana, Sentry for error tracking
- **Database:** Add read replicas if query load grows

**Phase 3 Additions:**
- **Tracing:** OpenTelemetry with Jaeger/Tempo backend
- **Multi-Tenancy:** PostgreSQL row-level security (RLS) policies
- **Backups:** pgBackRest or AWS RDS automated backups

### Frontend Infrastructure

**Current (MVP):** React 18 + Vite + TanStack Query + TailwindCSS + Leaflet
**Phase 1 Additions:**
- **Auth State:** Zustand or React Context for auth tokens
- **Form Validation:** React Hook Form + Zod

**Phase 2 Additions:**
- **CSV Import UI:** react-dropzone + papaparse
- **Charts:** Recharts or Chart.js for analytics

**Phase 3 Additions:**
- **Multi-Tenant UI:** Tenant switcher dropdown (admin-only)
- **Export:** SheetJS (xlsx) for Excel export

---

## Success Metrics & Exit Criteria Summary

### Phase 1 Success Metrics
- ✅ 100% of API endpoints require authentication
- ✅ 100% of write operations enforce RBAC
- ✅ 0 emails sent without idempotency check
- ✅ <5min time-to-first-inventory-reading (via CSV)
- ✅ Health check uptime >99.5%

### Phase 2 Success Metrics
- ✅ <1% job failure rate after retries
- ✅ First ATG integration live with >95% uptime
- ✅ >80% carrier email replies successfully parsed
- ✅ <10% false positive escalations (due to stale data)
- ✅ <30sec onboarding wizard completion time

### Phase 3 Success Metrics
- ✅ Multi-tenant isolation tested with 3+ tenants
- ✅ Security questionnaire completed and approved by 1+ MSP
- ✅ SLO dashboard shows >95% on all KPIs
- ✅ >50% of Type A prospects reference analytics in sales demos
- ✅ Standards alignment documented and reviewed by 1+ industry expert

---

## Implementation Principles (Claude Code Team Guidance)

### Security and Identity
1. **Backend auth first** - Remove all production dependency on frontend-only auth
2. **Token hygiene** - Short-lived access tokens (15min), long-lived refresh tokens (7 days) with rotation
3. **RBAC enforcement** - Server-side on every write, agents respect RBAC semantics
4. **Standards alignment** - HTTPS-only, rate limiting, input validation per Open Retailing guides

### Integration Design
1. **Canonical schema** - `InventoryObservation` and `LoadStatusEvent` as single source of truth
2. **Connector pattern** - Each integration (CSV, ATG, email) outputs canonical events
3. **Provenance tracking** - Never overwrite truth without recording source + timestamp
4. **Standards-compatible** - Product/terminal codes map to PIDX concepts even if not fully used

### Reliability and Operations
1. **Durable execution** - Replace best-effort with retry + backoff + DLQ
2. **Idempotency** - Every agent action has a unique key (no duplicate emails)
3. **Agent heartbeat** - Monitor "last successful run" and alert on staleness
4. **Graceful degradation** - If ATG is down, CSV still works; if email fails, escalation still created

### Observability
1. **Structured events** - Log agent run start/finish, inputs, actions, failures
2. **Queryable in UI** - Operations team can see "why didn't agent run for Site X?"
3. **Health endpoints** - `/health`, `/ready` for uptime monitoring
4. **Metrics exposure** - Prometheus `/metrics` endpoint for job lag, failures, latency

### Governed Automation
1. **Execution modes** - Default to "draft outputs + operator approval" at onboarding
2. **Throttles by default** - Carrier comms are reputational risk; prevent spam
3. **Graduated autonomy** - Customer enables automation one action type at a time
4. **Audit everything** - Every automated action logged with decision context

### UX for Type A
1. **Guided onboarding** - Clear prerequisites: inventory connected → carriers configured → agents tested
2. **Bulk operations** - Small teams need efficiency (bulk ETA updates, bulk site edits)
3. **Fast triage** - "Top 5 at-risk sites" widget, one-click escalation creation
4. **Standards over magic** - Avoid over-automation; Type A wants control and visibility

---

## Competitive Positioning vs Incumbents

### What Incumbents Emphasize (from market research)
- **Veeder-Root:** Fuel inventory/delivery data API, integration with back-office, wetstock management
- **PDI Technologies:** Automated order management, real-time inventory monitoring, planning/dispatch
- **Titan Cloud:** Inventory visibility, demand trends, carrier exception reporting
- **SkyBitz:** Tank monitoring → automated order creation, ERP integration
- **Insite360:** Rack-to-cash including remote monitoring, dispatch, load tracking, eBOL

### Our Differentiation for Type A
1. **AI-First Dispatch** - Incumbents are rule-based; we use Claude for nuanced decision-making
2. **Faster Time-to-Value** - Start with CSV/email, mature to ATG; no 6-month implementation
3. **Modern UX** - React/TailwindCSS vs legacy enterprise UI
4. **Transparent AI** - Full HITL visibility into agent reasoning and actions
5. **Standards-Aligned** - Built with Open Retailing and PIDX compatibility from Day 1

### What We Don't Compete On (Intentionally)
- ❌ Full rack-to-cash billing and invoicing (remain an overlay)
- ❌ Deep wetstock reconciliation (partner with ATG vendors)
- ❌ Mobile driver apps (focus on dispatcher workflows)
- ❌ Multi-modal logistics (stay focused on fuel delivery)

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ATG vendor API is unstable/undocumented | Medium | High | Start with best-documented vendor (Veeder-Root), build fallback to CSV |
| Customer IT blocks ATG integration (firewall/VPN) | High | High | Offer "pull from cloud aggregator" alternative, document VPN setup |
| Email deliverability issues (spam filters) | Medium | High | Use reputable ESP (SendGrid), implement SPF/DKIM/DMARC, throttle sends |
| Customer data quality poor (garbage in) | High | Medium | Build confidence scoring + plausibility checks, train on data hygiene |
| Carrier adoption low (don't reply to emails) | Medium | High | Start with 1-2 cooperative carriers per customer, manual fallback |
| Security questionnaire blocks procurement | Medium | Very High | Complete Phase 1 security baseline first, prepare docs early |
| Type A budget constraints (can't pay $500/mo) | High | Medium | Offer freemium tier (5 sites free) or usage-based pricing |
| Over-automation creates customer distrust | Medium | Very High | Default to draft mode, graduated autonomy, full audit trails |

---

## Conclusion

This roadmap transforms the MVP into a **Type A enterprise-ready platform** by focusing on **trust, integration, and operability** rather than "more AI features."

**The unlock is not better algorithms—it's better data pipelines and safer execution.**

By following this phased approach:
- **Phase 1** builds trust through security, safety rails, and real (but simple) integrations
- **Phase 2** delivers credible integration story with ATG + reliable execution
- **Phase 3** achieves procurement-readiness for MSP-managed Type A chains

The result: a platform that **small fuel chains trust to run daily**, not just a demo system.

**Next Step:** Prioritize Phase 1 tasks and begin with backend authentication + RBAC implementation.
