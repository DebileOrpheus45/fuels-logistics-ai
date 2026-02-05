"""
Real email sending service using SendGrid.

Replaces the mocked email functionality with actual SMTP delivery.
"""

import os
from typing import Optional
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

from app.models import EmailLog, EmailDeliveryStatus, Load, Carrier, User, AIAgent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@fuelslogistics.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Fuels Logistics AI Coordinator")
SENDGRID_ENABLED = os.getenv("SENDGRID_ENABLED", "false").lower() == "true"


class EmailService:
    """Service for sending emails via SendGrid and logging delivery."""

    def __init__(self, db: Session):
        self.db = db
        self.client = None
        if SENDGRID_ENABLED and SENDGRID_API_KEY:
            self.client = SendGridAPIClient(SENDGRID_API_KEY)

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        template_id: Optional[str] = None,
        load_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        sent_by_user_id: Optional[int] = None,
        sent_by_agent_id: Optional[int] = None,
    ) -> EmailLog:
        """
        Send an email and log the delivery.

        Args:
            recipient: Email address to send to
            subject: Email subject line
            body: Email body (plain text or HTML)
            template_id: Optional template identifier
            load_id: Optional related load ID
            carrier_id: Optional related carrier ID
            sent_by_user_id: Optional user who triggered the email
            sent_by_agent_id: Optional agent who sent the email

        Returns:
            EmailLog object with delivery status
        """
        # Create email log entry
        email_log = EmailLog(
            recipient=recipient,
            subject=subject,
            body=body,
            template_id=template_id,
            status=EmailDeliveryStatus.PENDING,
            load_id=load_id,
            carrier_id=carrier_id,
            sent_by_user_id=sent_by_user_id,
            sent_by_agent_id=sent_by_agent_id,
        )

        try:
            if not SENDGRID_ENABLED or not self.client:
                # SendGrid not configured - log only (like mock mode)
                logger.warning(
                    f"SendGrid disabled - email not sent to {recipient}: {subject}"
                )
                email_log.status = EmailDeliveryStatus.PENDING
                email_log.bounce_reason = "SendGrid not configured (SENDGRID_ENABLED=false)"
                self.db.add(email_log)
                self.db.commit()
                self.db.refresh(email_log)
                return email_log

            # Create SendGrid message
            message = Mail(
                from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
                to_emails=To(recipient),
                subject=subject,
                plain_text_content=Content("text/plain", body),
            )

            # Send via SendGrid
            response = self.client.send(message)

            # Update email log with success
            email_log.status = EmailDeliveryStatus.SENT
            email_log.sent_at = datetime.utcnow()
            email_log.message_id = response.headers.get("X-Message-Id")

            logger.info(
                f"Email sent successfully to {recipient}: {subject} (Message ID: {email_log.message_id})"
            )

        except Exception as e:
            # Update email log with failure
            email_log.status = EmailDeliveryStatus.FAILED
            email_log.bounce_reason = str(e)
            logger.error(f"Failed to send email to {recipient}: {e}")

        # Save to database
        self.db.add(email_log)
        self.db.commit()
        self.db.refresh(email_log)

        return email_log

    def send_eta_request_email(
        self,
        load: Load,
        carrier: Carrier,
        sent_by_agent_id: Optional[int] = None,
        sent_by_user_id: Optional[int] = None,
    ) -> EmailLog:
        """
        Send ETA request email to carrier dispatcher.

        This is the primary use case - agent requesting ETA from carrier.
        """
        subject = f"ETA Request - Load {load.po_number}"

        body = f"""
Dear {carrier.carrier_name} Dispatch,

We are requesting an updated ETA for the following load:

PO Number: {load.po_number}
Destination: {load.destination_site.consignee_name} ({load.destination_site.consignee_code})
Destination Address: {load.destination_site.address}
Product: {load.product_type}
Volume: {load.volume} gallons

Current ETA: {load.current_eta.strftime('%Y-%m-%d %H:%M') if load.current_eta else 'Not provided'}
Driver: {load.driver_name or 'Not assigned'}
Driver Phone: {load.driver_phone or 'Not provided'}

Please reply to this email with the updated ETA in one of these formats:
- Military time (e.g., "1430")
- 12-hour format (e.g., "2:30 PM")
- Time range (e.g., "between 1400 and 1600")

If you have any questions, please contact our dispatch team.

Thank you,
Fuels Logistics AI Coordinator

---
This is an automated message. Please do not reply directly to this email address.
Reply to: {SENDGRID_FROM_EMAIL}
        """.strip()

        return self.send_email(
            recipient=carrier.dispatcher_email,
            subject=subject,
            body=body,
            template_id="eta_request",
            load_id=load.id,
            carrier_id=carrier.id,
            sent_by_agent_id=sent_by_agent_id,
            sent_by_user_id=sent_by_user_id,
        )

    def get_email_history(
        self,
        load_id: Optional[int] = None,
        carrier_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[EmailLog]:
        """Get email history, optionally filtered by load or carrier."""
        query = self.db.query(EmailLog).order_by(EmailLog.created_at.desc())

        if load_id:
            query = query.filter(EmailLog.load_id == load_id)

        if carrier_id:
            query = query.filter(EmailLog.carrier_id == carrier_id)

        return query.limit(limit).all()

    def update_delivery_status(
        self,
        message_id: str,
        status: EmailDeliveryStatus,
        bounce_reason: Optional[str] = None,
    ):
        """
        Update email delivery status based on webhook callback.

        This would be called by a webhook endpoint that receives
        SendGrid delivery events (delivered, bounced, complained, etc.)
        """
        email_log = (
            self.db.query(EmailLog).filter(EmailLog.message_id == message_id).first()
        )

        if not email_log:
            logger.warning(f"Email log not found for message ID: {message_id}")
            return

        email_log.status = status
        email_log.updated_at = datetime.utcnow()

        if status == EmailDeliveryStatus.DELIVERED:
            email_log.delivered_at = datetime.utcnow()
        elif status == EmailDeliveryStatus.BOUNCED:
            email_log.bounced_at = datetime.utcnow()
            email_log.bounce_reason = bounce_reason
        elif status == EmailDeliveryStatus.COMPLAINED:
            email_log.complaint_at = datetime.utcnow()

        self.db.commit()
        logger.info(f"Updated email status to {status} for message {message_id}")


def send_eta_request(
    db: Session,
    load: Load,
    carrier: Carrier,
    sent_by_agent_id: Optional[int] = None,
    sent_by_user_id: Optional[int] = None,
) -> EmailLog:
    """
    Convenience function to send ETA request email.

    This is the function that agents will call.
    """
    email_service = EmailService(db)
    return email_service.send_eta_request_email(
        load=load,
        carrier=carrier,
        sent_by_agent_id=sent_by_agent_id,
        sent_by_user_id=sent_by_user_id,
    )
