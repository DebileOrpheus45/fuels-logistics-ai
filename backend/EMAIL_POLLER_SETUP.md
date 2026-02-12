# Gmail ETA Reply Poller - Setup Guide

## Overview
The Gmail IMAP poller automatically checks your Gmail inbox for carrier ETA replies, parses ETAs using LLM (Claude Haiku) with regex fallback, stores every inbound email for audit, updates load ETAs in the database, and logs activity to the Agent Activity Stream — all without manual intervention.

## Prerequisites

### 1. Gmail App Password (Required)
You **cannot** use your regular Gmail password. You must create an "App Password":

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Click "Select app" → Choose "Other (Custom name)"
4. Enter name: "Fuels Logistics API"
5. Click "Generate"
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
7. **Save this password** - you won't see it again!

### 2. Environment Variables
Add to your `.env` file in the `backend/` directory:

```env
# Gmail IMAP Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop  # 16-char app password (no spaces)
```

**Note:** The app password should have no spaces (remove them when copying).

## How It Works

```
Agent sends email: "PO-2024-001, what's your ETA?"
    ↓
Dispatcher replies via email: "Driver arriving between 0400-0745"
    ↓
IMAP poller checks inbox (every 30 seconds)
    ↓
Finds unread email with subject "RE: ETA Request - PO-2024-001"
    ↓
Extracts subject, body, sender
    ↓
Calls POST /api/email/inbound with parsed content
    ↓
LLM parser (Claude Haiku) extracts PO and ETA, regex fallback if LLM unavailable
    ↓
InboundEmail record saved (audit trail with parse method + result)
    ↓
Activity logged to Agent Activity Stream (EMAIL_RECEIVED)
    ↓
Database updated: PO-2024-001.current_eta = 7:45 AM
    ↓
Email marked as read (won't be processed again)
    ↓
Frontend shows inbound email in Emails > Received tab + Agent Monitor stream
```

## Starting the Poller

### Option 1: Standalone Service (Recommended)
```bash
cd backend
python start_email_poller.py
```

Output:
```
================================================================================
Gmail ETA Reply Poller - Starting
================================================================================

This service will:
  - Check Gmail inbox every 10 minutes
  - Process carrier ETA replies (subject contains 'RE: ETA' or PO number)
  - Update load ETAs automatically
  - Mark processed emails as read

Press Ctrl+C to stop
================================================================================

2026-01-25 09:00:00 - email_poller - INFO - Starting Gmail ETA poller...
2026-01-25 09:00:00 - email_poller - INFO - Connecting to Gmail IMAP...
2026-01-25 09:00:00 - email_poller - INFO - Successfully connected to Gmail IMAP
2026-01-25 09:00:01 - email_poller - INFO - Found 2 unread email(s)
2026-01-25 09:00:01 - email_poller - INFO - Processing email: RE: ETA Request - PO-2024-001...
2026-01-25 09:00:02 - email_poller - INFO - ✓ Successfully processed: ETA updated from 2026-01-25 10:30:00 to 2026-01-25 14:30
```

### Option 2: As Python Module
```bash
cd backend
python -m app.services.email_poller
```

## Configuration

Edit `backend/app/services/email_poller.py` to customize:

```python
poller = GmailETAPoller(
    email_address=email_address,
    password=password,
    check_interval=30,  # 30 seconds (default; change to 300 for 5 min, 600 for 10 min)
    api_base_url="http://localhost:8000"  # Change if API runs on different port
)
```

### ETA Parsing

The parser uses a two-tier approach:
1. **LLM (Claude Haiku)** — primary parser, handles natural language like "between 4 and 7:45 AM tomorrow"
2. **Regex fallback** — if `ANTHROPIC_API_KEY` is not set or LLM fails

The API key is read from `Settings` (via `.env`), not from `os.environ` directly.

### Data Storage

Every inbound email is stored in the `inbound_emails` table with:
- Raw email content (from, subject, body)
- Extracted PO number and parsed ETA
- Parse method used (`llm` or `regex`) and success flag
- Timestamps (received, processed)

An `Activity` record (type `EMAIL_RECEIVED`) is also created for the Agent Activity Stream.

## Email Detection Rules

The poller processes emails that match ANY of these patterns:

| Pattern | Example |
|---------|---------|
| Subject contains "RE: ETA" | `RE: ETA Request - PO-2024-001` |
| Subject contains "Re: ETA" | `Re: ETA for PO-2024-002` |
| Subject contains PO number | `RE: Load PO-2024-003` |

**Only unread emails are processed** - emails are marked as read after processing to prevent duplicates.

