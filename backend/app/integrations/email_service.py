"""
Email service for sending ETA requests to carriers.
Supports both mock (logging only) and real Gmail SMTP sending.
"""

from datetime import datetime
from typing import Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import get_settings
from app.database import SessionLocal
from app.models import Activity, ActivityType

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Email service that supports both mock and real Gmail SMTP sending."""

    def __init__(self):
        self.sent_emails = []  # In-memory log for testing/history
        self.gmail_enabled = settings.gmail_enabled
        self.gmail_user = settings.gmail_user
        self.gmail_app_password = settings.gmail_app_password

    def _send_via_gmail_smtp(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> dict:
        """
        Send email via Gmail SMTP.

        Requires:
        - GMAIL_USER environment variable (your Gmail address)
        - GMAIL_APP_PASSWORD environment variable (Gmail app password)
        - GMAIL_ENABLED=true

        To get an app password:
        1. Enable 2FA on your Google account
        2. Go to https://myaccount.google.com/apppasswords
        3. Generate a new app password for "Mail"
        4. Use that 16-character password (not your regular password)
        """
        if not self.gmail_user or not self.gmail_app_password:
            raise ValueError("Gmail credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD.")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Connect to Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_app_password)
                server.send_message(msg)

            logger.info(f"[GMAIL SENT] To: {to_email} | Subject: {subject}")

            return {
                "success": True,
                "message_id": f"gmail-{datetime.utcnow().timestamp()}",
                "to": to_email,
                "subject": subject,
                "sent_at": datetime.utcnow().isoformat(),
                "method": "gmail_smtp"
            }

        except Exception as e:
            logger.error(f"Failed to send email via Gmail: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email,
                "subject": subject,
                "method": "gmail_smtp"
            }

    def _send_mock(
        self,
        to_email: str,
        subject: str,
        body: str,
        po_number: str,
        carrier_name: str,
        site_name: str
    ) -> dict:
        """Mock email sending (logs only)."""
        email_record = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "po_number": po_number,
            "carrier_name": carrier_name,
            "site_name": site_name,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent",
            "method": "mock"
        }

        self.sent_emails.append(email_record)

        logger.info(f"[MOCK EMAIL] To: {to_email}")
        logger.info(f"[MOCK EMAIL] Subject: {subject}")
        logger.info(f"[MOCK EMAIL] Body:\n{body}")
        logger.info("-" * 50)

        return {
            "success": True,
            "message_id": f"mock-{len(self.sent_emails)}",
            "to": to_email,
            "subject": subject,
            "sent_at": email_record["sent_at"],
            "method": "mock"
        }

    def send_eta_request(
        self,
        to_email: str,
        carrier_name: str,
        po_number: str,
        site_name: str,
        hours_to_runout: Optional[float] = None,
        driver_name: Optional[str] = None
    ) -> dict:
        """
        Send an ETA request email to a carrier dispatcher.

        Args:
            to_email: Dispatcher email address
            carrier_name: Name of the carrier company
            po_number: Purchase order number
            site_name: Destination site name
            hours_to_runout: Hours until site runs out (for urgency)
            driver_name: Driver name if known

        Returns:
            Dict with send status and details
        """
        # Build email content
        urgency = ""
        if hours_to_runout and hours_to_runout < 24:
            urgency = f" URGENT: Site has only {hours_to_runout:.0f} hours of fuel remaining."
        elif hours_to_runout and hours_to_runout < 48:
            urgency = f" Note: Site has {hours_to_runout:.0f} hours of fuel remaining."

        subject = f"ETA Request - PO #{po_number}"

        body = f"""Hi {carrier_name} Dispatch,

Can you please provide an updated ETA for the following shipment?

PO Number: {po_number}
Destination: {site_name}
{f'Driver: {driver_name}' if driver_name else ''}
{urgency}

Please reply with the expected arrival time.

Thank you,
Fuels Logistics AI Coordinator"""

        # Send via Gmail or mock
        if self.gmail_enabled:
            result = self._send_via_gmail_smtp(to_email, subject, body)
        else:
            result = self._send_mock(to_email, subject, body, po_number, carrier_name, site_name)

        # Store in history
        sent_at = result.get("sent_at", datetime.utcnow().isoformat())
        self.sent_emails.append({
            "to": to_email,
            "subject": subject,
            "body": body,
            "po_number": po_number,
            "carrier_name": carrier_name,
            "site_name": site_name,
            "sent_at": sent_at,
            "success": result.get("success", False),
            "method": result.get("method", "unknown")
        })

        # Log to activity stream
        try:
            db = SessionLocal()
            activity = Activity(
                agent_id=None,
                activity_type=ActivityType.EMAIL_SENT,
                details={
                    "to": to_email,
                    "subject": subject,
                    "po_number": po_number,
                    "carrier_name": carrier_name,
                    "site_name": site_name,
                    "sent_at": sent_at,
                    "method": result.get("method", "unknown"),
                    "success": result.get("success", False),
                },
            )
            db.add(activity)
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"Failed to log email activity: {e}")

        return result

    def get_sent_emails(self, limit: int = 10) -> list:
        """Get recently sent emails (for debugging/UI)."""
        return self.sent_emails[-limit:]


# Singleton instance
email_service = EmailService()
