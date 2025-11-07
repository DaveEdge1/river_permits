#!/usr/bin/env python3
"""
Debug script to check Gates of Lodore API response for November 26, 2025
"""
import requests
import json
from datetime import datetime

def check_lodore_nov26():
    """Check recreation.gov API for Gates of Lodore on November 26, 2025"""

    # Gates of Lodore facility ID - need to verify this
    # Common Green River facility IDs:
    # 234653 - Desolation Canyon
    # 234652 - Gates of Lodore
    facility_ids = [
        "234652",  # Most likely Gates of Lodore
        "234653",  # Desolation Canyon (to compare)
    ]

    print("=" * 70)
    print("Gates of Lodore API Debug - November 26, 2025")
    print("=" * 70)

    # Check November 2025
    month_str = "2025-11-01T00:00:00.000Z"
    target_date = "2025-11-26"

    for facility_id in facility_ids:
        print(f"\n{'=' * 70}")
        print(f"Checking Facility ID: {facility_id}")
        print('=' * 70)

        url = f"https://www.recreation.gov/api/permits/{facility_id}/availability/month"
        params = {"start_date": month_str}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Save full response to file for inspection
                filename = f"debug_facility_{facility_id}_response.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Full response saved to: {filename}")

                # Get facility info from payload
                if 'payload' in data:
                    payload = data['payload']

                    # Print facility name if available
                    if 'facility_name' in payload:
                        print(f"Facility Name: {payload['facility_name']}")

                    # Check availability section
                    if 'availability' in payload:
                        availability = payload['availability']
                        print(f"\nFound {len(availability)} division(s)")

                        # Iterate through divisions
                        for division_id, division_info in availability.items():
                            if not isinstance(division_info, dict):
                                continue

                            print(f"\n  Division ID: {division_id}")

                            # Check if this division has date_availability
                            date_availability = None
                            if 'date_availability' in division_info:
                                date_availability = division_info['date_availability']
                                print(f"    Using 'date_availability' structure")
                            else:
                                # Direct date mapping
                                date_availability = {division_id: division_info}
                                print(f"    Using direct structure")

                            # Look specifically for Nov 26
                            found_nov_26 = False
                            for date_str, permit_info in date_availability.items():
                                if target_date in date_str:
                                    found_nov_26 = True
                                    print(f"\n    *** FOUND {target_date} ***")
                                    print(f"    Date string: {date_str}")
                                    print(f"    Permit info: {json.dumps(permit_info, indent=6)}")

                                    # Check availability status
                                    if isinstance(permit_info, dict):
                                        if 'remaining' in permit_info:
                                            print(f"    Remaining: {permit_info['remaining']}")
                                        if 'status' in permit_info:
                                            print(f"    Status: {permit_info['status']}")
                                        if 'is_available' in permit_info:
                                            print(f"    Is Available: {permit_info['is_available']}")

                            if not found_nov_26:
                                print(f"    {target_date} NOT found in this division")
                                # Show what dates ARE available
                                dates_in_division = list(date_availability.keys())[:5]
                                print(f"    Sample dates in division: {dates_in_division}")
                    else:
                        print("No 'availability' section in payload")
                else:
                    print("No 'payload' in response")
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
    check_lodore_nov26()
