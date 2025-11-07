#!/usr/bin/env python3
"""
Test San Juan River facility ID 234621 for current availability
"""
import requests
import json
from datetime import datetime, timedelta

facility_id = "234621"

print("=" * 80)
print(f"Testing San Juan River - Facility ID: {facility_id}")
print("=" * 80)

# Get facility info
print("\n1. Getting facility information...")
url = f"https://www.recreation.gov/api/permits/{facility_id}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if 'payload' in data:
            facility_name = data['payload'].get('facility_name', 'Unknown')
            print(f"Facility Name: {facility_name}")

            divisions = data['payload'].get('divisions', {})
            print(f"Divisions: {len(divisions)}")
            for div_id, div_info in divisions.items():
                print(f"  - {div_id}: {div_info.get('name', 'Unknown')}")

        # Save full response
        with open('san_juan_facility_info.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("Saved full facility info to san_juan_facility_info.json")
    else:
        print(f"ERROR: HTTP {response.status_code}")
        print(response.text[:500])
except Exception as e:
    print(f"ERROR: {e}")

# Check availability for next 6 months
print("\n2. Checking availability for next 6 months...")

# Start from current month
current_date = datetime.now()
months_to_check = 6

for i in range(months_to_check):
    check_date = current_date + timedelta(days=30*i)
    month_str = check_date.strftime("%Y-%m-01T00:00:00.000Z")

    print(f"\n  Checking {check_date.strftime('%B %Y')}...")

    url = f"https://www.recreation.gov/api/permits/{facility_id}/availability/month"
    params = {"start_date": month_str}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Save first month's data for inspection
            if i == 0:
                with open('san_juan_availability.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"    Saved availability data to san_juan_availability.json")

            if 'payload' in data and 'availability' in data['payload']:
                availability = data['payload']['availability']

                # Count available dates
                available_count = 0
                available_dates = []

                for division_id, division_info in availability.items():
                    if not isinstance(division_info, dict):
                        continue

                    date_availability = division_info.get('date_availability', {})

                    for date_str, permit_info in date_availability.items():
                        if isinstance(permit_info, dict):
                            remaining = permit_info.get('remaining', 0)
                            if isinstance(remaining, (int, float)) and remaining > 0:
                                available_count += 1
                                # Only show first 5
                                if len(available_dates) < 5:
                                    available_dates.append(f"{date_str[:10]} ({remaining} remaining)")

                if available_count > 0:
                    print(f"    ✓ Found {available_count} available date(s)")
                    for date_info in available_dates:
                        print(f"      - {date_info}")
                    if available_count > 5:
                        print(f"      ... and {available_count - 5} more")
                else:
                    print(f"    No availability")
            else:
                print(f"    No availability data in response")
        else:
            print(f"    ERROR: HTTP {response.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nIf you see available dates above but your permit monitor isn't finding them,")
print("check:")
print("  1. Your date range in the permit monitor")
print("  2. Your party size (min_people and max_people)")
print("  3. The permit_finder.py filtering logic")
