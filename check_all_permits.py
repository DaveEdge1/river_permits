#!/usr/bin/env python3
"""
Multi-user permit checker
Checks all enabled permits for all active users and sends notifications
Supports both email (SMTP/SendGrid) and push notifications (FCM)

Usage:
  python check_all_permits.py          # Normal mode - queries recreation.gov
  python check_all_permits.py --test   # Test mode - injects fake availability
"""
import sqlite3
import sys
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# Debug: Check environment BEFORE loading .env
print(f"DEBUG BEFORE load_dotenv: EMAIL_SERVICE = {os.getenv('EMAIL_SERVICE', 'NOT SET')}")

# Load environment variables from server/.env (override existing vars)
server_env_path = os.path.join(os.path.dirname(__file__), 'server', '.env')
load_dotenv(server_env_path, override=True)

# Debug: Check if SendGrid is configured AFTER loading .env
print(f"DEBUG AFTER load_dotenv: EMAIL_SERVICE = {os.getenv('EMAIL_SERVICE', 'NOT SET')}")
print(f"DEBUG AFTER load_dotenv: SENDGRID_API_KEY = {'SET' if os.getenv('SENDGRID_API_KEY') else 'NOT SET'}")

# Add parent directory to path to import permit_finder
sys.path.insert(0, os.path.dirname(__file__))

from permit_finder import PermitFinder
from notifier import Notifier
from fcm_notifier import FCMNotifier, get_user_device_tokens, deactivate_tokens, is_fcm_enabled

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

def get_all_enabled_permits():
    """Get all enabled permits for active users from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, u.email, u.push_enabled, u.email_enabled
        FROM permits p
        JOIN users u ON p.user_id = u.id
        WHERE p.enabled = 1 AND u.is_active = 1
        ORDER BY p.user_id, p.id
    """)

    permits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return permits

def check_if_notified(conn, user_id, permit_id, date, division_id):
    """Check if we've already sent notification for this permit/date/division"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM notifications
        WHERE user_id = ? AND permit_id = ? AND date = ? AND division_id = ?
    """, (user_id, permit_id, date, division_id))

    return cursor.fetchone() is not None

