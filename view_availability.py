#!/usr/bin/env python3
"""
View current availability for all enabled permits
Does NOT check notification history - shows ALL available permits
"""
import sqlite3
import sys
import os
from datetime import datetime
from collections import defaultdict

# Add parent directory to path to import permit_finder
sys.path.insert(0, os.path.dirname(__file__))

from permit_finder import PermitFinder

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

def main():
    print("=" * 60)
    print(f"Current Permit Availability - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initialize permit finder
    finder = PermitFinder()

    # Get all enabled permits
    permits = get_all_enabled_permits()

    if not permits:
        print("No enabled permits to check")
        return

    print(f"Checking {len(permits)} permit(s)")

    total_available = 0
    permits_with_availability = 0

    # Check each permit
    for permit in permits:
        print(f"\n{'=' * 60}")
        print(f"Permit: {permit['name']}")
        print(f"User: {permit['email']}")
        print(f"Facility ID: {permit['facility_id']}")
        print(f"Date Range: {permit['start_date']} to {permit['end_date']}")
        print(f"Party Size: {permit['min_people']}-{permit['max_people']} people")
        print('=' * 60)

        try:
            available = finder.check_permit_availability(
                facility_id=str(permit['facility_id']),
                start_date=permit['start_date'],
                end_date=permit['end_date'],
                min_people=permit['min_people'],
                max_people=permit['max_people']
            )

            if available:
                permits_with_availability += 1
                total_available += len(available)

                print(f"✓ Found {len(available)} available date(s):")

                # Group by date for cleaner output
                dates_by_division = defaultdict(list)
                for avail in available:
                    dates_by_division[avail.get('division_name', 'Unknown Division')].append(avail['date'])

                for division, dates in dates_by_division.items():
                    print(f"\n  {division}:")
                    # Show first 10 dates per division
                    for date in sorted(dates)[:10]:
                        print(f"    - {date}")
                    if len(dates) > 10:
                        print(f"    ... and {len(dates) - 10} more dates")
            else:
                print("✗ No available permits found")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total permits checked: {len(permits)}")
    print(f"Permits with availability: {permits_with_availability}")
    print(f"Total available dates: {total_available}")
    print("=" * 60)

if __name__ == "__main__":
    main()
