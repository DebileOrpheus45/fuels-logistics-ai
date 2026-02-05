"""
Gmail IMAP email polling service for automated ETA reply processing.

This service:
1. Connects to Gmail via IMAP
2. Checks for unread emails matching ETA reply pattern
3. Parses subject/body and calls the inbound email API
4. Marks processed emails as read
5. Runs continuously in the background

Usage:
    python -m app.services.email_poller
"""

import imaplib
import email
from email.header import decode_header
import time
import requests
from datetime import datetime
import re
from typing import Optional, List, Dict
import logging

from app.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GmailETAPoller:
    """Poll Gmail inbox for carrier ETA replies and process them automatically."""

    def __init__(
        self,
        email_address: str,
        password: str,
        check_interval: int = 600,  # 10 minutes default
        api_base_url: str = "http://localhost:8000"
    ):
        """
        Initialize Gmail poller.

        Args:
            email_address: Gmail address
            password: Gmail app password (NOT regular password)
            check_interval: Seconds between checks (default 600 = 10 minutes)
            api_base_url: Base URL for the FastAPI backend
        """
        self.email_address = email_address
        self.password = password
        self.check_interval = check_interval
        self.api_base_url = api_base_url
        self.imap = None

    def connect(self) -> bool:
        """Connect to Gmail IMAP server."""
        try:
            logger.info(f"Connecting to Gmail IMAP for {self.email_address}...")
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(self.email_address, self.password)
            logger.info("Successfully connected to Gmail IMAP")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {e}")
            return False

    def disconnect(self):
        """Disconnect from Gmail IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
                logger.info("Disconnected from Gmail IMAP")
            except:
                pass

    def decode_subject(self, subject: str) -> str:
        """Decode email subject handling different encodings."""
        decoded_parts = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)

    def extract_body(self, msg) -> str:
        """Extract plain text body from email message."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except:
                body = str(msg.get_payload())

        # Clean up body - remove signatures, quoted text
        body = self.clean_body(body)
        return body

    def clean_body(self, body: str) -> str:
        """Clean email body by removing signatures and quoted replies."""
        # Remove common signature markers
        signature_markers = [
            '\n--\n', '\n-- \n',
            'Sent from my iPhone',
            'Sent from my Android',
            'Get Outlook for'
        ]

        for marker in signature_markers:
            if marker in body:
                body = body.split(marker)[0]

        # Remove quoted reply sections (lines starting with >)
        lines = body.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('>')]

        return '\n'.join(cleaned_lines).strip()

    def is_eta_reply(self, subject: str) -> bool:
        """Check if email subject indicates an ETA reply."""
        patterns = [
            r'RE:.*ETA',
            r'Re:.*ETA',
            r'RE:.*PO-\d{4}-\d{3}',
            r'Re:.*PO-\d{4}-\d{3}',
        ]

        for pattern in patterns:
            if re.search(pattern, subject, re.IGNORECASE):
                return True

        return False

    def process_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Process a single email and send to API.

        Returns:
            API response dict if successful, None otherwise
        """
        try:
            # Fetch email
            _, msg_data = self.imap.fetch(email_id, "(RFC822)")
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            # Extract fields
            subject = self.decode_subject(msg.get("Subject", ""))
            from_email = msg.get("From", "")
            body = self.extract_body(msg)

            logger.info(f"Processing email: {subject[:50]}... from {from_email}")

            # Check if it's an ETA reply
            if not self.is_eta_reply(subject):
                logger.debug(f"Skipping non-ETA email: {subject}")
                return None

            # Call the inbound email API
            api_url = f"{self.api_base_url}/api/email/inbound"
            payload = {
                "subject": subject,
                "body": body,
                "from_email": from_email,
                "received_at": datetime.now().isoformat()
            }

            logger.info(f"Calling API: {api_url}")
            logger.debug(f"Payload: {payload}")

            response = requests.post(api_url, json=payload, timeout=10)
            result = response.json()

            if result.get("success"):
                logger.info(f"✓ Successfully processed: {result.get('message')}")
                # Mark as read
                self.imap.store(email_id, '+FLAGS', '\\Seen')
                return result
            else:
                logger.warning(f"✗ Processing failed: {result.get('message')}")
                # Still mark as read to avoid reprocessing
                self.imap.store(email_id, '+FLAGS', '\\Seen')
                return result

        except Exception as e:
            logger.error(f"Error processing email {email_id}: {e}")
            return None

    def check_inbox(self) -> int:
        """
        Check inbox for unread ETA reply emails and process them.
        Uses IMAP SUBJECT filter to only fetch ETA-related emails,
        not every unread email in the inbox.

        Returns:
            Number of emails processed
        """
        try:
            # Select inbox
            self.imap.select("INBOX")

            # Search for unread emails with ETA-related subjects only
            # Run separate IMAP searches and combine results
            all_email_ids = set()

            for subject_filter in ['"ETA"', '"PO-20"']:
                _, msg_nums = self.imap.search(None, 'UNSEEN', 'SUBJECT', subject_filter)
                if msg_nums[0]:
                    all_email_ids.update(msg_nums[0].split())

            if not all_email_ids:
                logger.info("No unread ETA-related emails found")
                return 0

            email_ids = list(all_email_ids)
            logger.info(f"Found {len(email_ids)} unread ETA-related email(s)")

            processed_count = 0
            for email_id in email_ids:
                result = self.process_email(email_id)
                if result is not None:
                    processed_count += 1

            logger.info(f"Processed {processed_count} ETA reply email(s)")
            return processed_count

        except Exception as e:
            logger.error(f"Error checking inbox: {e}")
            return 0

    def run(self):
        """Run the polling loop continuously."""
        logger.info(f"Starting Gmail ETA poller (checking every {self.check_interval} seconds)...")

        while True:
            try:
                # Connect fresh for each check (prevents stale connection SSL errors)
                if not self.connect():
                    logger.error("Failed to connect, retrying in 60 seconds...")
                    time.sleep(60)
                    continue

                # Check inbox
                self.check_inbox()

                # Disconnect to prevent stale connection
                self.disconnect()
                self.imap = None

                # Wait for next check
                logger.debug(f"Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal, stopping poller...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")
                # Disconnect and reconnect on next iteration
                self.disconnect()
                self.imap = None
                time.sleep(60)

        # Cleanup
        self.disconnect()
        logger.info("Gmail ETA poller stopped")


def main():
    """Main entry point for running the poller as a standalone service."""
    # Load credentials from settings
    settings = get_settings()
    email_address = settings.gmail_user
    password = settings.gmail_app_password

    if not email_address or not password:
        logger.error("Gmail credentials not configured in .env file!")
        logger.error("Required variables: GMAIL_USER, GMAIL_APP_PASSWORD")
        return

    # Create and run poller
    poller = GmailETAPoller(
        email_address=email_address,
        password=password,
        check_interval=600,  # 10 minutes
        api_base_url="http://localhost:8000"
    )

    poller.run()


if __name__ == "__main__":
    main()
