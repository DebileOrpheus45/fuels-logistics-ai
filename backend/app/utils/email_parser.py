"""
Email parsing utilities for inbound carrier ETA replies.

Two-tier approach:
  1. LLM-based parsing (Claude Haiku) - handles real-world email noise
  2. Regex fallback - when no API key or LLM call fails

Safety: Always uses later time in range as worst-case scenario.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.config import now_local

logger = logging.getLogger(__name__)


# ============================================================
# PUBLIC API
# ============================================================

# Sentinel for "LLM explicitly says no ETA" vs "LLM unavailable"
_LLM_NO_RESULT = object()


def _strip_quoted_text(body: str) -> str:
    """
    Strip quoted reply text from email body.
    Gmail: 'On Mon, Jan 1, 2026 at 3:00 PM Name <email> wrote:'
    Outlook: '-----Original Message-----' or '________________________________'
    Generic: lines starting with '>'
    """
    lines = body.split('\n')
    cleaned = []
    for line in lines:
        # Gmail quote header
        if re.match(r'^On\s+\w{3},\s+\w{3}\s+\d', line, re.IGNORECASE):
            break
        if re.match(r'^On\s+\d{1,2}/\d{1,2}/\d{2,4}', line, re.IGNORECASE):
            break
        # Outlook separators
        if line.strip().startswith('-----Original Message'):
            break
        if re.match(r'^_{10,}', line.strip()):
            break
        # Dashed separator (common in auto-generated emails)
        if line.strip() == '--':
            break
        # Skip quoted lines
        if line.strip().startswith('>'):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned).strip()


def parse_eta_from_email(subject: str, body: str, sent_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse ETA from carrier email reply.
    Tries LLM first (handles phone numbers, PO numbers in body, etc.),
    falls back to regex when no API key or LLM errors.

    Returns:
        datetime representing the ETA, or None if vague / unparseable.
    """
    result, _ = parse_eta_from_email_with_method(subject, body, sent_date)
    return result


def parse_eta_from_email_with_method(subject: str, body: str, sent_date: Optional[datetime] = None) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parse ETA from carrier email reply. Returns (eta, method).
    method is "llm", "regex", or None.
    """
    if sent_date is None:
        sent_date = now_local().replace(tzinfo=None)

    llm_result = _parse_with_llm(subject, body, sent_date)
    if llm_result is _LLM_NO_RESULT:
        logger.info("ETA parse result: LLM says no ETA (vague/unknown)")
        return None, "llm"  # LLM explicitly says no ETA
    if llm_result is not None:
        logger.info(f"ETA parse result: LLM returned {llm_result}")
        return llm_result, "llm"

    # LLM unavailable or errored -> regex fallback
    logger.info("LLM unavailable or failed — falling back to regex")
    regex_result = _parse_with_regex(subject, body, sent_date)
    return regex_result, "regex" if regex_result else None


def extract_po_number(subject: str, body: str) -> Optional[str]:
    """
    Extract PO number from email subject or body.

    Examples:
        "RE: ETA Request - PO-2024-001" -> "PO-2024-001"
        "Re: Load PO-2024-003 ETA" -> "PO-2024-003"
    """
    match = re.search(r'\b(PO-\d{4}-\d{3})\b', subject, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r'\b(PO-\d{4}-\d{3})\b', body, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


# ============================================================
# LLM-BASED PARSING
# ============================================================

def _get_anthropic_client():
    """Get Anthropic client for LLM parsing. Returns None if unavailable."""
    # Try settings first, then fall back to os.environ
    api_key = ""
    try:
        from app.config import get_settings
        api_key = get_settings().anthropic_api_key
    except Exception as e:
        logger.warning(f"Failed to load settings for LLM parsing: {e}")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.info("No ANTHROPIC_API_KEY - email parser will use regex only")
        return None

    try:
        from anthropic import Anthropic
        return Anthropic(api_key=api_key)
    except ImportError:
        logger.warning("anthropic package not installed - email parser will use regex only")
        return None


_PARSE_PROMPT = """\
You are an ETA extraction tool for a fuel logistics system.
A carrier dispatcher replied to an ETA request email. Extract the delivery ETA from their reply.

The email was received at: {received_at}

Rules:
- Return ONLY valid JSON, no markdown fences, no explanation.
- If the email contains a specific time or time range, extract it.
- For time ranges, use the LATER time (worst-case).
- For RELATIVE time references like "couple hours", "in an hour", "about 2 hours", "30 minutes", calculate the actual time by adding the offset to the email received time shown above.
- For example, if the email was received at 1:46 PM and says "next couple hours", return "1546" (1:46 PM + 2 hours). For "about an hour", add 1 hour. For "30 minutes", add 30 minutes. Always round UP for vague durations ("couple" = 2, "few" = 3).
- "tomorrow" or "tmrw" means the next calendar day after the received date. "6 pm tomorrow" received on Feb 18 = "1800" (it will be assigned to Feb 19 automatically).
- Ignore times that are clearly part of phone numbers, PO numbers, addresses, or signatures.
- Ignore times in quoted reply text (text after "On ... wrote:" or "> " prefixed lines).
- The time_24h field MUST be a valid 24h time: hours 00-23, minutes 00-59. Never return values like "2700" or "2561".
- ETAs more than 3 days in the future are suspicious for fuel deliveries — return "vague" with a reason if the timeframe seems unreasonable.
- Only return "vague" for truly unresolvable responses (e.g. "running late" with no timeframe, "delayed indefinitely", "not sure", "don't know").
- If you cannot determine an ETA at all, return status "unknown".

