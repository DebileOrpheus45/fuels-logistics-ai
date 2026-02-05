"""
Email parsing utilities for inbound carrier ETA replies.

Handles various formats:
- Single times: "0600", "1500", "3:00 PM"
- Time ranges: "between 1200 and 1400", "1-3 PM"
- Vague responses: "running late", "delayed"

Safety: Always uses later time in range as worst-case scenario.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_eta_from_email(subject: str, body: str, sent_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse ETA from carrier email reply.

    Args:
        subject: Email subject line (should contain PO number)
        body: Email body text
        sent_date: When the email was sent (defaults to now)

    Returns:
        datetime object representing the ETA, or None if couldn't parse

    Examples:
        "0600" -> today at 6:00 AM
        "1500" -> today at 3:00 PM
        "between 1200 and 1400" -> today at 2:00 PM (worst case)
        "1-3 PM" -> today at 3:00 PM (worst case)
        "running late" -> None (requires manual follow-up)
    """
    if sent_date is None:
        sent_date = datetime.now()

    # Normalize body text
    text = body.lower().strip()

    # Check for vague/delayed responses first (return None for manual handling)
    vague_patterns = [
        r'\brunning\s+late\b',
        r'\bdelayed\b',
        r'\bnot\s+sure\b',
        r'\bdon\'t\s+know\b',
        r'\bunknown\b',
    ]
    for pattern in vague_patterns:
        if re.search(pattern, text):
            return None  # Requires manual follow-up

    # Try to extract time range (prefer worst case - later time)
    time_range = extract_time_range(text)
    if time_range:
        start_time, end_time = time_range
        # Use end_time as worst-case scenario
        return combine_date_and_time(sent_date, end_time)

    # Try to extract single time
    single_time = extract_single_time(text)
    if single_time:
        return combine_date_and_time(sent_date, single_time)

    return None


def extract_time_range(text: str) -> Optional[Tuple[str, str]]:
    """
    Extract time range from text.

    Returns: (start_time, end_time) tuple or None

    Examples:
        "between 1200 and 1400" -> ("1200", "1400")
        "1-3 PM" -> ("1300", "1500")
        "10:00 AM - 12:00 PM" -> ("1000", "1200")
    """
    # Pattern 1: "between HHMM and HHMM"
    match = re.search(r'between\s+(\d{3,4})\s+and\s+(\d{3,4})', text)
    if match:
        return (normalize_time(match.group(1)), normalize_time(match.group(2)))

    # Pattern 2: "H-H PM/AM" (e.g., "1-3 PM")
    match = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*(am|pm)', text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        period = match.group(3)

        # Convert to 24-hour
        if period == 'pm' and start_hour != 12:
            start_hour += 12
            end_hour += 12
        elif period == 'am' and start_hour == 12:
            start_hour = 0
        if period == 'am' and end_hour == 12:
            end_hour = 0

        return (f"{start_hour:02d}00", f"{end_hour:02d}00")

    # Pattern 3: "HH:MM AM - HH:MM PM"
    match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)', text)
    if match:
        start_hour, start_min, start_period = int(match.group(1)), int(match.group(2)), match.group(3)
        end_hour, end_min, end_period = int(match.group(4)), int(match.group(5)), match.group(6)

        # Convert to 24-hour
        if start_period == 'pm' and start_hour != 12:
            start_hour += 12
        if end_period == 'pm' and end_hour != 12:
            end_hour += 12

        return (f"{start_hour:02d}{start_min:02d}", f"{end_hour:02d}{end_min:02d}")

    return None


def extract_single_time(text: str) -> Optional[str]:
    """
    Extract single time from text.

    Returns: time string in HHMM format or None

    Examples:
        "0600" -> "0600"
        "1500" -> "1500"
        "3:00 PM" -> "1500"
        "10:30 AM" -> "1030"
    """
    # Pattern 1: 4-digit military time (0600, 1500)
    match = re.search(r'\b([0-2]\d)([0-5]\d)\b', text)
    if match:
        return f"{match.group(1)}{match.group(2)}"

    # Pattern 2: H:MM AM/PM or HH:MM AM/PM
    match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)

        # Convert to 24-hour format
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        return f"{hour:02d}{minute:02d}"

    # Pattern 3: H AM/PM (e.g., "3 PM")
    match = re.search(r'\b(\d{1,2})\s*(am|pm)\b', text)
    if match:
        hour = int(match.group(1))
        period = match.group(2)

        # Convert to 24-hour format
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        return f"{hour:02d}00"

    return None


def normalize_time(time_str: str) -> str:
    """
    Normalize time string to HHMM format.

    Examples:
        "600" -> "0600"
        "1500" -> "1500"
    """
    time_str = time_str.strip()
    if len(time_str) == 3:
        return f"0{time_str}"
    return time_str


def combine_date_and_time(base_date: datetime, time_str: str) -> datetime:
    """
    Combine a date with a time string (HHMM format).

    Args:
        base_date: Base datetime (usually email sent date or today)
        time_str: Time in HHMM format (e.g., "1430")

    Returns:
        datetime object with combined date and time
    """
    hour = int(time_str[:2])
    minute = int(time_str[2:4])

    eta = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If the ETA time is in the past, assume it's tomorrow
    if eta < datetime.now():
        eta += timedelta(days=1)

    return eta


def extract_po_number(subject: str, body: str) -> Optional[str]:
    """
    Extract PO number from email subject or body.

    Examples:
        "RE: ETA Request - PO-2024-001" -> "PO-2024-001"
        "Re: Load PO-2024-003 ETA" -> "PO-2024-003"
    """
    # Try subject first
    match = re.search(r'\b(PO-\d{4}-\d{3})\b', subject, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    # Try body
    match = re.search(r'\b(PO-\d{4}-\d{3})\b', body, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


# Example usage and test cases
if __name__ == "__main__":
    test_cases = [
        # Single times
        ("0600", "0600"),
        ("1500", "1500"),
        ("3:00 PM", "1500"),
        ("10:30 AM", "1030"),
        ("3 PM", "1500"),

        # Time ranges (should return later time)
        ("between 1200 and 1400", "1400"),
        ("1-3 PM", "1500"),
        ("10:00 AM - 12:00 PM", "1200"),

        # Vague responses (should return None)
        ("running late", None),
        ("delayed", None),
        ("not sure", None),
    ]

    print("Testing ETA parser:\n")
    for body, expected in test_cases:
        result = parse_eta_from_email("RE: ETA Request", body)
        status = "PASS" if (result is not None and expected is not None) or (result is None and expected is None) else "FAIL"
        print(f"{status} '{body}' -> {result.strftime('%H%M') if result else 'None'} (expected: {expected})")
