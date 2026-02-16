"""
Email endpoints for viewing sent emails (mock implementation).
"""

from fastapi import APIRouter, Query

from app.services.email_service import email_service
from app.auth import get_current_user

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("/sent")
def get_sent_emails(limit: int = Query(default=20, le=100)):
    """
    Get recently sent emails (mock emails for testing).
    In production, this would query actual sent email records.
    """
    emails = email_service.get_sent_emails(limit=limit)
    return {
        "count": len(emails),
        "emails": emails
    }


@router.get("/sent/count")
def get_sent_email_count():
    """Get the count of emails sent in this session."""
    return {
        "count": len(email_service.sent_emails)
    }
