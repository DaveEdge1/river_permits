#!/bin/bash
# Test if the check-permits endpoint exists

echo "Testing /api/admin/check-permits endpoint..."
echo ""

# Get a session cookie by logging in first
echo "Note: This test requires admin credentials"
echo "Run manually with: curl -X POST http://localhost:3000/api/admin/check-permits -H 'Cookie: your-session-cookie'"
echo ""

# Check if server is responding
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health | grep -q "200"; then
    echo "✓ Server is running on port 3000"
else
    echo "✗ Server is not responding on port 3000"
    exit 1
fi

echo ""
echo "To test the endpoint:"
echo "1. Open browser DevTools (F12)"
echo "2. Go to Application/Storage → Cookies"
echo "3. Copy the 'connect.sid' cookie value"
echo "4. Run: curl -X POST http://localhost:3000/api/admin/check-permits -H 'Cookie: connect.sid=YOUR_COOKIE_VALUE'"
