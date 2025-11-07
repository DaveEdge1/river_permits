#!/usr/bin/env python3
"""
Debug script to check Gates of Lodore permit configuration and test API
"""
import sqlite3
import requests
import json
from datetime import datetime

DB_PATH = '/home/user/river_permits/database/permits.db'

def get_lodore_permit():
    """Get Gates of Lodore permit from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, u.email
        FROM permits p
        JOIN users u ON p.user_id = u.id
        WHERE LOWER(p.name) LIKE '%lodore%' OR LOWER(p.name) LIKE '%gates%'
    """)

    permits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return permits

def test_api(facility_id, start_date, end_date):
    """Test recreation.gov API with exact permit parameters"""
    print(f"\nTesting API with:")
    print(f"  Facility ID: {facility_id}")
    print(f"  Start Date: {start_date}")
    print(f"  End Date: {end_date}")

    # Check November 2025
    month_str = "2025-11-01T00:00:00.000Z"
    url = f"https://www.recreation.gov/api/permits/{facility_id}/availability/month"
    params = {"start_date": month_str}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"\nAPI Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Save response
            filename = f"debug_permit_{facility_id}_nov2025.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Full response saved to: {filename}")

            if 'payload' in data and 'availability' in data['payload']:
                availability = data['payload']['availability']
                print(f"\nFound {len(availability)} division(s)")

                # Look for any availability in November
                found_dates = []
                for division_id, division_info in availability.items():
                    if isinstance(division_info, dict):
                        date_availability = division_info.get('date_availability', {})
                        for date_str, permit_info in date_availability.items():
                            if '2025-11' in date_str:
                                # Check if available
                                if isinstance(permit_info, dict):
                                    remaining = permit_info.get('remaining', 0)
                                    if isinstance(remaining, (int, float)) and remaining > 0:
                                        found_dates.append({
                                            'date': date_str,
                                            'division': division_id,
                                            'remaining': remaining
                                        })

                if found_dates:
                    print(f"\n✓ Found {len(found_dates)} available date(s) in November:")
                    for item in found_dates[:10]:
                        print(f"  - {item['date']}: Division {item['division']}, {item['remaining']} remaining")
                else:
                    print("\n✗ No availability found in November 2025")
            else:
                print("\n✗ No availability data in response")
        else:
            print(f"✗ API Error: HTTP {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"✗ Request failed: {e}")

def main():
    print("=" * 70)
    print("Gates of Lodore Permit Debug")
    print("=" * 70)

    permits = get_lodore_permit()

    if not permits:
        print("\n✗ No Gates of Lodore permit found in database!")
        print("\nSearching for all permits:")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, facility_id FROM permits")
        all_permits = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for p in all_permits:
            print(f"  - {p['name']} (facility_id: {p['facility_id']})")
        return

    for permit in permits:
        print(f"\n{'=' * 70}")
        print(f"Permit: {permit['name']}")
        print(f"User: {permit['email']}")
        print(f"Facility ID: {permit['facility_id']}")
        print(f"Date Range: {permit['start_date']} to {permit['end_date']}")
        print(f"Party Size: {permit['min_people']} - {permit['max_people']} people")
        print(f"Enabled: {permit['enabled'] == 1}")
        print('=' * 70)

        # Check if November 26, 2025 is in range
        start = datetime.strptime(permit['start_date'], "%Y-%m-%d")
        end = datetime.strptime(permit['end_date'], "%Y-%m-%d")
        nov_26 = datetime(2025, 11, 26)

        if start <= nov_26 <= end:
            print(f"\n✓ November 26, 2025 IS in date range")
        else:
            print(f"\n✗ November 26, 2025 is NOT in date range!")
            print(f"  Your range: {start.date()} to {end.date()}")
            print(f"  Nov 26 is: {nov_26.date()}")

        # Test API
        test_api(permit['facility_id'], permit['start_date'], permit['end_date'])

if __name__ == "__main__":
    main()
