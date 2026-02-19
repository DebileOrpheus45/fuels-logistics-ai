"""
API endpoints for processing inbound carrier email replies.
"""

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from app.database import get_db
from app.models import (
    Load, InboundEmail, Activity, ActivityType,
    Escalation, IssueType, EscalationPriority,
)
from app.utils.email_parser import parse_eta_from_email_with_method, extract_po_number
from app.services.email_service import email_service
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


class InboundEmailRequest(BaseModel):
    """Request model for processing inbound carrier email."""
    subject: str
    body: str
    from_email: str
    received_at: Optional[datetime] = None
    message_id: Optional[str] = None  # Original email Message-ID for threading


class InboundEmailResponse(BaseModel):
    """Response model for inbound email processing."""
    success: bool
    po_number: Optional[str] = None
    parsed_eta: Optional[datetime] = None
    message: str
    auto_reply_sent: bool = False
    auto_reply_type: Optional[str] = None


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
    auto_reply_sent: bool = False
    auto_reply_type: Optional[str] = None
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
    Sends auto-reply: thank-you for good ETAs, escalation for vague ones.
    """
    received_at = email.received_at or datetime.now()
    settings = get_settings()

    # ── Self-email guard: skip processing for our own auto-replies ──
    # When we send auto-replies via Resend, they can land in the Gmail inbox
    # the IMAP poller watches, creating a loop. Detect and skip early.
    from_lower = email.from_email.lower().strip()
    is_self = settings.resend_from_email.lower() in from_lower
    if is_self:
        logger.info(f"Skipping self-email from {email.from_email} — not processing as carrier reply")
        # Save minimal record for audit trail, but don't parse or update anything
        inbound = InboundEmail(
            from_email=email.from_email,
            subject=email.subject,
            body=email.body,
            po_number=extract_po_number(email.subject, email.body),
            parse_success=False,
            parse_message="Skipped: self-email (auto-reply from our system)",
            received_at=received_at,
            processed_at=datetime.now(),
        )
        db.add(inbound)
        db.commit()
        return InboundEmailResponse(
            success=False,
            po_number=inbound.po_number,
            message="Skipped: self-email from our outbound address",
        )

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

    # ── Knowledge Graph Updates ──
    from app.services.knowledge_graph import on_eta_email_response, on_unparseable_email

    if success and load:
        # Carrier responded with valid ETA — update responsiveness
        try:
            on_eta_email_response(load.carrier_id, request_sent_at=load.last_email_sent)
        except Exception as kg_err:
            logger.warning(f"Knowledge graph update failed: {kg_err}")

    elif load and not parsed_eta:
        # Unparseable — check for important non-ETA content
        try:
            kg_result = on_unparseable_email(
                from_email=email.from_email,
                subject=email.subject,
                body=email.body,
                load_id=load.id
            )
            if kg_result.get("escalated"):
                message += f" (auto-escalated: {kg_result.get('issue_type')})"
        except Exception as kg_err:
            logger.warning(f"Knowledge graph unparseable check failed: {kg_err}")

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

    # --- Auto-reply to carrier ---
    auto_reply_type = None
    reply_result = None

    if success:
        # Case A: Good ETA — send thank-you
        reply_body = (
            f"Thank you for the update on PO #{po_number}.\n\n"
            f"We have recorded the ETA as {parsed_eta.strftime('%B %d, %Y at %I:%M %p')}.\n\n"
            f"If anything changes, please reply to this thread.\n\n"
            f"Best regards,\n"
            f"Fuels Logistics AI Coordinator"
        )
        reply_result = email_service.send_reply(
            to_email=email.from_email,
            subject=email.subject,
            body=reply_body,
            original_message_id=email.message_id,
        )
        auto_reply_type = "eta_acknowledged"

    elif load is not None and not parsed_eta:
        # Case B: Load found but vague/no ETA — escalate to coordinator
        coordinator_cc = settings.coordinator_email or None
        if not coordinator_cc:
            logger.warning("No COORDINATOR_EMAIL configured — escalation reply sent without CC")

        reply_body = (
            f"Thank you for your reply regarding PO #{po_number}.\n\n"
            f"We were unable to determine a specific ETA from your message. "
            f"A coordinator has been copied on this email and will follow up with you directly.\n\n"
            f"If you have an updated ETA, please reply with a specific time "
            f"(e.g., '3:30 PM' or '1530').\n\n"
            f"Best regards,\n"
            f"Fuels Logistics AI Coordinator"
        )
        reply_result = email_service.send_reply(
            to_email=email.from_email,
            subject=email.subject,
            body=reply_body,
            original_message_id=email.message_id,
            cc=coordinator_cc,
        )
        auto_reply_type = "coordinator_escalation"

        # Create escalation for the coordinator dashboard
        escalation = Escalation(
            issue_type=IssueType.NO_CARRIER_RESPONSE,
            priority=EscalationPriority.MEDIUM,
            description=(
                f"Carrier reply for {po_number} could not be parsed into a specific ETA. "
                f"From: {email.from_email}. "
                f"Message: \"{email.body[:200]}{'...' if len(email.body) > 200 else ''}\""
            ),
            load_id=load.id,
            site_id=load.destination_site_id,
            assigned_to=settings.coordinator_email or None,
        )
        db.add(escalation)

    # Update inbound email record with auto-reply status
    reply_actually_sent = reply_result and reply_result.get("success", False)
    if not reply_actually_sent and auto_reply_type:
        logger.warning(f"Auto-reply ({auto_reply_type}) FAILED for {po_number}: {reply_result}")
    if auto_reply_type:
        inbound.auto_reply_sent = reply_actually_sent
        inbound.auto_reply_type = auto_reply_type

        # Log auto-reply activity
        reply_subject = email.subject
        if not reply_subject.lower().startswith("re:"):
            reply_subject = f"Re: {reply_subject}"

        reply_activity = Activity(
            agent_id=None,
            activity_type=ActivityType.EMAIL_SENT,
            load_id=load.id if load else None,
            details={
                "to": email.from_email,
                "cc": settings.coordinator_email if auto_reply_type == "coordinator_escalation" else None,
                "subject": reply_subject,
                "po_number": po_number,
                "auto_reply_type": auto_reply_type,
                "success": reply_result.get("success", False) if reply_result else False,
            },
        )
        db.add(reply_activity)
        db.commit()

    return InboundEmailResponse(
        success=success,
        po_number=po_number,
        parsed_eta=parsed_eta,
        message=message,
        auto_reply_sent=auto_reply_type is not None,
        auto_reply_type=auto_reply_type,
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
