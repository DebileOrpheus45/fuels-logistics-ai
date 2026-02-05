# Gmail SMTP Integration Setup Guide

This guide explains how to configure real email sending via Gmail SMTP for the Fuels Logistics AI Coordinator.

## Quick Setup (5 minutes)

### Step 1: Enable 2-Factor Authentication on Gmail

1. Go to your [Google Account settings](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Scroll to **2-Step Verification** and enable it if not already enabled
4. Follow the prompts to set up 2FA using your phone

### Step 2: Generate an App Password

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - If the link doesn't work, go to Google Account > Security > 2-Step Verification > App passwords
2. Select app: **Mail**
3. Select device: **Other (Custom name)**
4. Enter name: `Fuels Logistics AI`
5. Click **Generate**
6. Google will show a 16-character password (e.g., `abcd efgh ijkl mnop`)
7. **Copy this password** - you'll need it in the next step

### Step 3: Configure Backend Environment

Edit your `backend/.env` file:

```bash
# Enable Gmail SMTP
GMAIL_ENABLED=true

# Your Gmail address
GMAIL_USER=your.email@gmail.com

# The 16-character app password (remove spaces)
GMAIL_APP_PASSWORD=abcdefghijklmnop
```

**Important:**
- Use the 16-character app password, NOT your regular Gmail password
- Remove spaces from the app password
- Keep the .env file secure - it contains credentials

### Step 4: Restart the Backend

```bash
# Stop the backend (Ctrl+C in the terminal)
# Then restart it
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see logs confirming Gmail is enabled:
```
INFO:     Starting backend server
INFO:     Gmail SMTP enabled: your.email@gmail.com
```

### Step 5: Test Email Sending

1. Open the dashboard: http://localhost:5173
2. Go to the **Agents** tab
3. Click **Run Check** on any agent
4. The agent will send real emails to carriers if it needs ETAs

You can verify emails were sent by:
- Checking the **Emails** tab in the dashboard
- Checking your Gmail "Sent" folder
- Checking the backend logs for `[GMAIL SENT]` messages

## Troubleshooting

### "Gmail credentials not configured"
- Make sure you set `GMAIL_ENABLED=true` in `.env`
- Verify `GMAIL_USER` and `GMAIL_APP_PASSWORD` are set
- Restart the backend server

### "App Passwords" option is missing
- Ensure 2-Factor Authentication is enabled on your Google account
- Wait a few minutes after enabling 2FA
- Try accessing https://myaccount.google.com/apppasswords directly

### "Authentication failed" errors
- Double-check the app password is correct (16 characters, no spaces)
- Make sure you're using the app password, NOT your regular Gmail password
- Try generating a new app password

### Emails not being sent
- Check backend logs for errors
- Verify the carrier email addresses in the database are valid
- Ensure your Gmail account can send emails (not suspended)

## Switching Back to Mock Mode

To disable real email sending and use mock mode:

Edit `backend/.env`:
```bash
GMAIL_ENABLED=false
```

Then restart the backend. Emails will be logged but not actually sent.

## Security Notes

- **Never commit your `.env` file to Git** - it's already in `.gitignore`
- The app password is scoped to "Mail" only, not full account access
- You can revoke the app password anytime at https://myaccount.google.com/apppasswords
- Use a dedicated Gmail account for production systems, not your personal account

## How It Works

The email service automatically switches between modes:

- **Mock mode** (`GMAIL_ENABLED=false`): Emails are logged to console only
- **Gmail SMTP mode** (`GMAIL_ENABLED=true`): Real emails sent via Gmail SMTP

The AI agents use the email service to send ETA requests to carriers. All sent emails are logged in:
- Backend logs
- In-memory history (viewable in Emails tab)
- Your Gmail "Sent" folder (when SMTP is enabled)

## Example Email

When the agent sends an ETA request, the carrier receives:

```
Subject: ETA Request - PO #PO-20260123-001

Hi ABC Transport Dispatch,

Can you please provide an updated ETA for the following shipment?

PO Number: PO-20260123-001
Destination: SITE-ATL-001
 URGENT: Site has only 18 hours of fuel remaining.

Please reply with the expected arrival time.

Thank you,
Fuels Logistics AI Coordinator
```

The carrier can reply to your Gmail address with the updated ETA.

---

**Questions?** See [USER-GUIDE.md](USER-GUIDE.md) for general usage or [ARCHITECTURE.md](ARCHITECTURE.md) for technical details.
