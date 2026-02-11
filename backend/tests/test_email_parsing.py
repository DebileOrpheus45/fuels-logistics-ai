"""
Test email parsing with sample carrier emails.

Supports two expected values per sample:
  - expected_eta_time: what the LLM parser should return (correct answer)
  - expected_eta_time_regex: what regex fallback returns (if different)

When ANTHROPIC_API_KEY is set, tests assert against expected_eta_time.
When not set (regex-only mode), tests accept expected_eta_time_regex as valid.

Usage:
    cd backend
    python tests/test_email_parsing.py           # standalone runner
    python -m pytest tests/test_email_parsing.py -v  # pytest
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.utils.email_parser import parse_eta_from_email, extract_po_number, _LLM_AVAILABLE

SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "sample_emails.json")

with open(SAMPLES_PATH, "r") as f:
    SAMPLE_EMAILS = json.load(f)


def _get_expected_eta(email: dict) -> str | None:
    """Pick the right expected ETA based on whether LLM is active."""
    if _LLM_AVAILABLE:
        return email["expected_eta_time"]
    # Regex mode: use regex-specific expectation if provided
    return email.get("expected_eta_time_regex", email["expected_eta_time"])


@pytest.fixture
def base_time():
    return datetime(2026, 2, 10, 6, 0, 0)


@pytest.mark.parametrize(
    "email",
    SAMPLE_EMAILS,
    ids=[e["description"] for e in SAMPLE_EMAILS],
)
class TestEmailParsing:

    def test_po_extraction(self, email):
        result = extract_po_number(email["subject"], email["body"])
        assert result == email["expected_po"]

    def test_eta_parsing(self, email, base_time):
        result = parse_eta_from_email(email["subject"], email["body"], base_time)
        expected_eta = _get_expected_eta(email)

        if email["should_parse"]:
            assert result is not None, "Expected ETA to be parsed but got None"
            actual_time = result.strftime("%H%M")
            assert actual_time == expected_eta, (
                f"Expected {expected_eta} but got {actual_time}"
            )
        else:
            if email["expected_po"] is None:
                pass  # no PO = wouldn't be called in prod
            else:
                assert result is None, f"Expected None (vague) but got {result}"


# Standalone runner
if __name__ == "__main__":
    # Trigger lazy init so _LLM_AVAILABLE is set
    parse_eta_from_email("test", "test", datetime.now())

    from app.utils.email_parser import _LLM_AVAILABLE as llm_active

    base = datetime(2026, 2, 10, 6, 0, 0)
    mode = "LLM + regex fallback" if llm_active else "Regex only (no ANTHROPIC_API_KEY)"

    print("=" * 70)
    print(f"EMAIL PARSING TEST SUITE  [{mode}]")
    print("=" * 70)

    passed = failed = 0

    for email in SAMPLE_EMAILS:
        po = extract_po_number(email["subject"], email["body"])
        eta = parse_eta_from_email(email["subject"], email["body"], base)

        expected_eta = email["expected_eta_time"] if llm_active else email.get("expected_eta_time_regex", email["expected_eta_time"])

        po_ok = po == email["expected_po"]
        if email["should_parse"]:
            eta_ok = eta is not None and eta.strftime("%H%M") == expected_eta
        else:
            eta_ok = eta is None if email["expected_po"] else True

        ok = po_ok and eta_ok
        if ok:
            passed += 1
        else:
            failed += 1

        eta_str = eta.strftime("%H%M") if eta else "None"
        exp_str = expected_eta or "None"
        note = f"  [{email['note']}]" if email.get("note") else ""

        print(f"\n{'PASS' if ok else 'FAIL'}  {email['description']}{note}")
        print(f"      PO: {po} (expected {email['expected_po']}) {'ok' if po_ok else 'MISMATCH'}")
        print(f"     ETA: {eta_str} (expected {exp_str}) {'ok' if eta_ok else 'MISMATCH'}")
        if not ok:
            print(f"  >>> Subject: {email['subject']}")
            print(f"  >>> Body: {email['body'][:80]}...")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 70)
