"""
Demonstration of carrier ETA email reply parsing.

This script shows how the email parser handles various carrier response formats
and updates load ETAs in the database.
"""

from datetime import datetime
from app.database import SessionLocal
from app.models import Load, Activity, ActivityType
from app.utils.email_parser import parse_eta_from_email, extract_po_number


def demo_parse_carrier_replies():
    """Demonstrate parsing various carrier email reply formats."""

    print("=" * 80)
    print("CARRIER ETA EMAIL REPLY PARSER - DEMONSTRATION")
    print("=" * 80)
    print()

    # Simulated carrier email replies
    test_emails = [
        {
            "subject": "RE: ETA Request - PO-2024-001",
            "body": "ETA is 1500",
            "from": "dispatcher@fastfuel.com",
            "expected": "3:00 PM today"
        },
        {
            "subject": "Re: Load PO-2024-002 ETA",
            "body": "between 1200 and 1400",
            "from": "dispatch@carrier.com",
            "expected": "2:00 PM today (worst-case)"
        },
        {
            "subject": "RE: ETA Request - PO-2024-003",
            "body": "Should arrive around 10:30 AM",
            "from": "driver@transport.com",
            "expected": "10:30 AM"
        },
        {
            "subject": "RE: ETA Request - PO-2024-004",
            "body": "1-3 PM",
            "from": "dispatcher@logistics.com",
            "expected": "3:00 PM (worst-case)"
        },
        {
            "subject": "RE: ETA Request - PO-2024-001",
            "body": "Running late, not sure when we'll arrive",
            "from": "driver@transport.com",
            "expected": "Manual follow-up required"
        },
    ]

    print("Testing Email Parsing:")
    print("-" * 80)

    for i, email in enumerate(test_emails, 1):
        print(f"\nTest {i}:")
        print(f"  Subject: {email['subject']}")
        print(f"  From: {email['from']}")
        print(f"  Body: \"{email['body']}\"")

        # Extract PO number
        po_number = extract_po_number(email['subject'], email['body'])
        print(f"  Extracted PO: {po_number}")

        # Parse ETA
        parsed_eta = parse_eta_from_email(email['subject'], email['body'])

        if parsed_eta:
            print(f"  Parsed ETA: {parsed_eta.strftime('%Y-%m-%d %I:%M %p')}")
            print(f"  Status: SUCCESS")
        else:
            print(f"  Parsed ETA: None")
            print(f"  Status: VAGUE RESPONSE - Requires manual follow-up")

        print(f"  Expected: {email['expected']}")

    print()
    print("=" * 80)


def demo_update_load_eta():
    """Demonstrate updating a load's ETA from a carrier email."""

    print()
    print("LIVE DATABASE UPDATE DEMONSTRATION")
    print("=" * 80)
    print()

    db = SessionLocal()

    try:
        # Find an active load
        load = db.query(Load).filter(Load.status == 'in_transit').first()

        if not load:
            print("No in-transit loads found for demonstration.")
            return

        print(f"Selected Load: {load.po_number}")
        print(f"Current ETA: {load.current_eta.strftime('%Y-%m-%d %I:%M %p') if load.current_eta else 'Not set'}")
        print()

        # Simulate receiving carrier email
        simulated_email = {
            "subject": f"RE: ETA Request - {load.po_number}",
            "body": "between 1200 and 1400",
            "from": "dispatcher@carrier.com"
        }

        print("Simulated Carrier Email:")
        print(f"  Subject: {simulated_email['subject']}")
        print(f"  From: {simulated_email['from']}")
        print(f"  Body: \"{simulated_email['body']}\"")
        print()

        # Parse ETA
        parsed_eta = parse_eta_from_email(
            simulated_email['subject'],
            simulated_email['body']
        )

        if parsed_eta:
            print(f"Parsed ETA: {parsed_eta.strftime('%Y-%m-%d %I:%M %p')}")
            print()

            # Ask for confirmation before updating
            response = input("Update database with this ETA? (y/n): ")

            if response.lower() == 'y':
                old_eta = load.current_eta
                load.current_eta = parsed_eta
                load.last_eta_update_at = datetime.now()

                # Log activity
                activity = Activity(
                    agent_id=None,
                    activity_type=ActivityType.EMAIL_SENT,
                    description=f"ETA updated via carrier email: {old_eta} → {parsed_eta}",
                    load_id=load.id
                )
                db.add(activity)
                db.commit()

                print()
                print(f"[SUCCESS] Database updated successfully!")
                print(f"  Old ETA: {old_eta.strftime('%Y-%m-%d %I:%M %p') if old_eta else 'Not set'}")
                print(f"  New ETA: {parsed_eta.strftime('%Y-%m-%d %I:%M %p')}")
                print(f"  Activity logged: Yes")
            else:
                print("Update cancelled.")
        else:
            print("Could not parse ETA (vague response).")
            print("This would require manual coordinator follow-up.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()

    finally:
        db.close()

    print()
    print("=" * 80)


def demo_show_supported_formats():
    """Show all supported carrier response formats."""

    print()
    print("SUPPORTED CARRIER RESPONSE FORMATS")
    print("=" * 80)
    print()

    formats = [
        ("Military Time", ["0600", "1500", "2330"]),
        ("12-Hour Time", ["3:00 PM", "10:30 AM", "6 PM"]),
        ("Time Ranges", ["between 1200 and 1400", "1-3 PM", "10:00 AM - 12:00 PM"]),
        ("Vague Responses", ["running late", "delayed", "not sure", "don't know"]),
    ]

    for category, examples in formats:
        print(f"{category}:")
        for example in examples:
            parsed = parse_eta_from_email("RE: ETA", example)
            if parsed:
                print(f"  [OK] \"{example}\" -> {parsed.strftime('%I:%M %p')}")
            else:
                print(f"  [MANUAL] \"{example}\" -> Requires manual follow-up")
        print()

    print("=" * 80)


if __name__ == "__main__":
    # Run all demonstrations
    demo_parse_carrier_replies()
    demo_show_supported_formats()

    # Optional: Update a real load
    print()
    response = input("Would you like to test updating a load in the database? (y/n): ")
    if response.lower() == 'y':
        demo_update_load_eta()
    else:
        print("\nSkipping database update demonstration.")

    print()
    print("Demonstration complete!")