## Testing

### 1. Send Test Email to Yourself
1. Send email to your Gmail account with:
   - Subject: `RE: ETA Request - PO-2024-001`
   - Body: `1430`
2. Leave email unread
3. Start the poller
4. Check logs for processing confirmation
5. Check database: `curl http://localhost:8000/api/loads/active | grep PO-2024-001`

### 2. Simulate Dispatcher Reply
Have someone send you an email:
```
To: your-email@gmail.com
Subject: RE: ETA Request - PO-2024-001
Body: between 1400 and 1600
```

The poller will:
- Extract PO: `PO-2024-001`
- Parse time range: `1400-1600`
- Use worst-case: `1600` (4:00 PM)
- Update database
- Mark email as read

## Troubleshooting

### Error: "Failed to connect to Gmail IMAP"
**Cause:** Invalid credentials or app password not enabled

**Fix:**
1. Verify `GMAIL_USER` is correct in `.env`
2. Verify `GMAIL_APP_PASSWORD` has no spaces
3. Generate new app password at https://myaccount.google.com/apppasswords
4. Ensure 2-factor authentication is enabled on your Google account

### Error: "Gmail credentials not configured"
**Cause:** `.env` file missing or variables not set

**Fix:**
```bash
cd backend
cat .env  # Check if GMAIL_USER and GMAIL_APP_PASSWORD are present
```

### Poller Not Processing Emails
**Cause:** Email subject doesn't match detection patterns

**Fix:**
- Ensure subject contains "RE: ETA" or a PO number
- Check logs to see what emails were found
- Email must be UNREAD

### Processed But ETA Not Updated
**Cause:** Parser couldn't extract PO or time

**Check API logs:**
```bash
# The backend logs will show:
POST /api/email/inbound - "success": false, "message": "Could not extract PO number"
```

**Fix:**
- Ensure subject or body contains PO number in format: `PO-2024-001`
- Ensure body contains valid time format (see supported formats in INGESTION-ROADMAP.md)

## Running in Production

### Option 1: systemd Service (Linux)
Create `/etc/systemd/system/fuels-email-poller.service`:
```ini
[Unit]
Description=Fuels Logistics Gmail ETA Poller
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/fuels-logistics-ai/backend
ExecStart=/usr/bin/python3 start_email_poller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fuels-email-poller
sudo systemctl start fuels-email-poller
sudo systemctl status fuels-email-poller
```

### Option 2: Windows Service (Windows)
Use NSSM (Non-Sucking Service Manager):
```bash
nssm install FuelsEmailPoller "C:\Python312\python.exe" "C:\path\to\backend\start_email_poller.py"
nssm start FuelsEmailPoller
```

### Option 3: Docker Container
Add to `docker-compose.yml`:
```yaml
services:
  email-poller:
    build: ./backend
    command: python start_email_poller.py
    env_file: ./backend/.env
    depends_on:
      - api
    restart: always
```

## Security Notes

1. **Never commit `.env` to git** - App passwords are sensitive
2. **Use app passwords, not regular passwords** - More secure, can be revoked
3. **Rotate app passwords periodically** - Generate new ones every 90 days
4. **Restrict Gmail API access** - Only enable IMAP, disable unused features

## Monitoring

Check poller health:
```bash
# Check if process is running
ps aux | grep email_poller

# View recent logs
tail -f /var/log/fuels-email-poller.log  # If using systemd

# Test API endpoint manually
curl -X POST http://localhost:8000/api/email/inbound/test \
  -H "Content-Type: application/json" \
  -d '{"subject":"RE: ETA Request - PO-2024-001","body":"1430","from_email":"test@example.com"}'
```

## API Endpoints

### Inbound Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/email/inbound` | Process an inbound carrier email (called by poller) |
| `GET`  | `/api/email/inbound` | List recent inbound emails (for frontend Received tab) |
| `POST` | `/api/email/inbound/test` | Test ETA parsing without saving to DB |

### Activity Stream
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/agents/activities/all` | All activities (email sent/received, escalations, etc.) |

## Frontend Integration

- **Emails tab → Received**: Shows all inbound emails with parse status badges (Parsed / Needs Review), PO number, and parsed ETA
- **Agent Monitor → Activity Stream**: Real-time feed of all email activity (sent and received), escalations, and agent actions — auto-refreshes every 15 seconds
- Activities with no agent (system-level, like email polling) show a "System" badge

## Cost
**$0** - Gmail IMAP is completely free with no rate limits for normal use.
LLM parsing uses Claude Haiku (~$0.001 per email parsed).
