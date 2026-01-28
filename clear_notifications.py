#!/usr/bin/env python3
"""
Clear all notification records from the database.
This allows you to test the notification system from a clean slate.
"""

import sqlite3
import os
from datetime import datetime

def clear_notifications():
    """Clear all records from the notifications table."""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count existing notifications
        cursor.execute("SELECT COUNT(*) FROM notifications")
        count = cursor.fetchone()[0]

        if count == 0:
            print("ℹ️  No notifications to clear (table is already empty)")
        else:
            # Clear all notifications
            cursor.execute("DELETE FROM notifications")
            conn.commit()
            print(f"✅ Cleared {count} notification record(s)")
            print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        conn.close()

    except Exception as e:
        print(f"❌ Error clearing notifications: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("Clear Notification Records")
    print("=" * 60)
    clear_notifications()
    print("=" * 60)
