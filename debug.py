#!/usr/bin/env python3
"""
Debug script to diagnose configuration issues
"""
import os
import json
import sys

print("=" * 60)
print("RIVER PERMIT FINDER - DEBUG SCRIPT")
print("=" * 60)

# Check if files exist
print("\n1. Checking required files...")
files_to_check = {
    'config.json': 'Configuration file',
    '.env': 'Environment variables',
    'permit_finder.py': 'Permit finder module',
    'main.py': 'Main application'
}

for filename, description in files_to_check.items():
    exists = os.path.exists(filename)
    status = "✓ FOUND" if exists else "✗ MISSING"
    print(f"   {status}: {filename} ({description})")

print("\n2. Checking config.json contents...")
try:
    with open('config.json', 'r') as f:
        config = json.load(f)

    print(f"   ✓ config.json is valid JSON")

    # Check permits
    permits = config.get('permits', [])
    print(f"   Total permits in config: {len(permits)}")

    enabled_count = 0
    for i, permit in enumerate(permits):
        enabled = permit.get('enabled', True)
        name = permit.get('name', 'Unknown')
        facility_id = permit.get('facility_id', 'Missing')

        print(f"\n   Permit {i+1}: {name}")
        print(f"      Facility ID: {facility_id}")
        print(f"      Enabled: {enabled}")
        print(f"      Start Date: {permit.get('start_date', 'Missing')}")
        print(f"      End Date: {permit.get('end_date', 'Missing')}")

        if enabled:
            enabled_count += 1

    print(f"\n   Total ENABLED permits: {enabled_count}")

    if enabled_count == 0:
        print("   ⚠ WARNING: No permits are enabled!")
        print("   Check that 'enabled': true in your config.json")

except FileNotFoundError:
    print("   ✗ config.json NOT FOUND")
    print("   → Run: cp config.example.json config.json")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"   ✗ config.json has INVALID JSON: {e}")
    sys.exit(1)

print("\n3. Checking .env file...")
try:
    with open('.env', 'r') as f:
        env_lines = f.readlines()

    print(f"   ✓ .env file exists ({len(env_lines)} lines)")

    # Check for key variables
    env_vars = {}
    for line in env_lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()

    required_vars = ['EMAIL_FROM', 'EMAIL_TO', 'EMAIL_PASSWORD']
    for var in required_vars:
        if var in env_vars:
            # Mask the value for security
            value = env_vars[var]
            if value and value != f'your_{var.lower()}_here':
                masked = value[:3] + '***' if len(value) > 3 else '***'
                print(f"   ✓ {var}: {masked}")
            else:
                print(f"   ⚠ {var}: Not configured (still has placeholder)")
        else:
            print(f"   ✗ {var}: Missing")

except FileNotFoundError:
    print("   ⚠ .env file NOT FOUND")
    print("   → Run: cp .env.example .env")
    print("   → Then edit .env with your credentials")

print("\n4. Testing permit_finder module...")
try:
    from permit_finder import PermitFinder
    finder = PermitFinder()
    print("   ✓ permit_finder module loads successfully")

    # Test with San Juan River
    if enabled_count > 0:
        test_permit = permits[0]
        facility_id = test_permit.get('facility_id')
        print(f"\n   Testing facility {facility_id}...")

        available = finder.check_permit_availability(
            facility_id=facility_id,
            start_date='2025-04-01',
            end_date='2025-04-30'
        )
        print(f"   Found {len(available)} permits in April 2025")
        if available:
            for permit in available[:3]:
                print(f"      - {permit['date']}: {permit['details'].get('remaining', '?')} remaining")

except ImportError as e:
    print(f"   ✗ Failed to import permit_finder: {e}")
except Exception as e:
    print(f"   ✗ Error testing permit finder: {e}")

print("\n5. Summary...")
if enabled_count > 0:
    print(f"   ✓ You have {enabled_count} enabled permit(s)")
    print("   → main.py should work correctly")
else:
    print("   ✗ No enabled permits found")
    print("   → This is why you see 'Checking 0 permit(s)'")
    print("   → Edit config.json and set 'enabled': true")

print("\n" + "=" * 60)
print("If you still have issues, share this output for help!")
print("=" * 60)
