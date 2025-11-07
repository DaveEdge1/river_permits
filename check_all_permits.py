#!/usr/bin/env python3
"""
Multi-user permit checker
Checks all enabled permits for all active users and sends notifications
"""
import sqlite3
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add parent directory to path to import permit_finder
sys.path.insert(0, os.path.dirname(__file__))

from permit_finder import PermitFinder
from notifier import Notifier

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

def get_all_enabled_permits():
    """Get all enabled permits for active users from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, u.email
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

def main():
    print("=" * 60)
    print(f"Multi-User Permit Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initialize permit finder
    finder = PermitFinder()

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

    # Track notifications to send per user
    notifications_by_user = defaultdict(lambda: defaultdict(list))

    # Check each permit
    for permit in permits:
        print(f"\nChecking: {permit['name']} (User: {permit['email']})")

        try:
            available = finder.check_permit_availability(
                facility_id=str(permit['facility_id']),
                start_date=permit['start_date'],
                end_date=permit['end_date'],
                min_people=permit['min_people'],
                max_people=permit['max_people']
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

                    # Record notifications
                    for avail in new_permits:
                        record_notification(
                            conn,
                            permit['user_id'],
                            permit['id'],
                            avail['date'],
                            avail['division_id'],
                            avail.get('division_name', f"Division {avail['division_id']}"),
                            avail.get('details', {}).get('remaining', 0)
                        )
                else:
                    print(f"  All available permits already notified")
            else:
                print(f"  No available permits found")

        except Exception as e:
            print(f"  ERROR: {e}")

    conn.close()

    # Send notifications to each user
    print("\n" + "=" * 60)
    print("Sending Notifications")
    print("=" * 60)

    if not notifications_by_user:
        print("No new permits to notify about")
        return

    for user_id, permit_notifications in notifications_by_user.items():
        # Get user email
        user_permit = next(p for p in permits if p['user_id'] == user_id)
        user_email = user_permit['email']

        print(f"\nUser: {user_email}")

        # Send one email per permit with available dates
        for permit_id, available_permits in permit_notifications.items():
            permit = next(p for p in permits if p['id'] == permit_id)

            print(f"  Sending notification for: {permit['name']} ({len(available_permits)} dates)")

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
                    print(f"    ✓ Notification sent successfully")
                else:
                    print(f"    ✗ Failed to send notification (check email configuration)")

            except Exception as e:
                import traceback
                print(f"    ✗ Error sending notification: {e}")
                print(f"       Details: {traceback.format_exc()}")

    print("\n" + "=" * 60)
    print("Check Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
