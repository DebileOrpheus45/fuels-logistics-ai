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
| `GMAIL_USER` | `you@gmail.com` | Gmail address for sending emails |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Gmail App Password (not regular password) |
| `DEBUG` | `false` | Set false for production |

### Frontend Service
| Variable | Example | Notes |
|----------|---------|-------|
| `VITE_API_URL` | `https://backend-production-xxxx.up.railway.app/api` | Must include `/api` suffix and `https://` prefix |

**Important**: `VITE_API_URL` is baked at build time. Changing it requires a redeploy (not just restart).

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
**Error**: Pydantic-settings on Railway wasn't parsing the `GMAIL_ENABLED` env var as `True` despite being set correctly. Root cause unclear (possibly Railway/Docker env var encoding).

**Fix**: Changed `EmailService.__init__` to auto-enable Gmail when `GMAIL_USER` and `GMAIL_APP_PASSWORD` are both set, removing dependency on the boolean flag.

### 8. `[Errno 101] Network is unreachable` (Gmail SMTP)
**Error**: `smtplib.SMTP_SSL` on port 465 fails inside Railway Docker containers. The container can't establish a direct SSL connection to `smtp.gmail.com:465`.

**Fix**: Switched to `smtplib.SMTP` on port 587 with `STARTTLS`. Port 587 is the standard email submission port and is more compatible with containerized environments.

### 9. Hardcoded `localhost:8000` in frontend
**Error**: `LoadDetailsSidebar` component had a hardcoded `fetch('http://localhost:8000/api/loads/active')` that bypassed the API client (no auth token, wrong URL in production).

**Fix**: Replaced with `getActiveLoads()` from the API client which uses `VITE_API_URL` and sends the auth token.

## Gmail App Password Setup

1. Go to Google Account > Security > 2-Step Verification
2. Scroll to "App passwords" at the bottom
3. Generate one for "Mail"
4. Use the 16-character password as `GMAIL_APP_PASSWORD`

## Auto-Seed Behavior

On first deploy (empty database), the backend automatically:
1. Creates tables via SQLAlchemy
2. Seeds users (admin/admin123, coordinator/fuel2024)
3. Seeds carriers, sites, lanes, loads
4. Adds GPS tracking data to loads

This runs once — subsequent deploys skip seeding if users exist.
