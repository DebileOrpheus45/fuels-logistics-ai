"""
Gmail API integration for sending real emails.

Setup Instructions:
1. Go to Google Cloud Console: https://console.cloud.google.com
2. Create a new project or select existing
3. Enable Gmail API: APIs & Services > Enable APIs > Gmail API
4. Create OAuth 2.0 credentials:
   - APIs & Services > Credentials > Create Credentials > OAuth client ID
   - Application type: Desktop app
   - Download the JSON file
5. Save the JSON file as 'gmail_credentials.json' in the backend folder
6. Run the setup script to authorize: python -m app.integrations.gmail_service

After setup, the service will use token.json for authentication.
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if google libraries are available
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logger.warning("Gmail libraries not installed. Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Paths for credentials
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'gmail_credentials.json')
TOKEN_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'token.json')


class GmailService:
    """Gmail API service for sending emails."""

    def __init__(self):
        self.service = None
        self.is_configured = False
        self.sent_emails = []  # Track sent emails

        if GMAIL_AVAILABLE:
            self._initialize()

    def _initialize(self):
        """Initialize Gmail API service."""
        creds = None

        # Load existing token
        if os.path.exists(TOKEN_PATH):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            except Exception as e:
                logger.error(f"Error loading token: {e}")

        # Refresh or get new credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None

        if creds and creds.valid:
            try:
                self.service = build('gmail', 'v1', credentials=creds)
                self.is_configured = True
                logger.info("Gmail service initialized successfully")
            except Exception as e:
                logger.error(f"Error building Gmail service: {e}")
        else:
            logger.warning("Gmail not configured. Run setup to authorize.")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_name: str = "Fuels Logistics AI"
    ) -> dict:
        """
        Send an email via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_name: Display name for sender

        Returns:
            Dict with send status and message ID
        """
        if not self.is_configured:
            logger.warning("Gmail not configured, falling back to mock")
            return self._mock_send(to_email, subject, body)

        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject

            msg_body = MIMEText(body, 'plain')
            message.attach(msg_body)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            # Track sent email
            email_record = {
                "to": to_email,
                "subject": subject,
                "body": body,
                "sent_at": datetime.utcnow().isoformat(),
                "message_id": sent_message['id'],
                "status": "sent"
            }
            self.sent_emails.append(email_record)

            logger.info(f"Email sent successfully to {to_email}, ID: {sent_message['id']}")

            return {
                "success": True,
                "message_id": sent_message['id'],
                "to": to_email,
                "subject": subject,
                "sent_at": email_record["sent_at"]
            }

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }

    def _mock_send(self, to_email: str, subject: str, body: str) -> dict:
        """Mock send for when Gmail is not configured."""
        email_record = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": f"mock-{len(self.sent_emails) + 1}",
            "status": "mock"
        }
        self.sent_emails.append(email_record)

        logger.info(f"[MOCK] Email to {to_email}: {subject}")

        return {
            "success": True,
            "message_id": email_record["message_id"],
            "to": to_email,
            "subject": subject,
            "sent_at": email_record["sent_at"],
            "mock": True
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
        This method matches the interface of the mock email service.
        """
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

        return self.send_email(to_email, subject, body)

    def get_sent_emails(self, limit: int = 10) -> list:
        """Get recently sent emails."""
        return self.sent_emails[-limit:]


def setup_gmail_auth():
    """
    Interactive setup for Gmail OAuth.
    Run this once to authorize the application.
    """
    if not GMAIL_AVAILABLE:
        print("Gmail libraries not installed.")
        print("Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Credentials file not found: {CREDENTIALS_PATH}")
        print("Please download OAuth credentials from Google Cloud Console")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the token
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())

    print(f"Authorization successful! Token saved to {TOKEN_PATH}")


# Create singleton instance
gmail_service = GmailService()


if __name__ == "__main__":
    setup_gmail_auth()
