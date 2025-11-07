"""
Notification system for sending email and SMS alerts
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Notifier:
    """Handles email and SMS notifications for permit availability"""

    def __init__(
        self,
        email_enabled: bool = True,
        sms_enabled: bool = False,
        email_from: Optional[str] = None,
        email_to: Optional[str] = None,
        email_password: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587
    ):
        """
        Initialize the notifier

        Args:
            email_enabled: Whether to send email notifications
            sms_enabled: Whether to send SMS notifications
            email_from: Sender email address
            email_to: Recipient email address
            email_password: Email password or app password
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        self.email_enabled = email_enabled
        self.sms_enabled = sms_enabled

        # Email configuration
        self.email_from = email_from or os.getenv('EMAIL_FROM')
        self.email_to = email_to or os.getenv('EMAIL_TO')
        self.email_password = email_password or os.getenv('EMAIL_PASSWORD')
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))

        # SMS configuration (Twilio)
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from = os.getenv('TWILIO_FROM_NUMBER')
        self.twilio_to = os.getenv('TWILIO_TO_NUMBER')

        # Initialize Twilio client if SMS is enabled
        self.twilio_client = None
        if self.sms_enabled:
            try:
                from twilio.rest import Client
                if self.twilio_sid and self.twilio_token:
                    self.twilio_client = Client(self.twilio_sid, self.twilio_token)
                    logger.info("Twilio SMS client initialized")
                else:
                    logger.warning("SMS enabled but Twilio credentials not found")
                    self.sms_enabled = False
            except ImportError:
                logger.warning("Twilio package not installed, SMS notifications disabled")
                self.sms_enabled = False

    def send_email(self, subject: str, body: str, html: bool = False) -> bool:
        """
        Send an email notification

        Args:
            subject: Email subject
            body: Email body content
            html: Whether body is HTML formatted

        Returns:
            True if email was sent successfully
        """
        if not self.email_enabled:
            logger.info("Email notifications disabled")
            print("    ! Email notifications are disabled")
            return False

        if not all([self.email_from, self.email_to, self.email_password]):
            missing = []
            if not self.email_from: missing.append("EMAIL_FROM")
            if not self.email_to: missing.append("EMAIL_TO")
            if not self.email_password: missing.append("EMAIL_PASSWORD")
            logger.error(f"Email configuration incomplete. Missing: {', '.join(missing)}")
            print(f"    ! Email configuration incomplete. Missing: {', '.join(missing)}")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.email_to

            # Add body
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type))

            # Send email
            print(f"    → Connecting to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                print(f"    → Logging in as {self.email_from}...")
                server.login(self.email_from, self.email_password)
                print(f"    → Sending email to {self.email_to}...")
                server.send_message(msg)

            logger.info(f"Email sent successfully to {self.email_to}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            print(f"    ! SMTP Authentication failed: Check EMAIL_FROM and EMAIL_PASSWORD")
            print(f"       Error: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            print(f"    ! SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            print(f"    ! Failed to send email: {e}")
            import traceback
            print(f"       {traceback.format_exc()}")
            return False

    def send_sms(self, message: str) -> bool:
        """
        Send an SMS notification via Twilio

        Args:
            message: SMS message content

        Returns:
            True if SMS was sent successfully
        """
        if not self.sms_enabled or not self.twilio_client:
            logger.info("SMS notifications disabled or not configured")
            return False

        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_from,
                to=self.twilio_to
            )
            logger.info(f"SMS sent successfully (SID: {message.sid})")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def notify_permits_found(
        self,
        permit_name: str,
        available_permits: List[Dict]
    ) -> bool:
        """
        Send notifications about found permits

        Args:
            permit_name: Name of the permit/river
            available_permits: List of available permit entries

        Returns:
            True if at least one notification was sent successfully
        """
        if not available_permits:
            return False

        # Create notification content
        subject = f"River Permit Available: {permit_name}"

        # Sort permits by date
        sorted_permits = sorted(available_permits, key=lambda x: x['date'])

        # Build email body (HTML)
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>River Permit Availability Alert!</h2>
            <p>Found {len(available_permits)} available permit(s) for <strong>{permit_name}</strong></p>

            <h3>Available Dates:</h3>
            <ul>
        """

        for permit in sorted_permits:
            date = permit['date']
            details = permit.get('details', {})
            division_name = permit.get('division_name', f"Division {permit.get('division_id', '?')}")

            html_body += f"<li><strong>{date}</strong> - {division_name}"
            if isinstance(details, dict):
                if 'remaining' in details:
                    html_body += f" - {details['remaining']} remaining"
                if 'status' in details:
                    html_body += f" - Status: {details['status']}"
            html_body += f" - <a href='https://www.recreation.gov/permits/{permit['facility_id']}'>Book Now</a></li>\n"

        html_body += """
            </ul>

            <p><strong>Act fast!</strong> River permits can be claimed quickly.</p>
            <p>Visit <a href="https://www.recreation.gov">Recreation.gov</a> to book your permit.</p>
        </body>
        </html>
        """

        # Plain text version
        text_body = f"River Permit Available: {permit_name}\n\n"
        text_body += f"Found {len(available_permits)} available permit(s):\n\n"
        for permit in sorted_permits:
            division_name = permit.get('division_name', f"Division {permit.get('division_id', '?')}")
            remaining = permit.get('details', {}).get('remaining', '?')
            text_body += f"- {permit['date']} - {division_name} ({remaining} remaining)\n"
        text_body += f"\nBook at: https://www.recreation.gov/permits/{sorted_permits[0]['facility_id']}\n"

        # SMS message (brief)
        first_permit = sorted_permits[0]
        division_name = first_permit.get('division_name', f"Division {first_permit.get('division_id', '?')}")
        sms_message = f"River Permit Alert! {permit_name} - {division_name} available on {first_permit['date']}"
        if len(sorted_permits) > 1:
            sms_message += f" (+{len(sorted_permits)-1} more dates)"
        sms_message += f". Book now at recreation.gov"

        # Send notifications
        success = False

        if self.email_enabled:
            success = self.send_email(subject, html_body, html=True) or success

        if self.sms_enabled:
            success = self.send_sms(sms_message) or success

        return success


def test_notifier():
    """Test the notifier with sample data"""
    from dotenv import load_dotenv
    load_dotenv()

    notifier = Notifier(email_enabled=True, sms_enabled=False)

    # Test data
    sample_permits = [
        {
            'date': '2025-06-15',
            'facility_id': '233262',
            'permit_id': '1',
            'details': {'remaining': 3, 'status': 'Available'}
        },
        {
            'date': '2025-06-20',
            'facility_id': '233262',
            'permit_id': '2',
            'details': {'remaining': 1, 'status': 'Available'}
        }
    ]

    print("Testing notification system...")
    success = notifier.notify_permits_found("Grand Canyon Colorado River", sample_permits)
    print(f"Notification {'sent' if success else 'failed'}")


if __name__ == "__main__":
    test_notifier()