def record_notification(conn, user_id, permit_id, date, division_id, division_name, remaining):
    """Record that we sent a notification"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO notifications
        (user_id, permit_id, date, division_id, division_name, remaining)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, permit_id, date, division_id, division_name, remaining))

    conn.commit()


def generate_fake_availability(permit):
    """
    Generate fake permit availability for testing.
    Creates 3 fake available dates within the permit's date range.
    """
    start = datetime.strptime(permit['start_date'], "%Y-%m-%d")
    end = datetime.strptime(permit['end_date'], "%Y-%m-%d")

    # Generate 3 dates spread across the range
    total_days = (end - start).days
    if total_days < 3:
        dates = [start + timedelta(days=i) for i in range(total_days + 1)]
    else:
        interval = total_days // 3
        dates = [
            start + timedelta(days=interval),
            start + timedelta(days=interval * 2),
            start + timedelta(days=interval * 3 - 1)
        ]

    # Create fake availability entries
    fake_availability = []
    for i, date in enumerate(dates[:3]):  # Max 3 dates
        fake_availability.append({
            'date': date.strftime("%Y-%m-%d"),
            'facility_id': str(permit['facility_id']),
            'division_id': 'TEST001',
            'division_name': 'Test Launch Point',
            'details': {'remaining': (i + 1) * 2}  # 2, 4, 6 remaining
        })

    return fake_availability


def main(test_mode=False):
    print("=" * 60)
    print(f"Multi-User Permit Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if test_mode:
        print("*** TEST MODE - Using fake availability data ***")
    print("=" * 60)

    # Initialize permit finder (only used in normal mode)
    finder = PermitFinder() if not test_mode else None

    # Get all enabled permits
    permits = get_all_enabled_permits()

    if not permits:
        print("No enabled permits to check")
        return

    print(f"Checking {len(permits)} permit(s)")

    # Group permits by user
    permits_by_user = defaultdict(list)
    for permit in permits:
        permits_by_user[permit['user_id']].append(permit)

    # Connect to database for notifications tracking
    conn = sqlite3.connect(DB_PATH)

    # In test mode, clear previous test notifications so fake data triggers again
    if test_mode:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notifications WHERE division_id = 'TEST001'")
        deleted = cursor.rowcount
        conn.commit()
        if deleted > 0:
            print(f"Cleared {deleted} previous test notification(s)")

    # Track notifications to send per user
    notifications_by_user = defaultdict(lambda: defaultdict(list))

    # Check each permit
    for permit in permits:
        print(f"\nChecking: {permit['name']} (User: {permit['email']})")

        try:
            # In test mode, use fake availability data
            if test_mode:
                available = generate_fake_availability(permit)
                print(f"  [TEST] Generated {len(available)} fake permits")
            else:
                available = finder.check_permit_availability(
                    facility_id=str(permit['facility_id']),
                    start_date=permit['start_date'],
                    end_date=permit['end_date'],
                    party_size=permit.get('party_size', 1)
                )

            if available:
                print(f"  Found {len(available)} available permit(s)")

                # Filter out permits we've already notified about
                new_permits = []
                for avail in available:
                    if not check_if_notified(
                        conn,
                        permit['user_id'],
                        permit['id'],
                        avail['date'],
                        avail['division_id']
                    ):
                        new_permits.append(avail)

                if new_permits:
                    print(f"  {len(new_permits)} NEW permit(s) (not yet notified)")

                    # Group by permit for this user
                    notifications_by_user[permit['user_id']][permit['id']].extend(new_permits)

                    # NOTE: Don't record notifications yet - wait until email is sent successfully
                else:
                    print(f"  All available permits already notified")
            else:
                print(f"  No available permits found")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Send notifications to each user
    print("\n" + "=" * 60)
    print("Sending Notifications")
    print("=" * 60)

    if not notifications_by_user:
        conn.close()
        print("No new permits to notify about")
        return

    # Initialize FCM notifier (if configured)
    fcm_notifier = FCMNotifier()
    fcm_available = is_fcm_enabled()
    print(f"FCM Push Notifications: {'Enabled' if fcm_available else 'Disabled'}")

    for user_id, permit_notifications in notifications_by_user.items():
        # Get user info
        user_permit = next(p for p in permits if p['user_id'] == user_id)
        user_email = user_permit['email']
        push_enabled = user_permit.get('push_enabled', 1) == 1
        email_enabled = user_permit.get('email_enabled', 1) == 1

        print(f"\nUser: {user_email}")
        print(f"  Preferences: push={push_enabled}, email={email_enabled}")

        # Get device tokens for push notifications
        device_tokens = []
        if push_enabled and fcm_available:
            device_tokens = get_user_device_tokens(user_id, DB_PATH)
            print(f"  Device tokens: {len(device_tokens)}")

        # Build consolidated rivers data for single push notification
        rivers_data = []
        permits_to_record = []  # Track which permits to record after notification

        for permit_id, available_permits in permit_notifications.items():
            permit = next(p for p in permits if p['id'] == permit_id)
            print(f"  River: {permit['name']} ({len(available_permits)} dates)")

            rivers_data.append({
                'permit_name': permit['name'],
                'facility_id': permit.get('facility_id'),
                'permits': available_permits
            })

            # Track for recording later
            permits_to_record.append({
                'permit_id': permit_id,
                'available_permits': available_permits
            })

        push_notification_sent = False
        email_notification_sent = False

        # Send SINGLE push notification with all rivers (if enabled and tokens available)
        if push_enabled and device_tokens and rivers_data:
            try:
                result = fcm_notifier.send_multi_river_notification(
                    tokens=device_tokens,
                    rivers_data=rivers_data
                )

                if result['success_count'] > 0:
                    total_permits = sum(len(r['permits']) for r in rivers_data)
                    print(f"    ✓ Push notification sent to {result['success_count']} device(s) ({len(rivers_data)} rivers, {total_permits} permits)")
                    push_notification_sent = True

                # Deactivate any failed tokens
                if result['failed_tokens']:
                    deactivate_tokens(result['failed_tokens'], DB_PATH)

            except Exception as e:
                print(f"    ✗ Push notification error: {e}")

        # Send email notifications (one per river for detailed info)
        if email_enabled:
            for permit_id, available_permits in permit_notifications.items():
                permit = next(p for p in permits if p['id'] == permit_id)

                # Create notifier for this user
                notifier = Notifier(
                    email_enabled=True,
                    sms_enabled=False,
                    email_to=user_email
                )

                # Send notification
                try:
                    success = notifier.notify_permits_found(
                        permit_name=permit['name'],
                        available_permits=available_permits
                    )

                    if success:
                        print(f"    ✓ Email sent for {permit['name']}")
                        email_notification_sent = True
                    else:
                        print(f"    ✗ Failed to send email for {permit['name']}")

                except Exception as e:
                    print(f"    ✗ Email error for {permit['name']}: {e}")

        # Record notifications if ANY notification method succeeded
        if push_notification_sent or email_notification_sent:
            for record in permits_to_record:
                for avail in record['available_permits']:
                    record_notification(
                        conn,
                        user_id,
                        record['permit_id'],
                        avail['date'],
                        avail['division_id'],
                        avail.get('division_name', f"Division {avail['division_id']}"),
                        avail.get('details', {}).get('remaining', 0)
                    )
        else:
            print(f"    ✗ No notification sent - will retry on next check")

    conn.close()

    print("\n" + "=" * 60)
    print("Check Complete")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check permit availability and send notifications')
    parser.add_argument('--test', action='store_true',
                        help='Test mode: use fake availability data instead of querying recreation.gov')
    args = parser.parse_args()

    main(test_mode=args.test)
