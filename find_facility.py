#!/usr/bin/env python3
"""
Utility script to help find recreation.gov facility IDs and information
"""
import sys
import requests
from permit_finder import PermitFinder


def search_facilities(search_term: str):
    """
    Search for facilities matching a term

    Args:
        search_term: Search term (river name, location, etc.)
    """
    print(f"Searching for: {search_term}")
    print("-" * 60)

    try:
        # Use recreation.gov search API
        url = "https://www.recreation.gov/api/search"
        params = {
            'q': search_term,
            'fq': 'entity_type:permit'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get('results', [])

        if not results:
            print("No results found.")
            print("\nTry:")
            print("  - Using different search terms")
            print("  - Searching on recreation.gov website and extracting facility ID from URL")
            return

        print(f"Found {len(results)} result(s):\n")

        for idx, result in enumerate(results, 1):
            entity_id = result.get('entity_id')
            name = result.get('name')
            parent_name = result.get('parent_name', '')

            print(f"{idx}. {name}")
            if parent_name:
                print(f"   Location: {parent_name}")
            print(f"   Facility ID: {entity_id}")
            print(f"   URL: https://www.recreation.gov/permits/{entity_id}")
            print()

    except Exception as e:
        print(f"Error searching: {e}")
        print("\nAlternatively, you can:")
        print("1. Go to https://www.recreation.gov")
        print("2. Search for your desired river permit")
        print("3. Look at the URL: the number after /permits/ is your facility ID")


def get_facility_info(facility_id: str):
    """
    Get detailed information about a facility

    Args:
        facility_id: Recreation.gov facility ID
    """
    print(f"Fetching information for facility ID: {facility_id}")
    print("-" * 60)

    finder = PermitFinder()
    info = finder.get_facility_info(facility_id)

    if not info:
        print("Could not retrieve facility information.")
        print(f"Verify the facility ID at: https://www.recreation.gov/permits/{facility_id}")
        return

    print(f"Name: {info.get('facility_name', 'Unknown')}")
    print(f"ID: {facility_id}")

    if 'description' in info:
        print(f"\nDescription:")
        print(info['description'][:500] + "..." if len(info['description']) > 500 else info['description'])

    print(f"\nURL: https://www.recreation.gov/permits/{facility_id}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("River Permit Facility Finder")
        print("=" * 60)
        print("\nUsage:")
        print("  Search for permits:")
        print("    python find_facility.py search <river name>")
        print("    Example: python find_facility.py search \"Grand Canyon\"")
        print()
        print("  Get facility details:")
        print("    python find_facility.py info <facility_id>")
        print("    Example: python find_facility.py info 233262")
        print()
        print("  Common river permit facility IDs:")
        print("    Grand Canyon - Colorado River: 233262")
        print("    Middle Fork Salmon River: 234068")
        print("    Rogue River Wild Section: 251982")
        print("    Selway River: 233395")
        print("    Main Salmon River: 10086745")
        print()
        return 1

    command = sys.argv[1].lower()

    if command == 'search':
        if len(sys.argv) < 3:
            print("Error: Please provide a search term")
            print("Example: python find_facility.py search \"Grand Canyon\"")
            return 1
        search_term = ' '.join(sys.argv[2:])
        search_facilities(search_term)

    elif command == 'info':
        if len(sys.argv) < 3:
            print("Error: Please provide a facility ID")
            print("Example: python find_facility.py info 233262")
            return 1
        facility_id = sys.argv[2]
        get_facility_info(facility_id)

    else:
        print(f"Unknown command: {command}")
        print("Use 'search' or 'info'")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
