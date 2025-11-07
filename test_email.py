#!/usr/bin/env python3
"""
Test email notification system
Reads configuration from server/.env and sends a test email
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def load_env_file(env_path):
    """Load environment variables from .env file"""
    env_vars = {}
    if not os.path.exists(env_path):
        print(f"ERROR: {env_path} not found!")
        return env_vars

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

def send_test_email(config):
    """Send a test email using the same method as notifier.py"""

    print("\n" + "=" * 60)
    print("Email Notification Test")
    print("=" * 60)

    # Get configuration
    email_from = config.get('EMAIL_FROM')
    email_password = config.get('EMAIL_PASSWORD')
    smtp_server = config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(config.get('SMTP_PORT', '587'))

    print("\nConfiguration:")
    print(f"  SMTP Server: {smtp_server}:{smtp_port}")
    print(f"  From: {email_from}")
    print(f"  To: {email_from} (sending to self)")

    # Validate configuration
    if not email_from or not email_password:
        print("\n❌ ERROR: Missing email configuration")
        if not email_from:
            print("   - EMAIL_FROM is not set")
        if not email_password:
            print("   - EMAIL_PASSWORD is not set")
        print("\nPlease update server/.env with your email credentials")
        return False

    # Create test message
    subject = "River Permits - Test Notification"

    html_body = """
    <html>
    <head></head>
    <body>
        <h2>Email Test Successful!</h2>
        <p>This is a test message from your River Permits notification system.</p>
        <p>If you're reading this, your email configuration is working correctly!</p>

        <h3>Configuration Details:</h3>
        <ul>
            <li><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</li>
            <li><strong>From Address:</strong> {email_from}</li>
        </ul>

        <p>Your permit notifications will be sent using these settings.</p>
    </body>
    </html>
    """.format(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        email_from=email_from
    )

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = email_from  # Send to self for testing
        msg.attach(MIMEText(html_body, 'html'))

        print("\n→ Connecting to SMTP server...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            print("→ Starting TLS...")
            server.starttls()

            print(f"→ Logging in as {email_from}...")
            server.login(email_from, email_password)

            print(f"→ Sending test email to {email_from}...")
            server.send_message(msg)

        print("\n" + "=" * 60)
        print("✓ SUCCESS! Test email sent successfully!")
        print("=" * 60)
        print("\nCheck your inbox for the test message.")
        print("(Check spam folder if you don't see it)")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "=" * 60)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nPossible causes:")
        print("  1. Incorrect email password")
        print("  2. Gmail users: Need to use an App Password")
        print("     - Visit: https://myaccount.google.com/apppasswords")
        print("     - Create an app password for 'Mail'")
        print("     - Use that 16-character password in EMAIL_PASSWORD")
        print("  3. 2-Step Verification not enabled (required for App Passwords)")
        return False

    except smtplib.SMTPException as e:
        print("\n" + "=" * 60)
        print("❌ SMTP ERROR")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nCheck your SMTP server settings in server/.env")
        return False

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False

def main():
    # Load environment from server/.env
    env_path = os.path.join(os.path.dirname(__file__), 'server', '.env')

    print(f"Loading configuration from: {env_path}")

    config = load_env_file(env_path)

    if not config:
        print("ERROR: Could not load configuration from server/.env")
        return

    # Send test email
    success = send_test_email(config)

    if not success:
        exit(1)

if __name__ == "__main__":
    main()
