#!/usr/bin/env python3
"""
Debug script to check the CORRECT Gates of Lodore facility (250014)
for November 26, 2025
"""
import requests
import json
from datetime import datetime

def check_lodore_correct():
    """Check recreation.gov API for Gates of Lodore (facility 250014) on November 26, 2025"""

    # CORRECT facility ID for Dinosaur Green and Yampa River Permits
    facility_id = "250014"

    print("=" * 70)
    print(f"Checking Facility {facility_id}: Dinosaur Green And Yampa River Permits")
    print("Target Date: November 26, 2025")
    print("=" * 70)

    # First, get facility info
    url = f"https://www.recreation.gov/api/permits/{facility_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'payload' in data:
                print(f"\nFacility Name: {data['payload'].get('facility_name', 'Unknown')}")

                # Show divisions
                if 'divisions' in data['payload']:
                    divisions = data['payload']['divisions']
                    print(f"\nDivisions ({len(divisions)}):")
                    for div_id, div_info in divisions.items():
                        print(f"  {div_id}: {div_info.get('name', 'Unknown')}")

            # Save facility info
            with open(f"facility_{facility_id}_info.json", 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nFull facility info saved to: facility_{facility_id}_info.json")
    except Exception as e:
        print(f"Error getting facility info: {e}")

    # Check November 2025 availability
    print("\n" + "=" * 70)
    print("Checking November 2025 Availability")
    print("=" * 70)

    month_str = "2025-11-01T00:00:00.000Z"
    target_date = "2025-11-26"

    url = f"https://www.recreation.gov/api/permits/{facility_id}/availability/month"
    params = {"start_date": month_str}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Save full response
            filename = f"facility_{facility_id}_nov2025.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Full response saved to: {filename}")

            if 'payload' in data:
                payload = data['payload']

                # Check next available date
                if 'next_available_date' in payload:
                    print(f"\nNext Available Date: {payload['next_available_date']}")

                # Check availability section
                if 'availability' in payload:
                    availability = payload['availability']
                    print(f"\nFound {len(availability)} division(s) in availability")

                    # Look for Nov 26 in all divisions
                    found_nov_26 = False

                    for division_id, division_info in availability.items():
                        if not isinstance(division_info, dict):
                            continue

                        # Check if this division has date_availability
                        date_availability = division_info.get('date_availability', {})

                        # Look specifically for Nov 26
                        for date_str, permit_info in date_availability.items():
                            if target_date in date_str:
                                found_nov_26 = True
                                print(f"\n*** FOUND {target_date} in Division {division_id} ***")
                                print(f"Date string: {date_str}")
                                print(f"Permit info:")
                                print(json.dumps(permit_info, indent=2))

                                # Analyze availability
                                if isinstance(permit_info, dict):
                                    if 'remaining' in permit_info:
                                        remaining = permit_info['remaining']
                                        print(f"\n  Remaining: {remaining}")
                                        if isinstance(remaining, (int, float)) and remaining > 0:
                                            print(f"  ✓ THIS SHOULD BE AVAILABLE (remaining > 0)")
                                        else:
                                            print(f"  ✗ NOT AVAILABLE (remaining = {remaining})")

                                    if 'status' in permit_info:
                                        print(f"  Status: {permit_info['status']}")

                                    if 'is_available' in permit_info:
                                        print(f"  Is Available: {permit_info['is_available']}")

                                print()

                    if not found_nov_26:
                        print(f"\n{target_date} NOT found in any division")

                        # Show sample dates from each division
                        print("\nSample dates per division:")
                        for division_id, division_info in availability.items():
                            if isinstance(division_info, dict):
                                date_availability = division_info.get('date_availability', {})
                                dates = list(date_availability.keys())
                                if dates:
                                    print(f"  Division {division_id}: {len(dates)} dates")
                                    print(f"    First 3: {dates[:3]}")
                                    print(f"    Last 3: {dates[-3:]}")
                                else:
                                    print(f"  Division {division_id}: NO DATES")

        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text[:500])

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_lodore_correct()
