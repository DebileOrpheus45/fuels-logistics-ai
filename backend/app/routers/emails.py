"""
Email endpoints for viewing sent emails and controlling the IMAP poller.
"""

from fastapi import APIRouter, Query, Depends

from app.services.email_service import email_service
from app.auth import get_current_user
from app.models import User

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


@router.get("/poller/status")
def get_poller_status(current_user: User = Depends(get_current_user)):
    """Get email poller running status."""
    from app.services.email_poller import _poller_thread, _stop_event
    running = (
        _poller_thread is not None
        and _poller_thread.is_alive()
        and (_stop_event is None or not _stop_event.is_set())
    )
    return {"running": running, "check_interval": 120 if running else None}


@router.post("/poller/start")
def start_poller(current_user: User = Depends(get_current_user)):
    """Start the email poller background thread."""
    from app.services.email_poller import _poller_thread, start_poller_thread
    if _poller_thread and _poller_thread.is_alive():
        return {"running": True, "message": "Already running"}
    start_poller_thread()
    return {"running": True, "message": "Poller started"}


@router.post("/poller/stop")
def stop_poller(current_user: User = Depends(get_current_user)):
    """Stop the email poller background thread."""
    from app.services.email_poller import stop_poller_thread
    stop_poller_thread()
    return {"running": False, "message": "Stop signal sent"}
