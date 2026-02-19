"""
Email endpoints for viewing sent emails and controlling the IMAP poller.
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.services.email_service import email_service
from app.auth import get_current_user
from app.models import User, EmailLog
from app.database import get_db

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("/sent")
def get_sent_emails(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """
    Get recently sent emails from the database.
    Persists across server restarts (unlike the old in-memory list).
    """
    logs = (
        db.query(EmailLog)
        .order_by(EmailLog.created_at.desc())
        .limit(limit)
        .all()
    )

    emails = [
        {
            "id": log.id,
            "to": log.recipient,
            "subject": log.subject,
            "body": log.body[:300] if log.body else "",
            "status": log.status.value if log.status else "unknown",
            "sent_at": (log.sent_at or log.created_at).isoformat(),
            "message_id": log.message_id,
            "po_number": None,  # Could extract from subject
            "carrier_name": None,
            "method": "resend",
            "success": log.status.value == "sent" if log.status else False,
        }
        for log in logs
    ]

    return {
        "count": len(emails),
        "emails": emails,
    }


@router.get("/sent/count")
def get_sent_email_count(db: Session = Depends(get_db)):
    """Get the total count of sent emails (persistent)."""
    count = db.query(EmailLog).count()
    return {"count": count}


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
