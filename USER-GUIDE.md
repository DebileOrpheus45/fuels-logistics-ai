# Fuels Logistics AI Coordinator - User Guide

**For Non-Technical Users**
**Last Updated:** January 22, 2026

---

## Table of Contents
1. [What Is This System?](#what-is-this-system)
2. [The Main Parts](#the-main-parts)
3. [Choosing Your Frontend](#choosing-your-frontend)
4. [Starting Everything Up](#starting-everything-up)
5. [Stopping Everything](#stopping-everything)
6. [What Happens When You Close Your Laptop](#what-happens-when-you-close-your-laptop)
7. [Daily Usage Workflow](#daily-usage-workflow)
8. [Understanding the Dashboard](#understanding-the-dashboard)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)
11. [When Do I Need to Reseed?](#when-do-i-need-to-reseed)

---

## What Is This System?

This is an AI-powered platform that helps coordinate fuel deliveries to gas stations. Instead of a human dispatcher manually checking inventory levels, sending emails to truck carriers, and tracking shipments, AI agents do most of this work automatically.

**What it does:**
- Monitors fuel levels at gas stations (called "sites")
- Predicts when a station will run out of fuel
- Automatically requests delivery updates from carriers via email
- Alerts you (the human coordinator) when critical issues need attention
- Keeps track of all active shipments

**Your role as the human:**
- Supervise the AI agents
- Handle critical escalations (like when a site is about to run out of fuel)
- Configure site constraints (tank sizes, delivery minimums, etc.)
- Assign AI agents to monitor specific groups of sites

### Recent Updates (January 2026)

**New Features:**
1. **Real Gmail Integration** - Agents can now send actual emails to carriers (optional, requires Gmail app password)
2. **Snapshot Ingestion** - Hourly state updates separate from site configuration
3. **Staleness Detection** - System tracks when data hasn't updated (helps catch system outages)
4. **Overnight Awareness** - Agents understand time-of-day and escalate more aggressively overnight
5. **Decision Logging** - See exactly why agents took actions (decision codes + metrics)

**What this means for you:**
- Agents can now send real ETA requests to dispatchers (if you enable Gmail)
- Easier to update site inventory via hourly snapshots
- Agents can detect when data goes stale and alert you
- Better overnight monitoring (agents act faster when humans aren't watching)
- More transparency into agent decisions

---

## The Main Parts

Think of this system like a restaurant kitchen:

### 1. **The Database (PostgreSQL in Docker)**
- **What it is:** The filing cabinet where all data is stored
- **Where it runs:** Inside a Docker container (a mini virtual computer)
- **What's stored:** Sites, loads, agents, escalations, activity logs
- **When to start it:** Every time before starting the backend
- **Stays running:** Yes, even if you close your laptop (as long as Docker Desktop is running)

### 2. **The Backend (FastAPI Python Server)**
- **What it is:** The kitchen where all the cooking happens
- **Where it runs:** On your computer at `http://localhost:8000`
- **What it does:**
  - Serves the API (like a waiter taking orders)
  - Runs AI agents on a schedule
  - Talks to the database
  - Handles requests from the frontend
- **When to start it:** Every time you want to use the system
- **Stays running:** Only while the terminal window is open
- **Shuts off when:** You close the terminal, close your laptop, or press Ctrl+C

### 3. **The Frontend (React Web App) - Two Options!**

**You have TWO frontend interfaces to choose from:**

#### **Option A: Base_v1 (Original)**
- **What it is:** Modern, card-based interface - like a sleek mobile app
- **Where it runs:** `http://localhost:5173`
- **Best for:** Daily operations, quick tasks, easier to learn
- **Folder:** `frontend/`

#### **Option B: MGClone_v1 (MercuryGate Style)**
- **What it is:** Professional TMS control tower - looks like MercuryGate software
- **Where it runs:** `http://localhost:5174`
- **Best for:** Executive dashboards, presentations, if you're used to MercuryGate
- **Folder:** `MGClone_v1/`

**Important:** Both frontends show the SAME data! They just look different. You can even run both at the same time and switch between browser tabs.

**What they do:** Show you the dashboard, let you click buttons, display data
**When to start:** Every time you want to use the system
**Stays running:** Only while the terminal window is open
**Shuts off when:** You close the terminal, close your laptop, or press Ctrl+C

---

## Choosing Your Frontend

**Which one should I use?**

### Use Base_v1 if:
- ✅ This is your first time using the system
- ✅ You want a modern, clean interface
- ✅ You're working on a phone or tablet
- ✅ You prefer card-based layouts

### Use MGClone_v1 if:
- ✅ You've used MercuryGate TMS before
- ✅ You need a "control tower" / command center view
- ✅ You're presenting to executives
- ✅ You prefer traditional table-based interfaces

**Can I switch between them?** YES! Just open different browser tabs. They both use the same backend data.

**See [FRONTEND-SWITCHER.md](FRONTEND-SWITCHER.md) for detailed comparison and switching instructions.**

---

## Starting Everything Up

**Do this every time you want to use the system** (like turning on your car before driving).

### Step 1: Start the Database
```bash
# Open Command Prompt or Terminal
cd C:\Users\vsubb\fuels-logistics-ai

# Start Docker database
docker-compose up -d
```

**What this does:** Starts PostgreSQL in the background. The `-d` means "detached" so it runs in the background.

**How long does it take?** 5-10 seconds

**How do I know it worked?**
```bash
docker ps
```
You should see a container named `fuels-logistics-ai-db-1` running.

---

### Step 2: Start the Backend (in a separate terminal window)

**Open a NEW terminal window** (don't close the first one!):

```bash
# Navigate to backend folder
cd C:\Users\vsubb\fuels-logistics-ai\backend

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**What this does:** Starts the FastAPI server and the AI agent scheduler.

**How long does it take?** 3-5 seconds

**How do I know it worked?** You'll see output like:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**IMPORTANT:** Keep this terminal window open! If you close it, the backend stops.

---

### Step 3: Start the Frontend (in another separate terminal window)

**Open a THIRD terminal window** and choose which frontend to start:

#### **Option A: Start Base_v1 (Recommended for beginners)**

```bash
# Navigate to frontend folder
cd C:\Users\vsubb\fuels-logistics-ai\frontend

# Start the React dev server
npm run dev
```

**How do I know it worked?** You'll see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

#### **Option B: Start MGClone_v1 (MercuryGate style)**

```bash
# Navigate to MGClone_v1 folder
cd C:\Users\vsubb\fuels-logistics-ai\MGClone_v1

# First time only: Install dependencies
npm install

# Start the React dev server
npm run dev
```

**How do I know it worked?** You'll see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5174/
```

#### **Advanced: Run BOTH frontends at the same time**

If you want to be able to switch between both interfaces:

**Terminal 3:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\frontend
npm run dev
```

**Terminal 4 (open a FOURTH window):**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\MGClone_v1
npm install  # first time only
npm run dev
```

Now you can access:
- Base_v1 at http://localhost:5173
- MGClone_v1 at http://localhost:5174

**IMPORTANT:** Keep terminal windows open! If you close them, the frontend stops.

---

### Step 4: Access the Dashboard

1. Open your web browser (Chrome, Firefox, Edge, etc.)
2. Go to the URL based on which frontend you started:
   - **Base_v1:** `http://localhost:5173`
   - **MGClone_v1:** `http://localhost:5174`
   - **Both running?** Open two tabs and try each!
3. Login with:
   - **Username:** `coordinator`
   - **Password:** `fuel2024`

**You should now see the dashboard!**

**Note:** The login credentials are the same for both frontends.

---

## Stopping Everything

**Do this when you're done for the day** (like shutting down your computer properly).

### Option 1: Stop Each Part Individually

**Stop the Frontend(s):**
- Go to the terminal(s) running `npm run dev`
- Press `Ctrl + C` in each terminal
- Type `Y` if asked to confirm
- If you're running both frontends, stop both terminals

**Stop the Backend:**
- Go to the terminal running `uvicorn`
- Press `Ctrl + C`

**Stop the Database:**
```bash
docker-compose down
```

**Note:** Stopping the database with `down` keeps all your data. If you want to delete all data and start fresh, use `docker-compose down -v` (the `-v` deletes the volume/storage).

---

### Option 2: Quick Shutdown (if you're in a hurry)

Just close all terminal windows and:
```bash
docker-compose down
```

The backend and frontend will stop immediately when you close their terminals. The database needs to be stopped manually with the command above.

---

## What Happens When You Close Your Laptop

**Short answer:** Everything stops except possibly the database (if Docker Desktop is set to keep running in the background).

**What happens to each part:**

### Database (Docker)
- **Depends on your Docker Desktop settings**
- If Docker Desktop is set to start on system boot, the database might still be running when you reopen
- If not, you'll need to run `docker-compose up -d` again
- **Your data is safe** - it's saved to disk, not lost when Docker stops

### Backend
- **Stops completely** when you close the laptop (or close the terminal)
- You'll need to start it again with `python -m uvicorn app.main:app --reload`
- The AI agent scheduler also stops, so agents won't run checks while the backend is off

### Frontend
- **Stops completely** when you close the laptop
- You'll need to start it again with `npm run dev`
- The browser tab will show "connection refused" if you try to access it

### AI Agents
- **Stop running** when the backend stops
- They won't check sites or send emails while stopped
- When you restart the backend, agents with status="ACTIVE" will resume their scheduled checks

---

## Daily Usage Workflow

### Morning Routine (Starting Your Day)
1. Open laptop
2. Start database: `docker-compose up -d`
3. Start backend in one terminal
4. Start frontend in another terminal
5. Open browser to `http://localhost:5173`
6. Login and check dashboard for overnight escalations

### During the Day
- Dashboard stays open in your browser
- Backend and frontend run in the background
- AI agents run checks every 15 minutes (configurable)
- You respond to escalations as they appear

### End of Day
1. Resolve any open escalations
2. Press `Ctrl + C` in backend terminal
3. Press `Ctrl + C` in frontend terminal
4. Run `docker-compose down` to stop database
5. Close your laptop

**Total time to start everything:** ~30 seconds
**Total time to stop everything:** ~10 seconds

---

## Understanding the Dashboard

When you login, you'll see several tabs at the top:

### 1. Dashboard Tab (Home)
**What you see:**
- **Stat cards at top:** Total sites, sites at risk, active loads, delayed loads, open escalations, active agents
- **Click these cards** to filter data on other tabs (e.g., click "Sites at Risk" to jump to Sites tab filtered to at-risk sites)

**Recent activity feed:** Shows what the AI agents have been doing (emails sent, escalations created, etc.)

---

### 2. Sites Tab
**What you see:**
- Grid of cards showing each gas station (site)
- Each card shows:
  - Site code and name
  - Fuel gauge (circular meter showing tank fill %)
  - Hours until runout
  - Assigned AI agent (dropdown to change)
  - Notes (if any)

**What you can do:**
- **Filter sites:** Click "All Sites", "At Risk", or "Critical" buttons at top
- **Edit a site:** Click the pencil icon (Edit button) on any site card
- **Batch upload:** Click "Batch Upload" button to update many sites at once via CSV file
- **Assign to agent:** Use the dropdown at bottom of each card

**Color coding:**
- **Red border:** Critical (< 12 hours to runout)
- **Orange border:** At risk (12-24 hours to runout)
- **Yellow border:** Warning (24-48 hours to runout)
- **Green border:** OK (> 48 hours to runout)

---

### 3. Loads Tab
**What you see:**
- List of all fuel shipments/deliveries
- Each load shows:
  - PO number
  - Carrier name
  - Destination site
  - Volume (gallons)
  - Status (Scheduled, In Transit, Delivered, Cancelled)
  - Current ETA

**Status badges:**
- **Blue:** Scheduled
- **Yellow:** In Transit
- **Green:** Delivered
- **Red:** Cancelled

---

### 4. Agent Monitor Tab
**This is your main HITL (Human-in-the-Loop) supervision interface**

**What you see:**
- Cards for each AI agent showing:
  - Agent name and status (Active/Stopped/Paused)
  - Number of assigned sites
  - Last activity timestamp
  - Recent activity summary

**What you can do:**
- **Start/Stop agents:** Click the Start or Stop button
- **Run manual check:** Click "Run Check" to make the agent check its sites immediately (instead of waiting for the scheduled interval)
- **Manage sites:** Click the purple "Manage Sites" button to assign/unassign sites to this agent
- **View activity log:** Scroll down to see detailed activity timeline

**Activity timeline:**
- Shows all actions the agent has taken
- Click on "Email sent" activities to see the actual email content
- Filter by activity type (All, Checks, Emails, Escalations, Updates)

---

### 5. Escalations Tab
**This is where critical issues appear that need YOUR attention**

**What you see:**
- List of all escalations (open and resolved)
- Each escalation shows:
  - Priority (Critical, High, Medium, Low)
  - Issue type (Runout Risk, Late Delivery, No Carrier Response, etc.)
  - Description written by the AI agent
  - Related site/load
  - Created timestamp

**What you can do:**
- **Click on an escalation** to see full details
- **Resolve it:** Add resolution notes and mark as resolved
- **Filter:** Show only open escalations or all escalations

**Priority colors:**
- **Red:** Critical (immediate action needed)
- **Orange:** High (action needed today)
- **Yellow:** Medium (monitor closely)
- **Gray:** Low (informational)

---

## Common Tasks

### Task 1: Edit Site Constraints

**When:** You get new information about a site (e.g., tank was upgraded, site uses more fuel now)

**How:**
1. Go to Sites tab
2. Find the site card
3. Click the pencil/edit icon in the top-right corner
4. A modal (popup window) appears with fields:
   - Tank Capacity (gallons)
   - Consumption Rate (gallons per hour)
   - Runout Threshold (when to alert, in hours)
   - Min Delivery Quantity (minimum gallons per delivery)
   - Notes (free text for coordinator notes)
5. Edit the fields you want to change
6. Click "Save Changes"

**Result:** The site's data is updated in the database immediately.

---

### Task 2: Batch Upload Site Constraints (Update Many Sites at Once)

**When:** You have a spreadsheet with updated constraints for many sites

**How:**
1. Go to Sites tab
2. Click "Batch Upload" button (green button at top)
3. A modal appears
4. **Prepare your CSV file:**
   - Must have these columns: `consignee_code`, `tank_capacity`, `consumption_rate`, `runout_threshold_hours`, `min_delivery_quantity`, `notes`
   - Example:
     ```csv
     consignee_code,tank_capacity,consumption_rate,runout_threshold_hours,min_delivery_quantity,notes
     SITE001,10000,250,48,3000,Often understaffed on weekends
     SITE002,15000,300,36,4000,
     SITE003,8000,200,48,2500,New manager as of Jan 2026
     ```
5. Click "Choose File" and select your CSV
6. Preview table appears showing what will be updated
7. Click "Upload and Update"
8. System matches sites by `consignee_code` and updates the fields
9. Results summary shows how many were updated, not found, or had errors

**Result:** Multiple sites updated in one action.

---

### Task 3: Assign Sites to an AI Agent

**When:** You want an agent to monitor specific sites (e.g., "Agent 1 monitors all sites in the northeast region")

**How:**

**Method A - Via Agent Monitor Tab:**
1. Go to Agent Monitor tab
2. Find the agent card
3. Click the purple "Manage Sites" button (Users icon)
4. A modal appears showing all sites as checkboxes
5. Check the sites you want this agent to monitor
6. Use "Select All" or "Deselect All" for quick selection
7. Use the search box to filter sites by code or name
8. Click "Save Assignment"

**Method B - Via Individual Site Cards:**
1. Go to Sites tab
2. On each site card, there's a dropdown labeled "Assigned Agent"
3. Select the agent from the dropdown
4. The assignment saves automatically

**Important:** Each site can only be assigned to ONE agent at a time.

**Result:** The agent will now monitor those sites during its check cycles.

---

### Task 4: Manually Run an Agent Check

**When:** You want the agent to check its sites immediately (not wait for the scheduled interval)

**How:**
1. Go to Agent Monitor tab
2. Find the agent card
3. Click "Run Check" button (lightning bolt icon)
4. Wait 5-10 seconds (you'll see a spinner)
5. Activity log updates with the results

**What happens:**
- Agent queries the database for current inventory levels of its assigned sites
- Agent checks active loads and ETAs
- Agent decides if any actions are needed:
  - Send ETA request email to carrier
  - Create escalation for critical runout risk
  - Update dashboard notes
- All actions are logged to the Activity table
- You can view the email content by clicking on "Email sent" in the activity log

**Result:** Agent takes immediate action if needed.

---

### Task 5: Start/Stop an Agent

**When:** You want to enable or disable automated monitoring

**How:**
1. Go to Agent Monitor tab
2. Find the agent card
3. Click "Start" or "Stop" button

**What "Start" does:**
- Changes agent status to "Active"
- Adds the agent to the scheduler
- Agent will run checks every X minutes (default: 15 minutes)
- Checks continue automatically until you stop it

**What "Stop" does:**
- Changes agent status to "Stopped"
- Removes agent from the scheduler
- No more automated checks (but you can still run manual checks)

**Result:** Agent runs on autopilot (Start) or requires manual triggering (Stop).

---

### Task 6: Resolve an Escalation

**When:** You've handled a critical issue and want to mark it as resolved

**How:**
1. Go to Escalations tab (or click the escalation from the banner at top of Dashboard)
2. Click on the escalation row
3. A modal appears with full details
4. Add notes in the "Resolution Notes" text box (e.g., "Called dispatcher, truck arriving in 2 hours")
5. Click "Resolve Escalation"

**Result:** Escalation status changes to "Resolved" and is removed from the open escalations count.

---

### Task 7: View Email Content Sent by Agent

**When:** You want to see exactly what the AI agent said in an email

**How:**
1. Go to Agent Monitor tab
2. Scroll to the activity timeline
3. Find an activity with type "Email Sent" (envelope icon)
4. Click on it
5. A modal appears showing:
   - Recipient
   - Subject
   - Body content
   - Timestamp

**Note:** By default, emails are mocked (logged to console only). To enable real email sending, see Task 8 below.

---

### Task 8: Enable Real Gmail Sending (Optional)

**When:** You want agents to send actual emails to carrier dispatchers instead of just logging them

**Prerequisites:**
- A Gmail account
- 2-Factor Authentication enabled on that account

**How:**
1. **Generate a Gmail App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Sign in with your Gmail account
   - Click "Select app" → Choose "Mail"
   - Click "Select device" → Choose "Other" and type "Fuels AI"
   - Click "Generate"
   - Copy the 16-character password (it looks like: `abcd efgh ijkl mnop`)

2. **Update your `.env` file:**
   - Open `backend/.env` in a text editor
   - Add or update these lines:
     ```env
     GMAIL_ENABLED=true
     GMAIL_USER=your-email@gmail.com
     GMAIL_APP_PASSWORD=abcdefghijklmnop
     ```
   - Replace `your-email@gmail.com` with your Gmail address
   - Replace `abcdefghijklmnop` with your 16-character app password (remove spaces)

3. **Restart the backend:**
   - Go to the backend terminal
   - Press `Ctrl + C` to stop
   - Run: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**How to test:**
1. Go to Agent Monitor tab
2. Run a manual agent check
3. Check the activity log - if an email was sent, it should say "GMAIL SENT" in the backend terminal logs

**Security Notes:**
- Use an app password, NOT your regular Gmail password
- The app password only works for this application
- You can revoke it anytime at https://myaccount.google.com/apppasswords

**Gmail Limits:**
- Gmail allows ~500 emails per day
- If you exceed this, Gmail will temporarily block sending

**To disable:** Set `GMAIL_ENABLED=false` in `.env` and restart backend

---

### Task 9: Ingest Hourly Snapshot (Update Current State)

**When:** You have an hourly export from your fuel management system and want to update current inventory levels and ETAs

**What this does:**
- Updates CURRENT STATE (inventory, hours to runout, ETAs)
- Does NOT change CONSTRAINTS (tank capacity, consumption rate, thresholds)
- Tracks staleness (detects when data stops updating)

**How (via API):**
```bash
curl -X POST http://localhost:8000/api/snapshots/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_time": "2026-01-22T14:30:00",
    "source": "Fuel Shepherd Export",
    "customer": "Stark Industries",
    "erp_source": "Fuel Shepherd",
    "sites": [
      {
        "site_id": "SITE001",
        "current_inventory": 5200.0,
        "hours_to_runout": 18.5
      },
      {
        "site_id": "SITE002",
        "current_inventory": 8100.0,
        "hours_to_runout": 32.0
      }
    ],
    "loads": [
      {
        "po_number": "PO-12345",
        "destination_site_id": "SITE001",
        "current_eta": "2026-01-23T08:00:00",
        "status": "IN_TRANSIT",
        "driver_name": "John Smith",
        "driver_phone": "555-1234",
        "volume": 3000.0
      }
    ]
  }'
```

**What happens:**
- Site inventory and runout times are updated
- `last_inventory_update_at` timestamp is set (for staleness tracking)
- Load ETAs, status, and driver info are updated
- `last_eta_update_at` timestamp is set ONLY if ETA actually changed
- Staleness counters reset for updated sites/loads

**Typical workflow:**
1. Every hour: Export data from your fuel system (Fuel Shepherd, FuelQuest, etc.)
2. Convert to JSON format (or CSV → JSON)
3. POST to `/api/snapshots/ingest`
4. System updates state, agents monitor for changes

**Future enhancement:** Google Sheets integration will automate this (agents pull from sheet hourly)

---

## Troubleshooting

### Problem: "Can't access http://localhost:5173"

**Browser shows:** "Connection refused" or "Site can't be reached"

**Cause:** Frontend isn't running

**Fix:**
1. Check if you have a terminal running `npm run dev`
2. If not, open a terminal and run:
   ```bash
   cd C:\Users\vsubb\fuels-logistics-ai\frontend
   npm run dev
   ```
3. Wait for it to say "ready" and try again

---

### Problem: "Dashboard shows zero sites/agents/loads"

**What happened:** Database is empty or backend can't connect

**Fix:**
1. Check if backend is running (should have a terminal with uvicorn output)
2. Check if database is running:
   ```bash
   docker ps
   ```
3. If you see the database container, reseed the data:
   ```bash
   cd C:\Users\vsubb\fuels-logistics-ai\backend
   python seed_data.py
   ```
4. Refresh the browser

---

### Problem: "Error: read ECONNRESET" or "Network Error"

**What happened:** Backend crashed or restarted

**Fix:**
1. Go to the backend terminal
2. Press `Ctrl + C` to stop it
3. Kill any stuck Python processes:
   ```bash
   taskkill //F //IM python.exe
   ```
4. Restart backend:
   ```bash
   cd C:\Users\vsubb\fuels-logistics-ai\backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Refresh the browser

---

### Problem: "column sites.consumption_rate does not exist"

**What happened:** Database schema is out of sync with the code

**Fix (NUCLEAR OPTION - deletes all data):**
```bash
docker-compose down -v
docker-compose up -d
cd backend
python seed_data.py
```

Then restart backend and frontend.

**What this does:**
- Stops database
- Deletes all data (`-v` flag)
- Recreates database with new schema
- Reseeds with test data

---

### Problem: "Agent ran a check but nothing happened"

**What happened:** Agent has no assigned sites OR there are no at-risk sites

**Fix:**
1. Go to Agent Monitor tab
2. Click "Manage Sites" on the agent
3. Assign at least one site to the agent
4. Click "Run Check" again

**How to verify:** Check the activity log - it should show "Check completed" with details.

---

### Problem: "Can't login - wrong password"

**What happened:** You mistyped the credentials

**Fix:**
- Username: `coordinator` (all lowercase)
- Password: `fuel2024` (all lowercase, no spaces)

**Note:** This is hardcoded in the frontend for the MVP. In production, this would use real authentication.

---

## When Do I Need to Reseed?

**Reseeding** means running `python seed_data.py` to populate the database with test data.

### You need to reseed when:

1. **First time setup** - When you first clone the project and start the database
2. **After database reset** - When you run `docker-compose down -v` (which deletes all data)
3. **Database is empty** - When dashboard shows zero sites/agents/loads but backend is running
4. **Schema changed** - When you see errors about missing columns (rare after initial setup)

### You DON'T need to reseed when:

1. **Daily startup** - Just starting the system for the day
2. **Backend restarts** - Backend crashed and you restarted it
3. **Frontend restarts** - Frontend crashed and you restarted it
4. **Laptop sleep/wake** - Closed laptop and reopened it
5. **Browser refresh** - You refreshed the browser tab

**Rule of thumb:** If you ran `docker-compose down -v`, you need to reseed. Otherwise, you probably don't.

---

## How the Reseeding Works

The `seed_data.py` script checks if the database already has data. If it finds any agents or sites, it skips seeding.

**What it creates:**
- 1 AI agent ("Coordinator Agent 1")
- 5 sites with varying inventory levels
- 2 carriers
- 4 active loads
- 4 escalations (some critical, some resolved)
- Sample activities

**How long it takes:** 2-3 seconds

**Example:**
```bash
cd C:\Users\vsubb\fuels-logistics-ai\backend
python seed_data.py
```

Output:
```
Seeding database...
Created 1 AI agents
Created 5 sites
Created 2 carriers
Created 5 lanes
Created 4 loads
Created sample activities
Created 4 escalations
Database seeded successfully!
```

---

## Understanding Process Lifecycle

### Backend Process

**Where it runs:** In a terminal window on your computer
**How long it runs:** Until you close the terminal or press `Ctrl + C`
**What happens when it stops:**
- API stops responding
- AI agents stop running checks
- Frontend can't fetch data (you'll see errors)

**Auto-restart:** NO - You must manually restart it

**Background mode:** You can run it in background (add `&` at end of command on Mac/Linux, or use `start` on Windows), but it's easier to just keep the terminal open

---

### Frontend Process

**Where it runs:** In a terminal window on your computer
**How long it runs:** Until you close the terminal or press `Ctrl + C`
**What happens when it stops:**
- Browser can't load the page
- Shows "connection refused"

**Auto-restart:** NO - You must manually restart it

**Background mode:** Same as backend - possible but easier to keep terminal open

---

### Database Process

**Where it runs:** Inside a Docker container
**How long it runs:** Until you run `docker-compose down` OR Docker Desktop stops
**What happens when it stops:**
- Backend can't connect to database
- You'll see errors like "could not connect to server"

**Auto-restart:** MAYBE - Depends on Docker Desktop settings:
- If Docker Desktop is set to "Start Docker Desktop when you log in", database will auto-start on boot
- Otherwise, you need to run `docker-compose up -d` manually

**Background mode:** YES - It always runs in the background (detached mode)

---

### AI Agent Scheduler

**Where it runs:** Inside the backend process (part of FastAPI)
**How long it runs:** As long as the backend is running
**What happens when it stops:**
- Agents stop running automated checks
- Manual checks still work

**Auto-restart:** When you restart the backend, the scheduler restarts and reloads agents with status="ACTIVE"

---

## Visual Process Map

```
┌─────────────────────────────────────────────────────────────┐
│  YOU OPEN YOUR LAPTOP                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │ Docker Desktop Running? │
          └───────┬──────────┬────┘
                  │          │
            YES   │          │  NO
                  ▼          ▼
          ┌─────────────┐   ┌──────────────────┐
          │ Database    │   │ Run:             │
          │ Auto-starts │   │ docker-compose   │
          │ ✓           │   │ up -d            │
          └─────┬───────┘   └────────┬─────────┘
                │                    │
                └────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Database is running  │
              │ ✓                    │
              └──────────┬───────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────┐                  ┌──────────────┐
│ Terminal 1:  │                  │ Terminal 2:  │
│ Start Backend│                  │ Start Frontend│
│              │                  │              │
│ cd backend   │                  │ cd frontend  │
│ uvicorn...   │                  │ npm run dev  │
└──────┬───────┘                  └──────┬───────┘
       │                                 │
       └────────────┬────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Open Browser:        │
         │ localhost:5173       │
         │                      │
         │ Login & Use System   │
         └──────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ WHEN DONE:           │
         │                      │
         │ 1. Ctrl+C backend    │
         │ 2. Ctrl+C frontend   │
         │ 3. docker-compose    │
         │    down              │
         └──────────────────────┘
```

---

## Quick Reference Commands

### Starting
```bash
# 1. Database
docker-compose up -d

# 2. Backend (new terminal)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (new terminal)
cd frontend
npm run dev

# 4. Browser
# Open http://localhost:5173
# Login: coordinator / fuel2024
```

### Stopping
```bash
# 1. Backend terminal: Ctrl + C
# 2. Frontend terminal: Ctrl + C
# 3. Database
docker-compose down
```

### Checking Status
```bash
# Is database running?
docker ps

# Is backend running?
curl http://localhost:8000/api/agents/

# Is frontend running?
# Try to access http://localhost:5173 in browser
```

### Troubleshooting
```bash
# Reset everything (DELETES ALL DATA)
docker-compose down -v
docker-compose up -d
cd backend
python seed_data.py

# Kill stuck Python processes (Windows)
taskkill //F //IM python.exe

# View database directly
docker exec -it fuels-logistics-ai-db-1 psql -U fueluser -d fueldb
```

---

## FAQ

### Q: How often do agents run checks automatically?
**A:** Every 15 minutes by default (configurable in agent settings). But only if the agent status is "Active" and the backend is running.

### Q: Do I need to keep the terminal windows open?
**A:** Yes, for backend and frontend. If you close them, those processes stop. The database runs in Docker, so it stays running even if you close terminals.

### Q: What if I forget to stop the database when I'm done?
**A:** It's fine. Docker containers use minimal resources when idle. You can leave it running. Just remember to stop it before shutting down your computer to avoid data corruption.

### Q: Can I access this from another computer?
**A:** Not by default. It's running on `localhost` which means only your computer can access it. To allow access from other computers on your network, you'd need to change the IP address settings (not covered in this MVP guide).

### Q: How much does it cost to run the AI agents?
**A:** Each agent check cycle costs ~$0.01-0.05 depending on Claude API usage (based on tokens used). If an agent runs every 15 minutes, that's 96 checks per day = ~$1-5/day per agent. You control costs by stopping agents when not needed.

### Q: What happens if an agent makes a mistake?
**A:** All agent actions are logged. You can review the activity log to see what the agent did and why. If it created an incorrect escalation, you can just resolve it with notes. The agent learns from the context you provide in site notes.

### Q: Can I change the agent's check interval?
**A:** Yes, but not through the UI in the MVP. You'd need to update the `check_interval_minutes` field in the database or ask a developer to add that feature to the UI.

### Q: What is "staleness" and why does it matter?
**A:** Staleness means data hasn't updated in a while. For example, if a site's inventory hasn't changed in 6 hours, that might mean:
- The fuel system is down
- The export process failed
- There's a communication issue

Agents can detect staleness and alert you, which helps catch system outages before they cause problems.

### Q: What's the difference between constraints and state?
**A:**
- **Constraints** = Static configuration (what the tank CAN hold, how fast it burns fuel)
- **State** = Current operational reality (what's IN the tank now, where the truck is)

Think of it like your car:
- Constraints: Gas tank holds 15 gallons, car gets 30 MPG
- State: Currently has 8 gallons, range is 240 miles

You set constraints once during setup. You update state hourly via snapshots.

### Q: Why do agents act differently overnight?
**A:** Overnight is when humans aren't watching dashboards. Agents are configured to be more aggressive overnight (lower thresholds, faster escalation) because:
- Human coordinators are asleep
- Issues can't wait until morning
- Better to over-alert than miss a critical situation

You can configure overnight hours and urgency multipliers per agent.

### Q: Can I see why the agent made a decision?
**A:** Yes! Each agent action logs:
- **Decision code** - Short label like "STALE_ETA_LOW_INVENTORY"
- **Decision metrics** - The exact numbers that triggered the action
- **Reasoning summary** - Optional human-readable explanation (generated on-demand)

Check the activity log in the Agent Monitor tab.

### Q: Do I need to enable Gmail for the system to work?
**A:** No, it's optional. By default, emails are "mocked" (logged to console). This is fine for testing and demos. Enable Gmail when you're ready for agents to actually communicate with carriers.

### Q: How often should I ingest snapshots?
**A:** Hourly is recommended. More frequent is fine (every 30 min), but less than hourly risks agents missing critical changes. The system is designed for batch updates, not real-time.

---

## Summary

**Think of it like running a car:**
- **Database (Docker)** = The engine - runs in the background, stores everything
- **Backend (Python)** = The transmission - connects everything, powers the AI
- **Frontend (React)** = The dashboard - what you see and interact with
- **You (Human)** = The driver - supervise, handle critical decisions

**Routine:**
1. Morning: Start all three parts (~30 seconds)
2. Day: Monitor dashboard, respond to escalations
3. Evening: Stop all three parts (~10 seconds)

**If anything breaks:** Restart it. Worst case, reset the database and reseed.

---

**End of User Guide**

**For technical details, see:** [ARCHITECTURE.md](ARCHITECTURE.md)
