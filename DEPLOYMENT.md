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
| `RESEND_API_KEY` | `re_xxxx` | Resend API key (free: 3,000 emails/month) |
| `RESEND_FROM_EMAIL` | `onboarding@resend.dev` | Verified domain sender (or Resend test address) |
| `RESEND_FROM_NAME` | `Fuels Logistics AI Coordinator` | Display name on outgoing emails |
| `GMAIL_USER` | `you@gmail.com` | Gmail address for IMAP polling (inbound only) |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Gmail App Password for IMAP polling |
| `DEBUG` | `false` | Set false for production |

### Frontend Service
| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `https://backend-production-xxxx.up.railway.app/api` | Must include `/api` suffix and `https://` prefix |

**Important**: `VITE_API_URL` is baked at build time. Changing it requires a redeploy (not just restart).

## Email Setup (Resend)

All outbound emails use **Resend HTTP API**. Railway blocks outbound SMTP (ports 25, 465, 587) on Hobby plan, so SMTP-based sending (Gmail, raw SMTP) will never work on Railway.

### Resend Setup
1. Create a free Resend account at https://resend.com (3,000 emails/month free)
2. Add and verify a domain, or use `onboarding@resend.dev` for testing
3. Create an API key (API Keys page)
4. Set these env vars on Railway backend:
   - `RESEND_API_KEY` = your API key (starts with `re_`)
   - `RESEND_FROM_EMAIL` = your verified domain email (or `onboarding@resend.dev`)
   - `RESEND_FROM_NAME` = display name (optional)

### Gmail IMAP (Inbound Only)
Gmail credentials (`GMAIL_USER`, `GMAIL_APP_PASSWORD`) are used for the **email poller** that reads inbound carrier replies via IMAP. They are NOT used for sending.

The email poller now starts automatically as a **background thread** inside the FastAPI process on startup. No separate service or Procfile worker needed. It checks Gmail every 2 minutes for unread ETA replies and processes them via the `/api/email/inbound` endpoint.

If `GMAIL_USER` or `GMAIL_APP_PASSWORD` are not set, the poller is silently disabled — everything else works normally.

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

**Fix**: Removed `GMAIL_ENABLED` flag entirely. Email sending now uses Resend HTTP API which auto-enables when `RESEND_API_KEY` is set.

### 8. `[Errno 101] Network is unreachable` (Gmail SMTP)
**Error**: `smtplib.SMTP` connections to `smtp.gmail.com` (ports 465, 587) fail on Railway Hobby plan.

**Root cause**: Railway Hobby plan has a hard firewall block on ALL outbound SMTP traffic (ports 25, 465, 587). No amount of STARTTLS, IPv4 forcing, or timeout tuning will fix this.

**Fix**: Replaced all SMTP-based email sending with **Resend HTTP API** (`resend` Python library). HTTP requests (port 443) are not blocked.

### 9. Hardcoded `localhost:8000` in frontend
**Error**: `LoadDetailsSidebar` component had a hardcoded `fetch('http://localhost:8000/api/loads/active')` that bypassed the API client (no auth token, wrong URL in production).

**Fix**: Replaced with `getActiveLoads()` from the API client which uses `VITE_API_URL` and sends the auth token.

### 10. Railway blocks ALL outbound SMTP on Hobby plan
**Error**: After trying SMTP_SSL:465, STARTTLS:587, and IPv4-forced connections, all failed with `[Errno 101] Network is unreachable`.

**Root cause**: Railway intentionally blocks outbound SMTP on Hobby plan to prevent spam. Only Pro plan ($20/mo) unblocks SMTP.

**Fix**: Consolidated all email sending to Resend HTTP API. Removed Gmail SMTP, Gmail OAuth API, SendGrid, and mock email code paths. Single email service at `app/services/email_service.py`.

### 11. Email poller only running locally, not on Railway
**Error**: Carrier email replies were only processed when the local machine was powered on. Replies sent overnight sat unprocessed until morning.

**Root cause**: The email poller (`start_email_poller.py`) was a standalone process that had to be run manually. It was not included in the Dockerfile, Procfile, or the FastAPI lifespan — so it never ran on Railway.

**Fix**: Integrated the poller as a background daemon thread in the FastAPI lifespan (`main.py`). It now starts automatically when the backend boots on Railway. Uses `threading.Event` for graceful shutdown. `api_base_url` uses `PORT` env var (Railway-assigned) instead of hardcoded `8000`.

## Auto-Seed Behavior

On first deploy (empty database), the backend automatically:
1. Creates tables via SQLAlchemy
2. Seeds users (admin/admin123, coordinator/fuel2024)
3. Seeds carriers, sites, lanes, loads
4. Adds GPS tracking data to loads

This runs once — subsequent deploys skip seeding if users exist.
