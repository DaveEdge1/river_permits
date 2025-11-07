#!/usr/bin/env python3
"""
Check what's currently in the notifications table.
"""

import sqlite3
import os
from datetime import datetime

def check_notifications():
    """Display all records from the notifications table."""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count notifications
        cursor.execute("SELECT COUNT(*) FROM notifications")
        count = cursor.fetchone()[0]

        print(f"Total notifications in database: {count}")
        print()

        if count > 0:
            # Show all notifications
            cursor.execute("""
                SELECT
                    n.id,
                    n.user_id,
                    n.permit_id,
                    n.available_date,
                    n.division_id,
                    n.division_name,
                    n.remaining_permits,
                    n.notified_at,
                    p.facility_id,
                    u.email
                FROM notifications n
                LEFT JOIN permits p ON n.permit_id = p.id
                LEFT JOIN users u ON n.user_id = u.id
                ORDER BY n.notified_at DESC
            """)

            notifications = cursor.fetchall()

            print(f"{'ID':<5} {'User Email':<30} {'Facility':<10} {'Date':<12} {'Division':<20} {'Notified At'}")
            print("=" * 110)

            for notif in notifications:
                print(f"{notif['id']:<5} {notif['email']:<30} {notif['facility_id']:<10} {notif['available_date']:<12} {notif['division_name']:<20} {notif['notified_at']}")

        conn.close()

    except Exception as e:
        print(f"❌ Error checking notifications: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 110)
    print(f"Notification Records Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 110)
    check_notifications()
    print("=" * 110)
