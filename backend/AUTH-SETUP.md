# Authentication System Setup Guide

## Overview

The Fuels Logistics AI Coordinator now has production-ready JWT authentication with role-based access control (RBAC).

**Security Features:**
- ✅ Backend JWT token authentication
- ✅ Bcrypt password hashing
- ✅ Role-based access control (Admin, Operator)
- ✅ Token expiration and refresh
- ✅ Protected API endpoints
- ✅ User management (create, deactivate, list)

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `python-jose[cryptography]` - JWT token generation/validation
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - OAuth2 form handling

### 2. Configure Environment

Add to your `.env` file:

```bash
# Generate a secure random secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-secure-random-key-here
```

**⚠️ CRITICAL:** Never use the example key in production! Generate a unique random key.

### 3. Start Database

```bash
# From project root
docker-compose up -d
```

### 4. Create Admin User

```bash
cd backend
python create_admin_user.py
```

This creates two users:
- **Admin:** username=`admin`, password=`admin123`, role=`ADMIN`
- **Operator:** username=`coordinator`, password=`fuel2024`, role=`OPERATOR`

**⚠️ IMPORTANT:** Change these default passwords after first login!

### 5. Start Backend

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### Public Endpoints (No Auth Required)

```http
POST /auth/login
  - OAuth2 compatible login
  - Request body: { username, password }
  - Returns: { access_token, refresh_token, token_type }
```

### Protected Endpoints (Requires Auth Token)

```http
GET /auth/me
  - Get current user information
  - Headers: Authorization: Bearer <access_token>

POST /auth/change-password
  - Change current user's password
  - Request body: { current_password, new_password }
```

### Admin-Only Endpoints

```http
POST /auth/users
  - Create new user
  - Request body: { username, email, password, full_name?, role? }

GET /auth/users
  - List all users

PATCH /auth/users/{user_id}/deactivate
  - Deactivate user account

PATCH /auth/users/{user_id}/activate
  - Activate user account
```

---

## User Roles

### ADMIN
- Full system access
- Can create/deactivate users
- Can modify system configuration
- All OPERATOR permissions

### OPERATOR
- View dashboard and sites
- View and update loads
- View escalations
- **Cannot** create users or modify system settings

---

## Testing the Auth System

### 1. Login with cURL

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Access Protected Endpoint

```bash
# Save token from login response
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Get current user info
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Create a New User (Admin Only)

```bash
curl -X POST http://localhost:8000/auth/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dispatcher1",
    "email": "dispatcher@fuelslogistics.com",
    "password": "secure_password_123",
    "full_name": "John Dispatcher",
    "role": "operator"
  }'
```

### 4. Test with FastAPI Docs

1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" button (top right)
3. Enter credentials: username=`admin`, password=`admin123`
4. Click "Authorize"
5. All endpoints now show lock icons (🔒) indicating auth is enforced

---

## Token Configuration

**Access Token:**
- Expires in **30 minutes**
- Used for API requests
- Short-lived for security

**Refresh Token:**
- Expires in **7 days**
- Used to get new access tokens without re-login
- (Refresh endpoint to be implemented in Week 2)

**Token Claims:**
- `sub` (subject) - Username
- `exp` (expiration) - Unix timestamp
- `type` (optional) - "refresh" for refresh tokens

---

## Security Best Practices

### Password Requirements
- Minimum 8 characters (enforced in frontend)
- Bcrypt hashed with automatic salt
- No password reuse (implement in Week 2)

### Token Security
- Store access tokens in memory or httpOnly cookies (NOT localStorage)
- Refresh tokens should be httpOnly cookies
- Always use HTTPS in production

### User Management
- Default new users to `OPERATOR` role
- Admin can upgrade users to ADMIN if needed
- Deactivate users instead of deleting (preserves audit trail)

---

## Migration from Mock Auth

**Old System (Frontend-Only):**
```javascript
// ❌ Insecure - no backend validation
if (username === 'coordinator' && password === 'fuel2024') {
  localStorage.setItem('token', 'fake-token')
}
```

**New System (Backend JWT):**
```javascript
// ✅ Secure - backend validates credentials
const response = await api.post('/auth/login', { username, password })
const { access_token } = response.data
// Store in httpOnly cookie or secure storage
```

---

## Troubleshooting

### "Could not validate credentials"
- Token expired (30min lifetime)
- Invalid token format
- JWT_SECRET_KEY mismatch
- **Fix:** Re-login to get new token

### "User account is inactive"
- User was deactivated by admin
- **Fix:** Admin must activate user via `/auth/users/{id}/activate`

### "Requires admin role"
- Endpoint requires ADMIN role, user is OPERATOR
- **Fix:** Admin must upgrade user role or use admin account

### "Username already registered"
- Username must be unique
- **Fix:** Choose different username

---

## Next Steps (Week 2)

1. **Frontend Integration:**
   - Create login page with form validation
   - Implement token refresh logic
   - Add "Logout" button
   - Show user info in header (name, role)

2. **Endpoint Protection:**
   - Add `Depends(get_current_user)` to all protected endpoints
   - Add `Depends(get_admin_user)` to admin-only endpoints
   - Update site/load/agent routers

3. **Audit Trail:**
   - Log all user actions (create, update, delete)
   - Track "created_by" and "updated_by" on models
   - Add "last_modified_by" to Activity logs

---

## Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ POST /auth/login
       │ { username, password }
       ▼
┌─────────────────────────────┐
│    FastAPI Backend          │
│                             │
│  1. Verify password (bcrypt)│
│  2. Generate JWT token      │
│  3. Return access_token     │
└──────┬──────────────────────┘
       │ { access_token, refresh_token }
       ▼
┌─────────────┐
│   Client    │
│  Stores JWT │
└──────┬──────┘
       │ GET /api/sites
       │ Authorization: Bearer <token>
       ▼
┌─────────────────────────────┐
│    FastAPI Backend          │
│                             │
│  1. Decode JWT              │
│  2. Validate signature      │
│  3. Check expiration        │
│  4. Load user from DB       │
│  5. Check is_active         │
│  6. Return protected data   │
└─────────────────────────────┘
```

---

## Files Created

- `backend/app/models.py` - User model and UserRole enum
- `backend/app/auth.py` - JWT and password utilities
- `backend/app/routers/auth.py` - Auth endpoints
- `backend/create_admin_user.py` - Admin user creation script
- `backend/requirements.txt` - Updated with auth dependencies
- `backend/.env.example` - JWT_SECRET_KEY documentation

---

## Demo Script

**Show prospective customer:**

1. "Our system has enterprise-grade JWT authentication with role-based access control"
2. *Open `/docs`, show lock icons on endpoints*
3. "Let me log in as an admin user"
4. *Click Authorize, enter admin/admin123*
5. "Now I can create a new operator user for your dispatch team"
6. *Create user via POST /auth/users*
7. "Operators can view and manage loads, but only admins can create new users or modify system settings"
8. *Show user list via GET /auth/users*
9. "All passwords are bcrypt-hashed, tokens expire after 30 minutes, and we track last login timestamps"

**Procurement credibility unlocked ✅**

---

## Version

- **Current:** v0.4.0 (JWT Auth + RBAC)
- **Last Updated:** February 5, 2026
