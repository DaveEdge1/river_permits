#!/usr/bin/env python3
import requests
import json
from datetime import datetime

facility_id = "250986"
print(f"Testing San Juan River - Facility ID: {facility_id}\n")

# Check next 3 months
for month_offset in range(3):
    check_date = datetime.now().replace(day=1)
    if month_offset > 0:
        month = check_date.month + month_offset
        year = check_date.year
        while month > 12:
            month -= 12
            year += 1
        check_date = check_date.replace(month=month, year=year)
    
    month_str = check_date.strftime("%Y-%m-01T00:00:00.000Z")
    
    url = f"https://www.recreation.gov/api/permits/{facility_id}/availability/month"
    params = {"start_date": month_str}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if 'payload' in data and 'availability' in data['payload']:
                availability = data['payload']['availability']
                
                available_count = 0
                sample_dates = []
                
                for division_id, division_info in availability.items():
                    if isinstance(division_info, dict):
                        date_avail = division_info.get('date_availability', {})
                        for date_str, permit_info in date_avail.items():
                            if isinstance(permit_info, dict):
                                remaining = permit_info.get('remaining', 0)
                                if remaining > 0:
                                    available_count += 1
                                    if len(sample_dates) < 5:
                                        sample_dates.append(f"{date_str[:10]}: {remaining} remaining")
                
                print(f"{check_date.strftime('%B %Y')}: {available_count} dates available")
                if sample_dates:
                    for date_info in sample_dates:
                        print(f"  - {date_info}")
                    if available_count > 5:
                        print(f"  ... and {available_count - 5} more")
            else:
                print(f"{check_date.strftime('%B %Y')}: No availability data")
        else:
            print(f"{check_date.strftime('%B %Y')}: HTTP {response.status_code}")
    except Exception as e:
        print(f"{check_date.strftime('%B %Y')}: Error - {e}")

print("\nIf no availability shows, the San Juan River may not have permits available")
print("for the current time period (check recreation.gov directly to confirm).")
