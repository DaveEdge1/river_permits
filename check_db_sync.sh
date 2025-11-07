#!/bin/bash
echo "Checking if web app database has data..."
curl -s http://localhost:3000/api/admin/permits 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    permits = data.get('permits', [])
    print(f'Web app database has {len(permits)} permit(s)')
    for p in permits:
        print(f'  - {p[\"name\"]} (ID: {p[\"id\"]}, Facility: {p[\"facility_id\"]})')
except:
    print('Could not read from web app API')
"

echo ""
echo "Checking if Python can read database file..."
python3 << 'PYEOF'
import sqlite3
try:
    conn = sqlite3.connect('/home/user/river_permits/database/permits.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM permits")
    count = cursor.fetchone()[0]
    print(f"Python SQLite sees {count} permit(s)")
    cursor.execute("SELECT id, name, facility_id FROM permits")
    for row in cursor.fetchall():
        print(f"  - {row[1]} (ID: {row[0]}, Facility: {row[2]})")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
PYEOF
