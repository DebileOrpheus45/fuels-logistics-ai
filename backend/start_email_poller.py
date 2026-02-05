"""
Startup script for the Gmail ETA reply poller service.

This script runs the email poller as a background service that:
- Checks Gmail inbox every 10 minutes
- Processes carrier ETA replies automatically
- Updates load ETAs in the database
- Marks processed emails as read

Usage:
    python start_email_poller.py

Configuration:
    - Set GMAIL_USER in .env (your Gmail address)
    - Set GMAIL_APP_PASSWORD in .env (NOT your regular password!)
    - Generate app password at: https://myaccount.google.com/apppasswords

To stop:
    Press Ctrl+C
"""

from app.services.email_poller import main

if __name__ == "__main__":
    print("=" * 80)
    print("Gmail ETA Reply Poller - Starting")
    print("=" * 80)
    print()
    print("This service will:")
    print("  - Check Gmail inbox every 10 minutes")
    print("  - Process carrier ETA replies (subject contains 'RE: ETA' or PO number)")
    print("  - Update load ETAs automatically")
    print("  - Mark processed emails as read")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()

    main()
