"""
End-to-end email parsing test.

Sends sample ETA request emails to YOUR inbox, then polls for your replies
and parses them through the LLM + regex parser.

Setup:
  1. Enable 2FA on your Google account
  2. Generate an app password at https://myaccount.google.com/apppasswords
  3. Add to backend/.env:
       GMAIL_ENABLED=true
       GMAIL_USER=your.email@gmail.com
       GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

Usage:
  cd backend
  python scripts/test_email_loop.py send     # Send test emails to yourself
  python scripts/test_email_loop.py poll     # Poll for replies and parse
  python scripts/test_email_loop.py both     # Send then poll
"""

import sys
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.utils.email_parser import parse_eta_from_email, extract_po_number

settings = get_settings()

# Test loads to send ETA requests for
TEST_LOADS = [
    {
        "po_number": "PO-2024-001",
        "carrier_name": "Summit Petroleum Logistics",
        "site_name": "Stark Industries - Cleveland Terminal",
        "hours_to_runout": 8,
        "driver_name": "Mike Rodriguez",
    },
    {
        "po_number": "PO-2024-003",
        "carrier_name": "Summit Petroleum Logistics",
        "site_name": "Wayne Enterprises - Gotham Depot",
        "hours_to_runout": 18,
        "driver_name": "Sarah Chen",
    },
    {
        "po_number": "PO-2024-005",
        "carrier_name": "Nationwide Fuel Transport",
        "site_name": "LuthorCorp - Metropolis Hub",
        "hours_to_runout": None,
        "driver_name": "James Parker",
    },
]


def check_config():
    """Verify Gmail is configured."""
    if not settings.gmail_user or not settings.gmail_app_password:
        print("=" * 60)
        print("Gmail not configured!")
        print()
        print("Add these to backend/.env:")
        print("  GMAIL_ENABLED=true")
        print("  GMAIL_USER=your.email@gmail.com")
        print("  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        print()
        print("Get an app password at:")
        print("  https://myaccount.google.com/apppasswords")
        print("=" * 60)
        return False
    return True


def send_test_emails():
    """Send ETA request emails to yourself."""
    if not check_config():
        return

    to_email = settings.gmail_user  # send to yourself
    print(f"\nSending {len(TEST_LOADS)} ETA request emails to {to_email}...\n")

    for load in TEST_LOADS:
        urgency = ""
        if load["hours_to_runout"] and load["hours_to_runout"] < 24:
            urgency = f"\nURGENT: Site has only {load['hours_to_runout']:.0f} hours of fuel remaining."
        elif load["hours_to_runout"] and load["hours_to_runout"] < 48:
            urgency = f"\nNote: Site has {load['hours_to_runout']:.0f} hours of fuel remaining."

        subject = f"ETA Request - {load['po_number']}"
        body = f"""Hi {load['carrier_name']} Dispatch,

Can you please provide an updated ETA for the following shipment?

PO Number: {load['po_number']}
Destination: {load['site_name']}
Driver: {load['driver_name']}
{urgency}

Please reply with the expected arrival time.
(Try replying with things like "0600", "3:30 PM", "between 1 and 3 PM", or "running late")

Thank you,
Fuels Logistics AI Coordinator"""

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.gmail_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(settings.gmail_user, settings.gmail_app_password)
                server.send_message(msg)

            print(f"  SENT  {load['po_number']} - {load['site_name']}")

        except Exception as e:
            print(f"  FAIL  {load['po_number']} - {e}")

    print(f"\nDone! Check {to_email} for the emails.")
    print("Reply to them with ETAs, then run: python scripts/test_email_loop.py poll")


def poll_for_replies():
    """Poll Gmail for replies and parse ETAs."""
    if not check_config():
        return

    import imaplib
    import email as email_lib
    from email.header import decode_header

    print(f"\nPolling {settings.gmail_user} for ETA replies...")
    print("(Press Ctrl+C to stop)\n")

    while True:
        try:
            # Connect
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(settings.gmail_user, settings.gmail_app_password)
            imap.select("INBOX")

            # Search for unread replies to our ETA requests
            all_ids = set()
            for search_term in ['"ETA Request"', '"PO-2024"']:
                _, msg_nums = imap.search(None, "UNSEEN", "SUBJECT", search_term)
                if msg_nums[0]:
                    all_ids.update(msg_nums[0].split())

            if not all_ids:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] No new replies. Checking again in 15s...")
            else:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Found {len(all_ids)} new email(s)!")

                for eid in all_ids:
                    _, msg_data = imap.fetch(eid, "(RFC822)")
                    msg = email_lib.message_from_bytes(msg_data[0][1])

                    # Decode subject
                    raw_subject = msg.get("Subject", "")
                    decoded = decode_header(raw_subject)
                    subject = ""
                    for part, enc in decoded:
                        if isinstance(part, bytes):
                            subject += part.decode(enc or "utf-8", errors="ignore")
                        else:
                            subject += part

                    from_addr = msg.get("From", "")

                    # Extract body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                                break
                    else:
                        payload = msg.get_payload(decode=True)
                        body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

                    # Remove quoted reply text
                    clean_body = []
                    for line in body.split("\n"):
                        if line.strip().startswith(">"):
                            continue
                        if line.strip().startswith("On ") and "wrote:" in line:
                            break
                        clean_body.append(line)
                    body = "\n".join(clean_body).strip()

                    print(f"\n  {'=' * 55}")
                    print(f"  From:    {from_addr}")
                    print(f"  Subject: {subject}")
                    print(f"  Body:    {body[:120]}{'...' if len(body) > 120 else ''}")
                    print(f"  {'-' * 55}")

                    # Parse
                    po = extract_po_number(subject, body)
                    eta = parse_eta_from_email(subject, body)

                    if po:
                        print(f"  PO:      {po}")
                    else:
                        print(f"  PO:      (not found)")

                    if eta:
                        print(f"  ETA:     {eta.strftime('%Y-%m-%d %H:%M')} ({eta.strftime('%I:%M %p')})")
                    else:
                        print(f"  ETA:     None (vague or unparseable - needs manual follow-up)")

                    print(f"  {'=' * 55}")

                    # Mark as read
                    imap.store(eid, "+FLAGS", "\\Seen")

            imap.logout()

        except KeyboardInterrupt:
            print("\n\nStopped polling.")
            return
        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(15)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "send":
        send_test_emails()
    elif cmd == "poll":
        poll_for_replies()
    elif cmd == "both":
        send_test_emails()
        print("\n" + "=" * 60)
        print("Now reply to the emails in your inbox, then I'll parse them.")
        print("=" * 60)
        poll_for_replies()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python scripts/test_email_loop.py [send|poll|both]")


if __name__ == "__main__":
    main()
