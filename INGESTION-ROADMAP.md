# Automated Ingestion Roadmap

## Overview
This document tracks planned automated ingestion channels to eliminate manual hourly intervention.

---

## Completed Features ✅

### Carrier ETA Email Reply Parser
**Status:** ✅ IMPLEMENTED (Jan 2026)

**Purpose:** Automatically parse carrier dispatcher email replies to ETA requests and update load ETAs in the database.

**Supported Formats:**
| Format | Example | Parsed Result |
|--------|---------|---------------|
| Military time | `0600`, `1500` | 6:00 AM, 3:00 PM |
| 12-hour with minutes | `3:00 PM`, `10:30 AM` | 3:00 PM, 10:30 AM |
| Simple AM/PM | `3 PM`, `10 AM` | 3:00 PM, 10:00 AM |
| Time ranges (military) | `between 1200 and 1400` | 2:00 PM (worst-case) |
| Time ranges (12-hour) | `1-3 PM` | 3:00 PM (worst-case) |
| Vague responses | `running late`, `delayed` | Flagged for manual follow-up |

**API Endpoints:**
- `POST /api/email/inbound/test` - Test parsing without DB update
- `POST /api/email/inbound` - Parse and update load ETA

**Files:**
- `backend/app/utils/email_parser.py` - Core parsing logic
- `backend/app/routers/email_inbound.py` - API endpoints
- `backend/app/services/email_poller.py` - Gmail IMAP polling service
- `backend/start_email_poller.py` - Poller startup script
- `backend/demo_email_parser.py` - Demo script

**Safety Features:**
- Time ranges use LATER time as worst-case scenario
- Vague responses return `success: false` for escalation
- PO number auto-extraction from subject/body

**Gmail IMAP Automation:** ✅ IMPLEMENTED
- Polls Gmail inbox every 10 minutes (configurable)
- Processes unread emails with "RE: ETA" or PO numbers in subject
- Automatically updates database and marks emails as read
- Uses Gmail App Password (secure authentication)
- Runs as standalone background service

**How to Start Email Polling:**
```bash
cd backend
python start_email_poller.py
```

**Next Steps for This Feature:**
- Webhook receiver for real-time email forwarding (optional)
- Integration into agent ETA request workflow
- Escalation creation for vague responses

---

## Current State (Manual Upload)

### CSV Batch Upload via UI
- CSV batch upload via UI
- Overwrites site configurations
- No versioning or deduplication

---

## Phase 1: Email Ingestion (Planned)

### Scheduled Inventory Reports
**Use Case:** Daily/hourly automated emails with inventory snapshots

**Ingestion Methods:**
1. CSV/XLSX attachments
2. Plain-text body parsing
3. Forwarded email chains

**Requirements:**
- Email polling (IMAP/Gmail API)
- Attachment extraction
- CSV parsing (same format as manual upload)
- Timestamp attribution
- Source tracking

**Challenges:**
- Format variations across senders
- Email threading/forwards
- Attachment naming conventions

---

### Alarm/Threshold Notification Emails
**Use Case:** System-generated alerts from upstream monitoring

**Example Triggers:**
- "Low Inventory Alert - SITE001"
- "Tank Level Below 20% - SITE-ATL-001"
- "Abnormal Consumption Detected"

**Requirements:**
- Subject line parsing
- Alarm type classification
- Site ID extraction
- Severity mapping
- Deduplication (same alarm resent)

**Parsing Strategy:**
- Regex patterns for subject lines
- Body text extraction (percentage, gallons, site code)
- Fallback to manual escalation if unparseable

**Example Patterns:**
```
Subject: "Alert: SITE001 Low Inventory"
Body: "Tank level at 15% (1,200 gallons). Estimated runout: 18 hours."

Extract:
- site_code: "SITE001"
- current_inventory: 1200
- hours_to_runout: 18
- alert_type: "low_inventory"
```

---

