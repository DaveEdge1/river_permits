"""
Notification system for sending email and SMS alerts
Supports SMTP and SendGrid API for email delivery
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
            email_password: Email password or app password (SMTP only)
            smtp_server: SMTP server address (SMTP only)
            smtp_port: SMTP server port (SMTP only)
        """
        self.email_enabled = email_enabled
        self.sms_enabled = sms_enabled

        # Determine email service (sendgrid or smtp)
        self.email_service = os.getenv('EMAIL_SERVICE', 'smtp').lower()

        # Email configuration
        self.email_from = email_from or os.getenv('EMAIL_FROM')
        self.email_to = email_to or os.getenv('EMAIL_TO')

        # SendGrid configuration
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.sendgrid_client = None

        # SMTP configuration (fallback)
        self.email_password = email_password or os.getenv('EMAIL_PASSWORD')
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))

        # Initialize SendGrid client if configured
        if self.email_service == 'sendgrid' and self.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
                logger.info("SendGrid API client initialized")
            except ImportError:
                logger.warning("SendGrid package not installed, falling back to SMTP")
                self.email_service = 'smtp'
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid client: {e}")
                self.email_service = 'smtp'

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
        Send an email notification via SendGrid API or SMTP

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

        # Route to appropriate send method
        if self.email_service == 'sendgrid' and self.sendgrid_client:
            return self._send_email_sendgrid(subject, body, html)
        else:
            return self._send_email_smtp(subject, body, html)

    def _send_email_sendgrid(self, subject: str, body: str, html: bool = False) -> bool:
        """Send email via SendGrid API"""
        if not all([self.email_from, self.email_to, self.sendgrid_api_key]):
            missing = []
            if not self.email_from: missing.append("EMAIL_FROM")
            if not self.email_to: missing.append("EMAIL_TO")
            if not self.sendgrid_api_key: missing.append("SENDGRID_API_KEY")
            logger.error(f"SendGrid configuration incomplete. Missing: {', '.join(missing)}")
            print(f"    ! SendGrid configuration incomplete. Missing: {', '.join(missing)}")
            return False

        try:
            from sendgrid.helpers.mail import Mail, Content

            # Create message
            print(f"    → Sending email via SendGrid...")
            print(f"    → From: {self.email_from}")
            print(f"    → To: {self.email_to}")

            # Create content
            if html:
                content = Content("text/html", body)
            else:
                content = Content("text/plain", body)

            # Create mail object
            mail = Mail(
                from_email=self.email_from,
                to_emails=self.email_to,
                subject=subject,
                html_content=body if html else None,
                plain_text_content=body if not html else None
            )

            # Send via SendGrid API
            response = self.sendgrid_client.send(mail)

            # Show detailed response info
            print(f"    → SendGrid Response Status: {response.status_code}")
            if hasattr(response, 'headers'):
                message_id = response.headers.get('x-message-id', 'N/A')
                print(f"    → Message ID: {message_id}")

            if response.body:
                print(f"    → Response Body: {response.body}")

            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent successfully via SendGrid to {self.email_to}")
                print(f"\n    ✓ Email accepted by SendGrid (Status: {response.status_code})")

                if response.status_code == 202:
                    print(f"\n    ⚠️  IMPORTANT: Status 202 = 'Accepted for delivery'")
                    print(f"    This means SendGrid accepted the request, but:")
                    print(f"    1. Check if sender '{self.email_from}' is VERIFIED in SendGrid")
                    print(f"    2. Check SendGrid Activity Feed to see delivery status")
                    print(f"    3. If sender not verified, emails will be silently dropped!")
                    print(f"\n    To verify sender:")
                    print(f"    → Go to: https://app.sendgrid.com/settings/sender_auth/senders")
                    print(f"    → Add '{self.email_from}' if not listed")
                    print(f"    → Click verification link in email")

                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                print(f"    ! SendGrid error: {response.status_code}")
                print(f"       {response.body}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            print(f"    ! Failed to send email via SendGrid: {e}")
            import traceback
            print(f"       {traceback.format_exc()}")
            return False

    def _send_email_smtp(self, subject: str, body: str, html: bool = False) -> bool:
        """Send email via SMTP"""
        if not all([self.email_from, self.email_to, self.email_password]):
            missing = []
            if not self.email_from: missing.append("EMAIL_FROM")
            if not self.email_to: missing.append("EMAIL_TO")
            if not self.email_password: missing.append("EMAIL_PASSWORD")
            logger.error(f"SMTP configuration incomplete. Missing: {', '.join(missing)}")
            print(f"    ! SMTP configuration incomplete. Missing: {', '.join(missing)}")
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
