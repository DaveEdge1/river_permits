#!/usr/bin/env python3
"""
Script to discover and catalog river permit facilities from recreation.gov

This script searches for all river permit facilities and generates a
river_permits.json file that the app can use for dropdown selection.
"""
import requests
import json
import time
from typing import List, Dict

# Search terms for finding river permits
RIVER_SEARCH_TERMS = [
    "river permit",
    "river permits",
    "canyon permit",
    "Green River",
    "Colorado River",
    "San Juan River",
    "Yampa River",
    "Grand Canyon",
    "Desolation Canyon",
    "Gates of Lodore",
    "Cataract Canyon",
    "Westwater Canyon",
]

# Known permit facilities to ensure we include them
KNOWN_FACILITIES = [
    "233262",  # Grand Canyon River
    "234621",  # San Juan River
    "233393",  # Desolation Gray - Green River
    "250014",  # Dinosaur Green And Yampa River Permits (Gates of Lodore)
    "621748",  # Canyonlands Overnight River Permits
    "621747",  # Canyonlands Day Use River Permits
]

def search_permits(search_term: str) -> List[Dict]:
    """Search recreation.gov for permits matching the search term"""
    print(f"Searching for: {search_term}")

    url = "https://www.recreation.gov/api/search"
    params = {
        "q": search_term,
        "entity_type": "permit"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                print(f"  Found {len(data['results'])} result(s)")
                return data['results']
    except Exception as e:
        print(f"  Error: {e}")

    return []

def get_facility_details(facility_id: str) -> Dict:
    """Get detailed information about a facility"""
    url = f"https://www.recreation.gov/api/permits/{facility_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'payload' in data:
                payload = data['payload']
                return {
                    'facility_id': facility_id,
                    'facility_name': payload.get('facility_name', 'Unknown'),
                    'description': payload.get('description', ''),
                    'divisions': payload.get('divisions', {}),
                    'city': payload.get('city', ''),
                    'state': payload.get('state', ''),
                    'latitude': payload.get('latitude'),
                    'longitude': payload.get('longitude'),
                }
    except Exception as e:
        print(f"  Error getting facility {facility_id}: {e}")

    return None

def is_river_permit(facility_name: str, description: str) -> bool:
    """Determine if this is a river permit based on name and description"""
    combined = (facility_name + " " + description).lower()

    # Keywords that indicate river permits
    river_keywords = ['river', 'canyon', 'rafting', 'float', 'boating', 'watercraft']

    # Keywords that indicate NOT river permits
    exclude_keywords = ['campground', 'camping', 'group camp', 'picnic', 'day use area',
                        'recreation area', 'ranger station', 'boat ramp', 'christmas tree']

    # Check for exclusions first
    for keyword in exclude_keywords:
        if keyword in combined:
            return False

    # Check for river-related keywords
    for keyword in river_keywords:
        if keyword in combined:
            return True

    return False

def main():
    print("=" * 80)
    print("River Permit Facility Discovery Script")
    print("=" * 80)

    all_facilities = {}  # facility_id -> facility info

    # Search using various terms
    print("\n" + "=" * 80)
    print("PHASE 1: Searching recreation.gov")
    print("=" * 80)

    for search_term in RIVER_SEARCH_TERMS:
        results = search_permits(search_term)

        for result in results:
            facility_id = result.get('entity_id')
            if facility_id and facility_id not in all_facilities:
                name = result.get('name', 'Unknown')
                description = result.get('description', '')

                if is_river_permit(name, description):
                    all_facilities[facility_id] = {
                        'facility_id': facility_id,
                        'facility_name': name,
                        'city': result.get('city', ''),
                        'state': result.get('state', ''),
                        'parent_name': result.get('parent_name', ''),
                        'description': description[:200] + '...' if len(description) > 200 else description
                    }
                    print(f"  ✓ Added: {name} ({facility_id})")

        time.sleep(0.5)  # Be nice to the API

    # Add known facilities
    print("\n" + "=" * 80)
    print("PHASE 2: Adding known facilities")
    print("=" * 80)

    for facility_id in KNOWN_FACILITIES:
        if facility_id not in all_facilities:
            print(f"Getting details for facility {facility_id}...")
            details = get_facility_details(facility_id)
            if details:
                all_facilities[facility_id] = details
                print(f"  ✓ Added: {details['facility_name']} ({facility_id})")
            time.sleep(0.5)

    # Get full details for all facilities
    print("\n" + "=" * 80)
    print("PHASE 3: Getting detailed information")
    print("=" * 80)

    enriched_facilities = []

    for facility_id, basic_info in all_facilities.items():
        print(f"Getting full details for {basic_info['facility_name']}...")
        details = get_facility_details(facility_id)

        if details:
            # Merge with basic info
            facility_info = {
                'facility_id': facility_id,
                'facility_name': details['facility_name'],
                'description': details.get('description', basic_info.get('description', '')),
                'city': details.get('city', basic_info.get('city', '')),
                'state': details.get('state', basic_info.get('state', '')),
                'latitude': details.get('latitude'),
                'longitude': details.get('longitude'),
                'divisions': {}
            }

            # Add division information
            if details.get('divisions'):
                for div_id, div_info in details['divisions'].items():
                    facility_info['divisions'][div_id] = {
                        'id': div_id,
                        'name': div_info.get('name', f'Division {div_id}'),
                        'description': div_info.get('description', '')
                    }
                print(f"  ✓ {len(facility_info['divisions'])} division(s)")

            enriched_facilities.append(facility_info)

        time.sleep(0.5)

    # Sort by name
    enriched_facilities.sort(key=lambda x: x['facility_name'])

    # Save to JSON file
    output_file = 'river_permits.json'
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(enriched_facilities),
            'facilities': enriched_facilities
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Found {len(enriched_facilities)} river permit facilities")
    print(f"✓ Saved to {output_file}")

    print("\nFacilities discovered:")
    for facility in enriched_facilities:
        div_count = len(facility.get('divisions', {}))
        location = f"{facility['city']}, {facility['state']}" if facility['city'] else facility['state']
        print(f"  - {facility['facility_name']}")
        print(f"    ID: {facility['facility_id']} | Location: {location} | Divisions: {div_count}")

if __name__ == "__main__":
    main()
