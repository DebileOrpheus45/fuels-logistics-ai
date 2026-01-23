# Frontend Switcher Guide

This project includes two frontends that you can hotswap between:
- **Base_v1** (Original modern design)
- **MGClone_v1** (MercuryGate TMS-inspired design)

Both frontends connect to the same backend API.

---

## Quick Reference

| Frontend | Port | Style | When to Use |
|----------|------|-------|-------------|
| **Base_v1** | 5173 | Modern, card-based SaaS | Daily operations, mobile-friendly |
| **MGClone_v1** | 5174 | Enterprise TMS, table-based | Control tower view, executive dashboards |

---

## Running Both Frontends Simultaneously

You can run both frontends at the same time and switch between them in your browser.

### Setup

**Terminal 1 - Backend:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Base_v1 Frontend:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\frontend
npm run dev
# Runs on http://localhost:5173
```

**Terminal 3 - MGClone_v1 Frontend:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\MGClone_v1
npm install  # First time only
npm run dev
# Runs on http://localhost:5174
```

Now you can switch between:
- **Base_v1**: http://localhost:5173
- **MGClone_v1**: http://localhost:5174

Both use the same login (coordinator / fuel2024) and the same backend data.

---

## Running Only One Frontend at a Time

If you prefer to run only one frontend to save resources:

### Option 1: Use Base_v1 (Original)
```bash
cd C:\Users\vsubb\fuels-logistics-ai\frontend
npm run dev
```
Access: http://localhost:5173

### Option 2: Use MGClone_v1 (MercuryGate Style)
```bash
cd C:\Users\vsubb\fuels-logistics-ai\MGClone_v1
npm run dev
```
Access: http://localhost:5174

---

## Renaming for True Hotswapping

If you want to actually rename the directories and swap them (not recommended unless you have a specific reason):

### Current Structure
```
fuels-logistics-ai/
├── frontend/          # Base_v1 (port 5173)
├── MGClone_v1/        # MGClone (port 5174)
└── backend/
```

### To Rename Frontend to Base_v1
**WARNING: Stop all frontends first!**

```bash
cd C:\Users\vsubb\fuels-logistics-ai

# Stop any running npm processes first
# Then rename
mv frontend Base_v1

# Update package.json in Base_v1 if needed
```

### To Make MGClone_v1 the Default Frontend
**WARNING: Stop all frontends first!**

```bash
cd C:\Users\vsubb\fuels-logistics-ai

# Option A: Rename for clarity
mv frontend Base_v1
mv MGClone_v1 frontend

# Option B: Create symbolic link (advanced)
# Not recommended on Windows without admin privileges
```

---

## When to Use Each Frontend

### Use Base_v1 When:
- ✅ You want a modern, clean interface
- ✅ Working on mobile or smaller screens
- ✅ You prefer card-based layouts
- ✅ Daily operations and quick tasks
- ✅ Team members are less technical

### Use MGClone_v1 When:
- ✅ You need a control tower / NOC view
- ✅ Presenting to executives or stakeholders
- ✅ You prefer traditional TMS interfaces
- ✅ Working with large datasets in tables
- ✅ You want MercuryGate-style aesthetics
- ✅ Team members are familiar with MercuryGate

---

## Troubleshooting

### "Port already in use"
**Problem:** You're trying to start a frontend but the port is already taken.

**Solution:**
```bash
# On Windows, kill Node processes
taskkill //F //IM node.exe

# Then restart the frontend you want
```

### "Connection refused to backend"
**Problem:** Frontend loads but shows no data or connection errors.

**Solution:** Make sure the backend is running on port 8000:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### "MGClone_v1 shows missing dependencies"
**Problem:** First time running MGClone_v1.

**Solution:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\MGClone_v1
npm install
npm run dev
```

### "Styles look broken"
**Problem:** Frontend loads but CSS is missing or looks wrong.

**Solution:**
```bash
# Clear Vite cache and reinstall
cd [frontend directory]
rm -rf node_modules .vite
npm install
npm run dev
```

---

## Feature Parity

Both frontends have the same core features:
- ✅ Dashboard stats with KPIs
- ✅ Sites view with inventory tracking
- ✅ Loads/shipments tracking
- ✅ AI agent monitoring and control
- ✅ Escalation management
- ✅ Real-time data via React Query

**The only differences are visual/UX design choices.**

---

## Development Workflow

### Typical Daily Use

**Morning:**
1. Start backend once
2. Start Base_v1 for daily work
3. Optionally start MGClone_v1 if needed for demos

**During the Day:**
- Use Base_v1 for normal operations
- Switch to MGClone_v1 for stakeholder presentations
- Both frontends show the same real-time data

**Evening:**
- Stop both frontends (Ctrl+C in terminals)
- Stop backend
- Stop database if desired (`docker-compose down`)

---

## Future: Unified Frontend with Theme Switcher

In a future version, we could merge both frontends into one with a theme toggle:

```javascript
// Hypothetical future feature
<ThemeSwitcher>
  <option value="modern">Base Design</option>
  <option value="mercurygate">Control Tower</option>
</ThemeSwitcher>
```

For now, having two separate frontends provides maximum flexibility without complexity.

---

## Recommended Setup

**For most users:**
- Keep `frontend` as the primary (Base_v1 style)
- Use MGClone_v1 when you specifically want the TMS aesthetic
- Run only one frontend at a time to save resources

**For power users:**
- Run both simultaneously
- Keep both browser tabs open
- Use Base_v1 for operations, MGClone_v1 for monitoring

**For teams:**
- Let each user choose their preferred frontend
- Document which frontend is used for specific workflows
- Use MGClone_v1 for training users familiar with MercuryGate

---

**Questions?** See [USER-GUIDE.md](USER-GUIDE.md) for general usage or [ARCHITECTURE.md](ARCHITECTURE.md) for technical details.
