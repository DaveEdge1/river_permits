#!/usr/bin/env python3
"""
Test SendGrid email notification
Reads configuration from server/.env and sends a test email via SendGrid API
"""
import os
import sys
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
                # Set in os.environ so notifier can read it
                os.environ[key.strip()] = value.strip()
                env_vars[key.strip()] = value.strip()

    return env_vars

def test_sendgrid():
    """Test SendGrid email sending"""
    print("\n" + "=" * 60)
    print("SendGrid Email Test")
    print("=" * 60)

    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), 'server', '.env')
    print(f"\nLoading configuration from: {env_path}")

    config = load_env_file(env_path)

    if not config:
        print("ERROR: Could not load configuration from server/.env")
        return False

    # Check required configuration
    email_from = config.get('EMAIL_FROM')
    sendgrid_api_key = config.get('SENDGRID_API_KEY')

    print("\nConfiguration:")
    print(f"  EMAIL_SERVICE: {config.get('EMAIL_SERVICE', 'smtp')}")
    print(f"  EMAIL_FROM: {email_from}")
    print(f"  SENDGRID_API_KEY: {'*' * 20 if sendgrid_api_key else 'NOT SET'}")

    if not email_from or not sendgrid_api_key:
        print("\n❌ ERROR: Missing SendGrid configuration")
        if not email_from:
            print("   - EMAIL_FROM is not set")
        if not sendgrid_api_key:
            print("   - SENDGRID_API_KEY is not set")
        print("\nPlease update server/.env with:")
        print("  EMAIL_SERVICE=sendgrid")
        print("  EMAIL_FROM=grooverbookings@gmail.com")
        print("  SENDGRID_API_KEY=SG.your_api_key_here")
        return False

    # Import notifier
    sys.path.insert(0, os.path.dirname(__file__))
    from notifier import Notifier

    # Create test email content
    subject = "River Permits - SendGrid Test"
    html_body = """
    <html>
    <head></head>
    <body>
        <h2>SendGrid Test Successful!</h2>
        <p>This is a test message from your River Permits notification system using SendGrid API.</p>
        <p>If you're reading this, your SendGrid configuration is working correctly!</p>

        <h3>What This Means:</h3>
        <ul>
            <li>✓ SendGrid API key is valid</li>
            <li>✓ Sender email is verified</li>
            <li>✓ Emails can be sent over HTTPS (no SMTP port blocking)</li>
            <li>✓ Your permit notifications will work!</li>
        </ul>

        <h3>Sample Permit Alert:</h3>
        <p>Found 2 available permit(s) for <strong>San Juan River</strong></p>
        <ul>
            <li><strong>2025-06-15</strong> - Mexican Hat to Clay Hills - 3 remaining - <a href="https://www.recreation.gov/permits/250986">Book Now</a></li>
            <li><strong>2025-06-20</strong> - Mexican Hat to Clay Hills - 1 remaining - <a href="https://www.recreation.gov/permits/250986">Book Now</a></li>
        </ul>

        <p><strong>Next Steps:</strong></p>
        <ol>
            <li>The permit checker runs every 15 minutes automatically</li>
            <li>You'll receive emails like this when permits become available</li>
            <li>Book quickly - permits go fast!</li>
        </ol>
    </body>
    </html>
    """

    print("\n→ Initializing SendGrid notifier...")
    try:
        notifier = Notifier(
            email_enabled=True,
            sms_enabled=False,
            email_to=email_from  # Send to self for testing
        )

        if notifier.email_service != 'sendgrid':
            print(f"\n❌ WARNING: Email service is set to '{notifier.email_service}', not 'sendgrid'")
            print("   Make sure EMAIL_SERVICE=sendgrid is set in server/.env")
            if not notifier.sendgrid_client:
                print("   SendGrid client not initialized, falling back to SMTP")
                return False

        print(f"→ Sending test email to {email_from}...")
        success = notifier.send_email(subject, html_body, html=True)

        if success:
            print("\n" + "=" * 60)
            print("✓ SUCCESS! Test email sent via SendGrid!")
            print("=" * 60)
            print("\nCheck your inbox for the test message.")
            print("(Check spam folder if you don't see it)")
            print("\nYour permit notifications are now configured and working!")
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ FAILED to send email")
            print("=" * 60)
            return False

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())

        print("\n💡 Common Issues:")
        print("  1. SendGrid API key is invalid")
        print("     - Check that you copied the full key starting with 'SG.'")
        print("  2. Sender email not verified in SendGrid")
        print("     - Go to SendGrid → Settings → Sender Authentication")
        print("     - Click 'Verify a Single Sender'")
        print("     - Verify the email address you're using")
        print("  3. SendGrid package not installed")
        print("     - Run: pip install sendgrid")
        return False

if __name__ == "__main__":
    success = test_sendgrid()
    exit(0 if success else 1)
