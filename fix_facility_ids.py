#!/usr/bin/env python3
"""
Script to verify and fix facility IDs for all permit monitors
"""
import sqlite3
import requests
import json
import time
from typing import Dict, Optional, List

DB_PATH = '/home/user/river_permits/database/permits.db'

# Known correct facility IDs based on investigation
KNOWN_FACILITIES = {
    "Gates of Lodore": "250014",  # Dinosaur Green And Yampa River Permits
    "Yampa River": "250014",      # Same facility, different division
    "Deerlodge Park": "250014",   # Same facility, different division
    "San Juan River": "234621",   # San Juan River
    "Desolation Canyon": "233393", # Desolation Gray - Green River Permit
    "Grand Canyon": "233262",     # Grand Canyon River
}

def get_all_permits():
    """Get all permits from the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, u.email
        FROM permits p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.id
    """)

    permits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return permits

def test_facility_id(facility_id: str) -> Dict:
    """Test if a facility ID is valid and get its info"""
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
                    'valid': True,
                    'facility_name': payload.get('facility_name', 'Unknown'),
                    'divisions': payload.get('divisions', {}),
                    'data': payload
                }
        return {'valid': False, 'error': f"HTTP {response.status_code}"}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def search_facility_by_name(name: str) -> Optional[str]:
    """Search for a facility by name on recreation.gov"""
    url = "https://www.recreation.gov/api/search"
    params = {
        "q": name,
        "entity_type": "permit"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                # Return the first result's entity_id
                result = data['results'][0]
                return result.get('entity_id')
    except Exception as e:
        print(f"    Search error: {e}")

    return None

def update_facility_id(permit_id: int, new_facility_id: str):
    """Update a permit's facility ID in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE permits
        SET facility_id = ?
        WHERE id = ?
    """, (new_facility_id, permit_id))

    conn.commit()
    conn.close()

def main():
    print("=" * 70)
    print("Facility ID Verification and Fix Script")
    print("=" * 70)

    permits = get_all_permits()

    if not permits:
        print("\nNo permits found in database!")
        return

    print(f"\nFound {len(permits)} permit(s) to check\n")

    updates_needed = []

    for permit in permits:
        print(f"\n{'=' * 70}")
        print(f"Permit #{permit['id']}: {permit['name']}")
        print(f"User: {permit['email']}")
        print(f"Current Facility ID: {permit['facility_id']}")
        print('=' * 70)

        # Test current facility ID
        print("Testing current facility ID...")
        result = test_facility_id(permit['facility_id'])

        if result['valid']:
            print(f"✓ Facility ID is VALID")
            print(f"  Recreation.gov Name: {result['facility_name']}")
            if result['divisions']:
                print(f"  Divisions ({len(result['divisions'])}):")
                for div_id, div_info in list(result['divisions'].items())[:5]:
                    print(f"    - {div_id}: {div_info.get('name', 'Unknown')}")
        else:
            print(f"✗ Facility ID is INVALID")
            print(f"  Error: {result['error']}")

            # Try to find correct facility ID
            print(f"\n  Searching for correct facility ID...")

            # First check known facilities
            correct_id = None
            for known_name, known_id in KNOWN_FACILITIES.items():
                if known_name.lower() in permit['name'].lower():
                    correct_id = known_id
                    print(f"  Found in known facilities: {known_id}")
                    break

            # If not found in known facilities, search recreation.gov
            if not correct_id:
                print(f"  Searching recreation.gov for: {permit['name']}")
                correct_id = search_facility_by_name(permit['name'])
                if correct_id:
                    print(f"  Found via search: {correct_id}")
                    # Verify it's valid
                    verify = test_facility_id(correct_id)
                    if verify['valid']:
                        print(f"  Verified: {verify['facility_name']}")
                    else:
                        print(f"  Search result was invalid, ignoring")
                        correct_id = None

            if correct_id and correct_id != permit['facility_id']:
                updates_needed.append({
                    'permit_id': permit['id'],
                    'permit_name': permit['name'],
                    'old_id': permit['facility_id'],
                    'new_id': correct_id
                })
            else:
                print(f"  ✗ Could not find correct facility ID")

        time.sleep(0.5)  # Be nice to the API

    # Show summary of updates needed
    print("\n" + "=" * 70)
    print("UPDATE SUMMARY")
    print("=" * 70)

    if not updates_needed:
        print("\n✓ All facility IDs are valid! No updates needed.")
        return

    print(f"\nFound {len(updates_needed)} permit(s) that need updating:\n")
    for update in updates_needed:
        print(f"  Permit #{update['permit_id']}: {update['permit_name']}")
        print(f"    {update['old_id']} → {update['new_id']}")
        print()

    # Ask for confirmation
    response = input("\nApply these updates? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        print("\nApplying updates...")
        for update in updates_needed:
            print(f"  Updating permit #{update['permit_id']}...", end=' ')
            try:
                update_facility_id(update['permit_id'], update['new_id'])
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")

        print("\n✓ Updates complete!")
        print("\nRecommendation: Run the 'Check Permits Now' feature to verify the fixes.")
    else:
        print("\nNo updates applied.")

if __name__ == "__main__":
    main()