Return this JSON shape:
{{"status": "ok", "time_24h": "HHMM"}}
or
{{"status": "vague", "reason": "brief reason"}}
or
{{"status": "unknown"}}

Examples:
- "ETA 0600" -> {{"status": "ok", "time_24h": "0600"}}
- "Should arrive 4:30 PM" -> {{"status": "ok", "time_24h": "1630"}}
- "between 1200 and 1400" -> {{"status": "ok", "time_24h": "1400"}}
- "1-3 PM" -> {{"status": "ok", "time_24h": "1500"}}
- "6 pm tomorrow" -> {{"status": "ok", "time_24h": "1800"}}
- "next couple hours" (received 1:46 PM) -> {{"status": "ok", "time_24h": "1546"}}
- "about an hour" (received 10:00 AM) -> {{"status": "ok", "time_24h": "1100"}}
- "30 minutes out" (received 3:15 PM) -> {{"status": "ok", "time_24h": "1545"}}
- "Running late, will update" -> {{"status": "vague", "reason": "running late, no timeframe"}}
- "I don't know yet" -> {{"status": "vague", "reason": "unknown eta"}}
- "next week sometime" -> {{"status": "vague", "reason": "too far in future for fuel delivery"}}
"""

def _parse_with_llm(subject: str, body: str, sent_date: datetime) -> Optional[datetime]:
    """
    Use Claude Haiku to parse ETA from email. Returns None to signal
    'fall through to regex' (LLM unavailable or call failed).
    Returns a datetime on success, or a special _LLM_NO_RESULT that
    we map to None (vague/unknown).
    """
    client = _get_anthropic_client()
    if client is None:
        logger.warning("LLM email parsing skipped: no Anthropic client (check ANTHROPIC_API_KEY)")
        return None  # no key -> fall through to regex

    logger.info("LLM email parsing: Anthropic client available, calling Claude Haiku")
    user_msg = f"Subject: {subject}\n\nBody:\n{body}"
    system_prompt = _PARSE_PROMPT.format(received_at=sent_date.strftime("%Y-%m-%d %I:%M %p"))

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )

        # Record LLM usage
        try:
            from app.database import SessionLocal
            from app.services.llm_usage import record_llm_usage
            _udb = SessionLocal()
            record_llm_usage(_udb, "email_parsing", "claude-haiku-4-5-20251001",
                             response.usage.input_tokens, response.usage.output_tokens)
            _udb.close()
        except Exception:
            pass

        raw = response.content[0].text.strip()
        logger.info(f"LLM raw response: {raw!r}")
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
        result = json.loads(raw)

        if result.get("status") == "ok":
            time_str = result["time_24h"]
            if not validate_time_str(time_str):
                logger.warning(f"LLM returned invalid time '{time_str}' — rejecting")
                return None
            eta = combine_date_and_time(sent_date, time_str)
            if eta is None:
                logger.warning(f"LLM time '{time_str}' failed guardrails (past/future) — rejecting")
                return _LLM_NO_RESULT  # Don't fall through to regex with bad data
            return eta

        if result.get("status") in ("vague", "unknown"):
            logger.info(f"LLM classified email as {result['status']}: {result.get('reason', '')}")
            # Return sentinel so we DON'T fall through to regex
            # (LLM explicitly says there's no ETA)
            return _LLM_NO_RESULT

    except json.JSONDecodeError as e:
        logger.warning(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.warning(f"LLM email parsing failed: {e}")

    return None  # fall through to regex


# ============================================================
# REGEX FALLBACK (original implementation)
# ============================================================

def _parse_with_regex(subject: str, body: str, sent_date: datetime) -> Optional[datetime]:
    """Regex-based ETA parsing. Used when LLM is unavailable."""
    # Strip quoted reply text to avoid parsing times from Gmail/Outlook quoted headers
    stripped = _strip_quoted_text(body)
    text = (stripped if stripped else body).lower().strip()

    # Check for vague/delayed responses
    vague_patterns = [
        r'\brunning\s+late\b',
        r'\bdelayed\b',
        r'\bnot\s+sure\b',
        r'\bdon\'t\s+know\b',
        r'\bunknown\b',
    ]
    for pattern in vague_patterns:
        if re.search(pattern, text):
            return None

    # Try time range first (worst case = later time)
    time_range = extract_time_range(text)
    if time_range:
        _, end_time = time_range
        return combine_date_and_time(sent_date, end_time)

    # Try single time
    single_time = extract_single_time(text)
    if single_time:
        return combine_date_and_time(sent_date, single_time)

    return None


def extract_time_range(text: str) -> Optional[Tuple[str, str]]:
    """Extract time range from text. Returns (start, end) in HHMM or None."""
    # "between HHMM and HHMM"
    match = re.search(r'between\s+(\d{3,4})\s+and\s+(\d{3,4})', text)
    if match:
        return (normalize_time(match.group(1)), normalize_time(match.group(2)))

    # "H-H PM/AM"
    match = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*(am|pm)', text)
    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        period = match.group(3)
        if period == 'pm' and start_hour != 12:
            start_hour += 12
            end_hour += 12
        elif period == 'am' and start_hour == 12:
            start_hour = 0
        if period == 'am' and end_hour == 12:
            end_hour = 0
        return (f"{start_hour:02d}00", f"{end_hour:02d}00")

    # "HH:MM AM - HH:MM PM"
    match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)', text)
    if match:
        start_hour, start_min, start_period = int(match.group(1)), int(match.group(2)), match.group(3)
        end_hour, end_min, end_period = int(match.group(4)), int(match.group(5)), match.group(6)
        if start_period == 'pm' and start_hour != 12:
            start_hour += 12
        if end_period == 'pm' and end_hour != 12:
            end_hour += 12
        return (f"{start_hour:02d}{start_min:02d}", f"{end_hour:02d}{end_min:02d}")

    return None


def extract_single_time(text: str) -> Optional[str]:
    """Extract single time from text. Returns HHMM format or None."""
    # 4-digit military time
    match = re.search(r'\b([0-2]\d)([0-5]\d)\b', text)
    if match:
        return f"{match.group(1)}{match.group(2)}"

    # H:MM AM/PM
    match = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', text)
    if match:
        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}{minute:02d}"

    # H AM/PM
    match = re.search(r'\b(\d{1,2})\s*(am|pm)\b', text)
    if match:
        hour, period = int(match.group(1)), match.group(2)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}00"

    return None


def normalize_time(time_str: str) -> str:
    """Normalize time string to HHMM format. "600" -> "0600"."""
    time_str = time_str.strip()
    if len(time_str) == 3:
        return f"0{time_str}"
    return time_str


def validate_time_str(time_str: str) -> bool:
    """Validate HHMM time string has real hour (0-23) and minute (0-59)."""
    if not re.match(r'^\d{4}$', time_str):
        return False
    hour = int(time_str[:2])
    minute = int(time_str[2:4])
    return 0 <= hour <= 23 and 0 <= minute <= 59


# Maximum hours into the future an ETA can be (fuel deliveries are same-day/next-day)
MAX_ETA_FUTURE_HOURS = 72
# Maximum hours in the past we'll accept (allow some clock drift)
MAX_ETA_PAST_HOURS = 1


def combine_date_and_time(base_date: datetime, time_str: str) -> Optional[datetime]:
    """
    Combine a date with HHMM time string.
    Returns None if the time is nonsensical or outside the reasonable window.

    Guardrails:
      - Hour must be 0-23, minute must be 0-59 (rejects "2700", "1561")
      - If time is in the past (today), assumes tomorrow
      - ETA must be within MAX_ETA_FUTURE_HOURS (72h) — rejects "next week" style results
      - ETA must not be more than MAX_ETA_PAST_HOURS (1h) in the past — rejects stale info
    """
    if not validate_time_str(time_str):
        logger.warning(f"Rejected invalid time '{time_str}': hour/minute out of range")
        return None

    hour = int(time_str[:2])
    minute = int(time_str[2:4])
    now = now_local().replace(tzinfo=None)
    eta = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If time is in the past today, assume tomorrow
    if eta < now:
        eta += timedelta(days=1)

    # Guardrail: too far in the future
    if eta > now + timedelta(hours=MAX_ETA_FUTURE_HOURS):
        logger.warning(f"Rejected ETA {eta} — more than {MAX_ETA_FUTURE_HOURS}h in the future")
        return None

    # Guardrail: too far in the past (even after tomorrow bump)
    if eta < now - timedelta(hours=MAX_ETA_PAST_HOURS):
        logger.warning(f"Rejected ETA {eta} — more than {MAX_ETA_PAST_HOURS}h in the past")
        return None

    return eta


# ============================================================
# Standalone test runner
# ============================================================

if __name__ == "__main__":
    test_cases = [
        ("0600", "0600"),
        ("1500", "1500"),
        ("3:00 PM", "1500"),
        ("10:30 AM", "1030"),
        ("3 PM", "1500"),
        ("between 1200 and 1400", "1400"),
        ("1-3 PM", "1500"),
        ("10:00 AM - 12:00 PM", "1200"),
        ("running late", None),
        ("delayed", None),
        ("not sure", None),
    ]

    print("Testing ETA parser:\n")
    for body, expected in test_cases:
        result = parse_eta_from_email("RE: ETA Request", body)
        status = "PASS" if (result is not None and expected is not None) or (result is None and expected is None) else "FAIL"
        print(f"{status} '{body}' -> {result.strftime('%H%M') if result else 'None'} (expected: {expected})")
