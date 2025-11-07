#!/usr/bin/env python3
"""
Search for San Juan River permit on recreation.gov
"""
import requests
import json

print("=" * 80)
print("Searching for San Juan River Permits")
print("=" * 80)

search_terms = [
    "San Juan River",
    "San Juan River Permit",
    "San Juan",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

all_results = []

for term in search_terms:
    print(f"\nSearching for: '{term}'")

    url = "https://www.recreation.gov/api/search"
    params = {
        "q": term,
        "entity_type": "permit"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()

            if 'results' in data:
                print(f"  Found {len(data['results'])} results")

                for result in data['results']:
                    entity_id = result.get('entity_id')
                    name = result.get('name', 'Unknown')
                    city = result.get('city', '')
                    state = result.get('state', '')
                    parent = result.get('parent_name', '')

                    # Filter for river-related permits
                    combined = f"{name} {parent}".lower()
                    if 'river' in combined or 'juan' in combined:
                        result_info = {
                            'entity_id': entity_id,
                            'name': name,
                            'location': f"{city}, {state}" if city else state,
                            'parent': parent
                        }

                        if result_info not in all_results:
                            all_results.append(result_info)
                            print(f"  ✓ {name}")
                            print(f"    ID: {entity_id}")
                            print(f"    Location: {city}, {state}")
                            if parent:
                                print(f"    Parent: {parent}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Now test each found ID
print("\n" + "=" * 80)
print("Testing Found IDs")
print("=" * 80)

valid_facilities = []

for result in all_results:
    facility_id = result['entity_id']
    print(f"\nTesting: {result['name']} ({facility_id})")

    url = f"https://www.recreation.gov/api/permits/{facility_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'payload' in data:
                facility_name = data['payload'].get('facility_name', 'Unknown')
                divisions = data['payload'].get('divisions', {})

                print(f"  ✓ VALID")
                print(f"  Facility Name: {facility_name}")
                print(f"  Divisions: {len(divisions)}")

                for div_id, div_info in list(divisions.items())[:3]:
                    print(f"    - {div_id}: {div_info.get('name', 'Unknown')}")

                valid_facilities.append({
                    'id': facility_id,
                    'name': facility_name,
                    'divisions': len(divisions),
                    'location': result['location']
                })
        else:
            print(f"  ✗ INVALID (HTTP {response.status_code})")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("VALID SAN JUAN RIVER PERMITS")
print("=" * 80)

if valid_facilities:
    for facility in valid_facilities:
        print(f"\nID: {facility['id']}")
        print(f"Name: {facility['name']}")
        print(f"Location: {facility['location']}")
        print(f"Divisions: {facility['divisions']}")
else:
    print("\nNo valid San Juan River permits found!")
    print("The San Juan River permit may not be available through recreation.gov")
    print("or it may use a different name/system.")
