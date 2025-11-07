#!/usr/bin/env python3
"""
Check the schema of the notifications table.
"""

import sqlite3
import os

def check_schema():
    """Display the schema of the notifications table."""
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get table schema
        cursor.execute("PRAGMA table_info(notifications)")
        columns = cursor.fetchall()

        print("Notifications table schema:")
        print(f"{'ID':<5} {'Column Name':<25} {'Type':<15} {'Not Null':<10} {'Default':<15}")
        print("=" * 80)

        for col in columns:
            print(f"{col[0]:<5} {col[1]:<25} {col[2]:<15} {col[3]:<10} {str(col[4]):<15}")

        conn.close()

    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 80)
    check_schema()
    print("=" * 80)
