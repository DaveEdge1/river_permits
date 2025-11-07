#!/usr/bin/env python3
"""
Diagnostic script to debug check_all_permits.py hanging issue
"""
import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'permits.db')

print("=" * 60)
print(f"Database Diagnostic - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

print(f"\nDatabase path: {DB_PATH}")
print(f"Database exists: {os.path.exists(DB_PATH)}")

if os.path.exists(DB_PATH):
    import stat
    st = os.stat(DB_PATH)
    print(f"Database size: {st.st_size} bytes")
    print(f"Last modified: {datetime.fromtimestamp(st.st_mtime)}")
    print(f"Permissions: {stat.filemode(st.st_mode)}")

print("\nAttempting to connect to database...")
try:
    conn = sqlite3.connect(DB_PATH)
    print("✓ Connected successfully")

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\nChecking tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Found {len(tables)} table(s):")
    for table in tables:
        print(f"  - {table['name']}")

    print("\nChecking permits...")
    try:
        cursor.execute("""
            SELECT p.*, u.email
            FROM permits p
            JOIN users u ON p.user_id = u.id
            WHERE p.enabled = 1 AND u.is_active = 1
            ORDER BY p.id
        """)

        permits = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(permits)} enabled permit(s):")

        for permit in permits:
            print(f"\n  Permit #{permit['id']}:")
            print(f"    Name: {permit['name']}")
            print(f"    User: {permit['email']}")
            print(f"    Facility ID: {permit['facility_id']}")
            print(f"    Date Range: {permit['start_date']} to {permit['end_date']}")
            print(f"    Party Size: {permit['min_people']}-{permit['max_people']}")
            print(f"    Enabled: {permit['enabled']}")

    except sqlite3.OperationalError as e:
        print(f"✗ Error querying permits: {e}")

    print("\nChecking notifications history...")
    try:
        cursor.execute("SELECT COUNT(*) as count FROM notifications")
        result = cursor.fetchone()
        print(f"Total notifications in history: {result['count']}")

        cursor.execute("""
            SELECT permit_id, date, division_id, division_name, notified_at
            FROM notifications
            ORDER BY notified_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        if recent:
            print("Recent notifications:")
            for notif in recent:
                print(f"  - Permit #{notif['permit_id']}, {notif['date']}, {notif['division_name']}")
        else:
            print("No notification history")

    except sqlite3.OperationalError as e:
        print(f"✗ Error querying notifications: {e}")

    conn.close()

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic complete")
print("=" * 60)
