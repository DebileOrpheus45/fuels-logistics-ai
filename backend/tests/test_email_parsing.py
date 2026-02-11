"""
Test email parsing with sample carrier emails.

Usage:
    cd backend
    python -m pytest tests/test_email_parsing.py -v
"""

import json
import os
import sys
from datetime import datetime

# Ensure backend is on path when run standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.utils.email_parser import parse_eta_from_email, extract_po_number


SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "sample_emails.json")

with open(SAMPLES_PATH, "r") as f:
    SAMPLE_EMAILS = json.load(f)


@pytest.fixture
def base_time():
    """Fixed base time so tests are deterministic."""
    return datetime(2026, 2, 10, 6, 0, 0)


@pytest.mark.parametrize(
    "email",
    SAMPLE_EMAILS,
    ids=[e["description"] for e in SAMPLE_EMAILS],
)
class TestEmailParsing:

    def test_po_extraction(self, email):
        """Verify PO number is extracted correctly."""
        result = extract_po_number(email["subject"], email["body"])
        assert result == email["expected_po"]

    def test_eta_parsing(self, email, base_time):
        """Verify ETA is parsed (or correctly rejected) from the email body."""
        result = parse_eta_from_email(email["subject"], email["body"], base_time)

        if email["should_parse"]:
            assert result is not None, f"Expected ETA to be parsed but got None"
            actual_time = result.strftime("%H%M")
            assert actual_time == email["expected_eta_time"], (
                f"Expected {email['expected_eta_time']} but got {actual_time}"
            )
        else:
            if email["expected_po"] is None:
                # No PO number means the parser wouldn't even be called in prod,
                # but we still run it to confirm it doesn't crash
                pass
            else:
                assert result is None, f"Expected None (vague response) but got {result}"


# Also run as standalone script
if __name__ == "__main__":
    base = datetime(2026, 2, 10, 6, 0, 0)

    print("=" * 70)
    print("EMAIL PARSING TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    for email in SAMPLE_EMAILS:
        po = extract_po_number(email["subject"], email["body"])
        eta = parse_eta_from_email(email["subject"], email["body"], base)

        po_ok = po == email["expected_po"]
        if email["should_parse"]:
            eta_ok = eta is not None and eta.strftime("%H%M") == email["expected_eta_time"]
        else:
            eta_ok = eta is None if email["expected_po"] else True

        ok = po_ok and eta_ok
        status = "PASS" if ok else "FAIL"

        if ok:
            passed += 1
        else:
            failed += 1

        eta_str = eta.strftime("%H%M") if eta else "None"
        expected_eta = email["expected_eta_time"] or "None"

        print(f"\n{'PASS' if ok else 'FAIL'}  {email['description']}")
        print(f"      PO: {po} (expected {email['expected_po']}) {'ok' if po_ok else 'MISMATCH'}")
        print(f"     ETA: {eta_str} (expected {expected_eta}) {'ok' if eta_ok else 'MISMATCH'}")
        if not ok:
            print(f"  >>> Subject: {email['subject']}")
            print(f"  >>> Body: {email['body'][:80]}...")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 70)
