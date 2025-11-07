#!/usr/bin/env python3
"""
Search for Gates of Lodore facility ID on recreation.gov
"""
import requests
import json

def search_facility():
    """Search for Gates of Lodore on recreation.gov"""

    print("=" * 70)
    print("Searching for Gates of Lodore Facility")
    print("=" * 70)

    # Try the search/suggest API
    search_terms = [
        "Gates of Lodore",
        "Lodore",
        "Green River Utah",
        "Green River Permits"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for term in search_terms:
        print(f"\n{'=' * 70}")
        print(f"Searching for: {term}")
        print('=' * 70)

        # Try permits search endpoint
        url = "https://www.recreation.gov/api/search"
        params = {
            "q": term,
            "entity_type": "permit"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Save response
                filename = f"search_{term.replace(' ', '_').lower()}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Response saved to: {filename}")

                # Parse results
                if 'results' in data:
                    results = data['results']
                    print(f"\nFound {len(results)} result(s):")

                    for i, result in enumerate(results):
                        print(f"\n  Result {i+1}:")
                        if 'entity_id' in result:
                            print(f"    Entity ID: {result['entity_id']}")
                        if 'name' in result:
                            print(f"    Name: {result['name']}")
                        if 'city' in result:
                            print(f"    City: {result['city']}")
                        if 'state' in result:
                            print(f"    State: {result['state']}")
                        if 'parent_name' in result:
                            print(f"    Parent: {result['parent_name']}")
                        if 'description' in result:
                            desc = result['description'][:100]
                            print(f"    Description: {desc}...")

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    # Also try some known Green River facility IDs
    print(f"\n{'=' * 70}")
    print("Testing known Green River facility IDs:")
    print('=' * 70)

    known_ids = {
        "234652": "Gates of Lodore (guessed)",
        "233262": "Grand Canyon River",
        "234621": "San Juan River",
        "4675312": "Another possibility",
        "4675313": "Another possibility"
    }

    for facility_id, name in known_ids.items():
        url = f"https://www.recreation.gov/api/permits/{facility_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'payload' in data and 'facility_name' in data['payload']:
                    actual_name = data['payload']['facility_name']
                    print(f"  {facility_id}: {actual_name}")

                    if 'lodore' in actual_name.lower():
                        print(f"    *** FOUND IT! ***")
                        # Save full details
                        with open(f"facility_{facility_id}_details.json", 'w') as f:
                            json.dump(data, f, indent=2)
        except:
            pass

if __name__ == "__main__":
    search_facility()
