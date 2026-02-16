"""
Unified email service using SendGrid HTTP API.

This is the ONLY email service in the application.
All email sending goes through SendGrid's HTTP API, which works on
Railway, Render, and other platforms that block outbound SMTP.

Usage:
  - Routers (loads, emails, email_inbound): import `email_service` singleton
  - Agents (coordinator, rules engine): import `send_eta_request` function
"""

import logging
from typing import Optional
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Cc
from sqlalchemy.orm import Session

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_sendgrid_config():
    """Get SendGrid config from settings."""
    settings = get_settings()
    return {
        "api_key": settings.sendgrid_api_key,
        "from_email": settings.sendgrid_from_email,
        "from_name": settings.sendgrid_from_name,
    }


def _send_via_sendgrid(
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
) -> dict:
    """
    Send an email via SendGrid HTTP API.
    This is the single source of truth for all email sending in the app.
    """
    config = _get_sendgrid_config()

    if not config["api_key"]:
        logger.warning(
            f"[SendGrid] API key not configured — email NOT sent to {to_email}: {subject}"
        )
        return {
            "success": False,
            "error": "SendGrid API key not configured. Set SENDGRID_API_KEY env var.",
            "to": to_email,
            "subject": subject,
            "method": "sendgrid",
        }

    try:
        message = Mail(
            from_email=Email(config["from_email"], config["from_name"]),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )
        if cc:
            message.add_cc(Cc(cc))

        client = SendGridAPIClient(config["api_key"])
        response = client.send(message)

        message_id = response.headers.get("X-Message-Id", "")
        logger.info(
            f"[SendGrid] Sent to {to_email} | Subject: {subject} | ID: {message_id}"
        )

        return {
            "success": True,
            "message_id": message_id,
            "to": to_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "method": "sendgrid",
        }

    except Exception as e:
        logger.error(f"[SendGrid] Failed to send to {to_email}: {e}")
        return {
            "success": False,
            "error": str(e),
            "to": to_email,
            "subject": subject,
            "method": "sendgrid",
        }


# ---------------------------------------------------------------------------
# Singleton service — used by loads router, emails router, email_inbound
# ---------------------------------------------------------------------------

class EmailService:
    """Lightweight wrapper around SendGrid for router-level email sending."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    def send_eta_request(
        self,
        to_email: str,
        carrier_name: str,
        po_number: str,
        site_name: str,
        hours_to_runout: Optional[float] = None,
        driver_name: Optional[str] = None,
    ) -> dict:
        """Send ETA request email to a carrier dispatcher."""
        urgency = ""
        if hours_to_runout and hours_to_runout < 24:
            urgency = f" URGENT: Site has only {hours_to_runout:.0f} hours of fuel remaining."
        elif hours_to_runout and hours_to_runout < 48:
            urgency = f" Note: Site has {hours_to_runout:.0f} hours of fuel remaining."

        subject = f"ETA Request - PO #{po_number}"
        body = (
            f"Hi {carrier_name} Dispatch,\n\n"
            f"Can you please provide an updated ETA for the following shipment?\n\n"
            f"PO Number: {po_number}\n"
            f"Destination: {site_name}\n"
            + (f"Driver: {driver_name}\n" if driver_name else "")
            + f"{urgency}\n\n"
            f"Please reply with the expected arrival time.\n\n"
            f"Thank you,\n"
            f"Fuels Logistics AI Coordinator"
        )

        result = _send_via_sendgrid(to_email, subject, body)

        # In-memory log
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "po_number": po_number,
            "carrier_name": carrier_name,
            "site_name": site_name,
            "sent_at": result.get("sent_at", datetime.utcnow().isoformat()),
            "success": result.get("success", False),
            "method": "sendgrid",
        })

        # Activity stream
        try:
            from app.database import SessionLocal
            from app.models import Activity, ActivityType

            db = SessionLocal()
            db.add(Activity(
                agent_id=None,
                activity_type=ActivityType.EMAIL_SENT,
                details={
                    "to": to_email,
                    "subject": subject,
                    "po_number": po_number,
                    "carrier_name": carrier_name,
                    "site_name": site_name,
                    "success": result.get("success", False),
                    "method": "sendgrid",
                },
            ))
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"Failed to log email activity: {e}")

        return result

    def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_message_id: Optional[str] = None,
        cc: Optional[str] = None,
    ) -> dict:
        """Send a reply email (used by email_inbound auto-reply)."""
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        result = _send_via_sendgrid(to_email, subject, body, cc=cc)

        self.sent_emails.append({
            "to": to_email,
            "cc": cc,
            "subject": subject,
            "sent_at": result.get("sent_at", datetime.utcnow().isoformat()),
            "success": result.get("success", False),
            "method": "sendgrid",
            "type": "auto_reply",
        })

        return result

    def get_sent_emails(self, limit: int = 10) -> list:
        """Get recently sent emails (for /api/emails/sent endpoint)."""
        return self.sent_emails[-limit:]


# Singleton
email_service = EmailService()


# ---------------------------------------------------------------------------
# DB-based functions — used by coordinator_agent and rules_engine
# ---------------------------------------------------------------------------

def send_eta_request(
    db: Session,
    load,
    carrier,
    sent_by_agent_id: Optional[int] = None,
    sent_by_user_id: Optional[int] = None,
):
    """
    Send ETA request email and log to EmailLog table.
    Used by coordinator_agent.py and rules_engine.py.
    """
    from app.models import EmailLog, EmailDeliveryStatus

    config = _get_sendgrid_config()

    site = load.destination_site
    subject = f"ETA Request - Load {load.po_number}"
    body = (
        f"Dear {carrier.carrier_name} Dispatch,\n\n"
        f"We are requesting an updated ETA for the following load:\n\n"
        f"PO Number: {load.po_number}\n"
        f"Destination: {site.consignee_name} ({site.consignee_code})\n"
        f"Destination Address: {site.address}\n"
        f"Product: {load.product_type}\n"
        f"Volume: {load.volume} gallons\n\n"
        f"Current ETA: {load.current_eta.strftime('%Y-%m-%d %H:%M') if load.current_eta else 'Not provided'}\n"
        f"Driver: {load.driver_name or 'Not assigned'}\n"
        f"Driver Phone: {load.driver_phone or 'Not provided'}\n\n"
        f"Please reply with the updated ETA.\n\n"
        f"Thank you,\n"
        f"Fuels Logistics AI Coordinator\n\n"
        f"---\n"
        f"This is an automated message.\n"
        f"Reply to: {config['from_email']}"
    )

    # Create email log entry
    email_log = EmailLog(
        recipient=carrier.dispatcher_email,
        subject=subject,
        body=body,
        template_id="eta_request",
        status=EmailDeliveryStatus.PENDING,
        load_id=load.id,
        carrier_id=carrier.id,
        sent_by_user_id=sent_by_user_id,
        sent_by_agent_id=sent_by_agent_id,
    )

    result = _send_via_sendgrid(carrier.dispatcher_email, subject, body)

    if result.get("success"):
        email_log.status = EmailDeliveryStatus.SENT
        email_log.sent_at = datetime.utcnow()
        email_log.message_id = result.get("message_id")
    else:
        email_log.status = EmailDeliveryStatus.FAILED
        email_log.bounce_reason = result.get("error", "Unknown error")

    db.add(email_log)
    db.commit()
    db.refresh(email_log)

    return email_log
