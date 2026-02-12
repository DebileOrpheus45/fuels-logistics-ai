"""
API endpoints for processing inbound carrier email replies.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models import Load, InboundEmail, Activity, ActivityType
from app.utils.email_parser import parse_eta_from_email_with_method, extract_po_number

router = APIRouter(prefix="/api/email", tags=["email"])


class InboundEmailRequest(BaseModel):
    """Request model for processing inbound carrier email."""
    subject: str
    body: str
    from_email: str
    received_at: Optional[datetime] = None


class InboundEmailResponse(BaseModel):
    """Response model for inbound email processing."""
    success: bool
    po_number: Optional[str] = None
    parsed_eta: Optional[datetime] = None
    message: str


class InboundEmailOut(BaseModel):
    """Response model for listing inbound emails."""
    id: int
    from_email: str
    subject: str
    body: str
    po_number: Optional[str] = None
    parsed_eta: Optional[datetime] = None
    parse_method: Optional[str] = None
    parse_success: bool
    parse_message: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: datetime

    class Config:
        from_attributes = True


@router.post("/inbound", response_model=InboundEmailResponse)
def process_inbound_email(
    email: InboundEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Process inbound carrier email reply and update load ETA.
    Saves every inbound email for audit trail regardless of parse outcome.
    """
    received_at = email.received_at or datetime.now()

    # Extract PO number from subject or body
    po_number = extract_po_number(email.subject, email.body)

    # Find the load (if PO found)
    load = None
    if po_number:
        load = db.query(Load).filter(Load.po_number == po_number).first()

    # Parse ETA from email body
    parsed_eta, parse_method = parse_eta_from_email_with_method(email.subject, email.body, received_at)

    # Build result message
    if not po_number:
        success = False
        message = "Could not extract PO number from email"
    elif not load:
        success = False
        message = f"Load not found: {po_number}"
    elif not parsed_eta:
        success = False
        message = "Vague ETA response - requires manual follow-up"
    else:
        success = True
        old_eta = load.current_eta
        load.current_eta = parsed_eta
        load.last_eta_update_at = datetime.now()
        message = f"ETA updated from {old_eta} to {parsed_eta.strftime('%Y-%m-%d %H:%M')}"

    # Save inbound email record (always, for audit trail)
    inbound = InboundEmail(
        from_email=email.from_email,
        subject=email.subject,
        body=email.body,
        po_number=po_number,
        load_id=load.id if load else None,
        parsed_eta=parsed_eta,
        parse_method=parse_method,
        parse_success=success,
        parse_message=message,
        received_at=received_at,
        processed_at=datetime.now(),
    )
    db.add(inbound)

    # Log to activity stream
    activity = Activity(
        agent_id=None,
        activity_type=ActivityType.EMAIL_RECEIVED,
        load_id=load.id if load else None,
        details={
            "from_email": email.from_email,
            "subject": email.subject,
            "po_number": po_number,
            "parsed_eta": parsed_eta.isoformat() if parsed_eta else None,
            "parse_method": parse_method,
            "parse_success": success,
            "message": message,
        },
    )
    db.add(activity)
    db.commit()

    return InboundEmailResponse(
        success=success,
        po_number=po_number,
        parsed_eta=parsed_eta,
        message=message,
    )


@router.get("/inbound", response_model=List[InboundEmailOut])
def get_inbound_emails(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """Get recent inbound carrier emails, newest first."""
    emails = (
        db.query(InboundEmail)
        .order_by(InboundEmail.created_at.desc())
        .limit(limit)
        .all()
    )
    return emails


@router.post("/inbound/test", response_model=InboundEmailResponse)
def test_eta_parsing(email: InboundEmailRequest):
    """
    Test endpoint to parse ETA without updating database.
    Useful for validating email formats.
    """
    po_number = extract_po_number(email.subject, email.body)
    received_at = email.received_at or datetime.now()
    parsed_eta, _ = parse_eta_from_email_with_method(email.subject, email.body, received_at)

    if not po_number:
        return InboundEmailResponse(
            success=False,
            message="Could not extract PO number"
        )

    if not parsed_eta:
        return InboundEmailResponse(
            success=False,
            po_number=po_number,
            message="Could not parse ETA (vague response)"
        )

    return InboundEmailResponse(
        success=True,
        po_number=po_number,
        parsed_eta=parsed_eta,
        message=f"Successfully parsed: {parsed_eta.strftime('%Y-%m-%d %H:%M')}"
    )
