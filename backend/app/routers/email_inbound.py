"""
API endpoints for processing inbound carrier email replies.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import Load, Activity, ActivityType, User
from app.utils.email_parser import parse_eta_from_email, extract_po_number
from app.auth import get_current_user

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


@router.post("/inbound", response_model=InboundEmailResponse)
def process_inbound_email(
    email: InboundEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Process inbound carrier email reply and update load ETA.

    Expected email formats:
    - Subject: "RE: ETA Request - PO-2024-001"
    - Body: "0600" or "between 1200 and 1400" or "3 PM"

    Returns:
        - success: Whether ETA was successfully parsed and updated
        - po_number: Extracted PO number
        - parsed_eta: Parsed ETA datetime
        - message: Human-readable status message
    """
    # Extract PO number from subject or body
    po_number = extract_po_number(email.subject, email.body)
    if not po_number:
        return InboundEmailResponse(
            success=False,
            message="Could not extract PO number from email"
        )

    # Find the load
    load = db.query(Load).filter(Load.po_number == po_number).first()
    if not load:
        return InboundEmailResponse(
            success=False,
            po_number=po_number,
            message=f"Load not found: {po_number}"
        )

    # Parse ETA from email body
    received_at = email.received_at or datetime.now()
    parsed_eta = parse_eta_from_email(email.subject, email.body, received_at)

    if not parsed_eta:
        # Vague response - skip activity logging (no agent involved)
        return InboundEmailResponse(
            success=False,
            po_number=po_number,
            message="Vague ETA response - requires manual follow-up"
        )

    # Update load ETA
    old_eta = load.current_eta
    load.current_eta = parsed_eta
    load.last_eta_update_at = datetime.now()

    # Note: Activity logging requires agent_id (not nullable), so we skip it for inbound emails
    # This is a direct carrier response, not an agent action
    db.commit()

    return InboundEmailResponse(
        success=True,
        po_number=po_number,
        parsed_eta=parsed_eta,
        message=f"ETA updated from {old_eta} to {parsed_eta.strftime('%Y-%m-%d %H:%M')}"
    )


@router.post("/inbound/test", response_model=InboundEmailResponse)
def test_eta_parsing(email: InboundEmailRequest):
    """
    Test endpoint to parse ETA without updating database.
    Useful for validating email formats.
    """
    po_number = extract_po_number(email.subject, email.body)
    received_at = email.received_at or datetime.now()
    parsed_eta = parse_eta_from_email(email.subject, email.body, received_at)

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
