# Railway Deployment Guide & Troubleshooting

## Architecture

```
Railway Project
  ├── backend    (Python/FastAPI, Dockerfile)
  ├── frontend   (React/Vite, Nixpacks + serve)
  └── Postgres   (Railway plugin)
```

## Required Environment Variables

### Backend Service
| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Reference to Railway Postgres plugin |
| `JWT_SECRET_KEY` | `<random 32+ char string>` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CORS_ORIGINS` | `https://frontend-production-xxxx.up.railway.app` | Your frontend Railway URL |
| `SENDGRID_API_KEY` | `SG.xxxx` | SendGrid API key (free: 100 emails/day) |
| `SENDGRID_FROM_EMAIL` | `noreply@yourdomain.com` | Verified sender in SendGrid |
| `SENDGRID_FROM_NAME` | `Fuels Logistics AI Coordinator` | Display name on outgoing emails |
| `GMAIL_USER` | `you@gmail.com` | Gmail address for IMAP polling (inbound only) |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Gmail App Password for IMAP polling |
| `DEBUG` | `false` | Set false for production |

### Frontend Service
| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `https://backend-production-xxxx.up.railway.app/api` | Must include `/api` suffix and `https://` prefix |

**Important**: `VITE_API_URL` is baked at build time. Changing it requires a redeploy (not just restart).

## Email Setup (SendGrid)

All outbound emails use **SendGrid HTTP API**. Railway blocks outbound SMTP (ports 25, 465, 587) on Hobby plan, so SMTP-based sending (Gmail, raw SMTP) will never work on Railway.

### SendGrid Setup
1. Create a free SendGrid account at https://sendgrid.com (100 emails/day free)
2. Verify a sender identity (Settings > Sender Authentication)
3. Create an API key (Settings > API Keys > Create API Key > Full Access)
4. Set these env vars on Railway backend:
   - `SENDGRID_API_KEY` = your API key
   - `SENDGRID_FROM_EMAIL` = your verified sender email
   - `SENDGRID_FROM_NAME` = display name (optional)

### Gmail IMAP (Inbound Only)
Gmail credentials (`GMAIL_USER`, `GMAIL_APP_PASSWORD`) are only used for the **email poller** that reads inbound carrier replies via IMAP. They are NOT used for sending.

## Deployment Errors & Fixes

### 1. Railpack: `failed to stat .../secrets/GMAIL_ENABLED`
**Error**: Railpack mounts all service variables as build-time secret files and fails when they're unavailable during build.

**Fix**: Added `backend/Dockerfile` so Railway uses Docker instead of Railpack. Docker only injects env vars at runtime, not build time.

### 2. `password cannot be longer than 72 bytes` (bcrypt)
**Error**: `passlib==1.7.4` is incompatible with `bcrypt>=4.1.0`. The newer bcrypt library changed its API, causing passlib to error even on short passwords like "admin123".

**Fix**: Pin `bcrypt==4.0.1` in `requirements.txt`.

### 3. `postgres://` vs `postgresql://`
**Error**: Railway Postgres plugin provides `postgres://` URL scheme, but SQLAlchemy 2.0 requires `postgresql://`.

**Fix**: Added `field_validator` in `app/config.py` that auto-replaces `postgres://` with `postgresql://`.

### 4. `npm ci` lock file mismatch
**Error**: Adding `serve` to `package.json` without updating `package-lock.json` caused `npm ci` to fail on Railway.

**Fix**: Run `npm install` locally to sync lock file, then commit both files.

### 5. `email-validator` missing
**Error**: Pydantic `EmailStr` requires the `email-validator` package which wasn't in `requirements.txt`.

**Fix**: Added `email-validator>=2.1.0` to `requirements.txt`.

### 6. Database empty — 401 on login
**Error**: Seed script didn't create `User` records on first deploy, so login always returned 401.

**Fix**: Added user creation to `seed_data.py` and auto-seed logic in `main.py` lifespan that checks `User.count() == 0`.

### 7. `GMAIL_ENABLED=true` not parsed as boolean
**Error**: Pydantic-settings on Railway wasn't parsing the `GMAIL_ENABLED` env var as `True`.

**Fix**: Removed `GMAIL_ENABLED` flag entirely. Email sending now uses SendGrid HTTP API which auto-enables when `SENDGRID_API_KEY` is set.

### 8. `[Errno 101] Network is unreachable` (Gmail SMTP)
**Error**: `smtplib.SMTP` connections to `smtp.gmail.com` (ports 465, 587) fail on Railway Hobby plan.

**Root cause**: Railway Hobby plan has a hard firewall block on ALL outbound SMTP traffic (ports 25, 465, 587). No amount of STARTTLS, IPv4 forcing, or timeout tuning will fix this.

**Fix**: Replaced all SMTP-based email sending with **SendGrid HTTP API** (`sendgrid` Python library). HTTP requests (port 443) are not blocked.

### 9. Hardcoded `localhost:8000` in frontend
**Error**: `LoadDetailsSidebar` component had a hardcoded `fetch('http://localhost:8000/api/loads/active')` that bypassed the API client (no auth token, wrong URL in production).

**Fix**: Replaced with `getActiveLoads()` from the API client which uses `VITE_API_URL` and sends the auth token.

### 10. Railway blocks ALL outbound SMTP on Hobby plan
**Error**: After trying SMTP_SSL:465, STARTTLS:587, and IPv4-forced connections, all failed with `[Errno 101] Network is unreachable`.

**Root cause**: Railway intentionally blocks outbound SMTP on Hobby plan to prevent spam. This is documented in their community forums. Only Pro plan ($20/mo) unblocks SMTP.

**Fix**: Consolidated all email sending to SendGrid HTTP API. Removed Gmail SMTP (`app/integrations/email_service.py`), Gmail OAuth API (`app/integrations/gmail_service.py`), and mock email code paths. Single email service at `app/services/email_service.py`.

## Auto-Seed Behavior

On first deploy (empty database), the backend automatically:
1. Creates tables via SQLAlchemy
2. Seeds users (admin/admin123, coordinator/fuel2024)
3. Seeds carriers, sites, lanes, loads
4. Adds GPS tracking data to loads

This runs once — subsequent deploys skip seeding if users exist.