### Carrier ETA Reply Parsing ✅ (Implemented)
**Use Case:** Dispatcher replies to agent ETA requests

**Implemented:** See [backend/app/utils/email_parser.py](backend/app/utils/email_parser.py)

**Supported Formats:**
- Single time: "0600", "1500", "3:00 PM"
- Time ranges: "between 1200 and 1400", "1-3 PM"
- Vague responses: "running late", "delayed"

**Safety:** Always uses later time in range as worst-case scenario

---

## Phase 2: File Drop Integrations (Future)

### Google Sheets Auto-Sync
**Use Case:** Living spreadsheet updated by external scripts/automation

**Requirements:**
- Google Sheets API integration
- Scheduled polling (e.g., every 15 minutes)
- Change detection (compare checksums or lastModified)
- Row-by-row diff to avoid full overwrites

**Implementation:**
- OAuth2 authentication
- Read-only access to shared sheet
- Map columns to site snapshot schema
- Preserve manual overrides

---

### SFTP File Drops
**Use Case:** Upstream system writes CSV/XLSX to SFTP server

**Requirements:**
- SFTP client library (paramiko)
- Directory watcher (poll for new files)
- File naming conventions (timestamp-based)
- Archive processed files

**Workflow:**
1. Poll SFTP directory every 5-15 minutes
2. Download new files
3. Parse and ingest
4. Move to `/processed/` directory
5. Delete after retention period

---

### Cloud Storage Webhooks
**Use Case:** Trigger-based ingestion from S3, Google Drive, Azure Blob

**Requirements:**
- Webhook endpoint to receive file upload notifications
- Authentication (API keys, signed URLs)
- Download and parse file
- Idempotency (same file uploaded twice)

**Supported Services:**
- Google Drive (watch for folder changes)
- AWS S3 (S3 event notifications → Lambda → webhook)
- Dropbox (webhook API)

---

## Phase 3: Advanced Integrations (Future)

### API Polling (If Available)
**Use Case:** Direct API from upstream inventory management system

**Examples:**
- FuelQuest API
- Fuel Shepherd API
- TMS vendor APIs

**Requirements:**
- API client library
- Authentication (API keys, OAuth)
- Rate limiting
- Error handling and retries
- Schema mapping

**Note:** This is explicitly **NOT** a dependency - system must work without APIs.

---

## Technical Requirements (All Channels)

### Idempotency
- Same input ingested twice = same output
- Use content hash or timestamp to detect duplicates
- Don't create duplicate escalations

### Timestamping
- Every snapshot must have `ingested_at` timestamp
- Track source channel (email, sftp, manual, etc.)
- Preserve original timestamp if available

### Source Attribution
- Track where data came from
- Support audit trail ("who uploaded this?")
- Enable debugging ("why did this change?")

### Staleness Detection
- Missing expected ingestion is a signal
- Track `last_ingestion_at` per site
- Escalate if data stops arriving

### Failure Handling
- Partial ingestion failure must not corrupt state
- Unparseable data must create alert, not crash
- Fallback to manual upload if automation fails

---

## Implementation Priority

**Now:**
1. ✅ Carrier ETA reply parsing (implemented this session)

**Next (Phase 1):**
2. Email attachment parsing (CSV/XLSX)
3. Google Sheets integration
4. Alarm email parsing

**Later (Phase 2):**
5. SFTP file drops
6. Cloud storage webhooks

**Future (Phase 3):**
7. Vendor API integrations (if available)

---

## Safety Constraints

### Demo Mode Isolation
- All automated ingestion must respect `DEMO_MODE` flag
- Demo emails must use separate inbox
- Demo data must be session-scoped

### Email Allowlisting
- Inbound email parsing must validate sender
- Only process emails from trusted domains
- Reject/quarantine suspicious sources

### Rate Limiting
- Polling intervals must be configurable
- Don't hammer external APIs
- Back off on repeated failures

---

**Last Updated:** January 25, 2026
**Status:** Planning document - most features not yet implemented
