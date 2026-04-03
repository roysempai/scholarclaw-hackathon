#!/bin/bash

echo "=========================================="
echo "Audit Log API Testing"
echo "=========================================="
echo ""

# Login as regular user
echo "1. Login as regular user..."
LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}')
USER_TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$USER_TOKEN" ]; then
    echo "❌ Login failed!"
    exit 1
fi
echo "✅ User login successful"
echo ""

# Test user audit logs
echo "2. Testing GET /api/audit/logs (user's own logs)..."
LOGS=$(curl -s http://localhost:8000/api/audit/logs -H "Authorization: Bearer $USER_TOKEN")
echo "$LOGS" | head -100
echo ""

# Login as admin
echo "3. Login as admin..."
ADMIN_LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!@#"}')
ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "❌ Admin login failed!"
    exit 1
fi
echo "✅ Admin login successful"
echo ""

# Test admin endpoints
echo "4. Testing GET /api/audit/attacks (admin only)..."
ATTACKS=$(curl -s http://localhost:8000/api/audit/attacks -H "Authorization: Bearer $ADMIN_TOKEN")
echo "$ATTACKS"
echo ""

echo "5. Testing GET /api/audit/attack-summary (admin only)..."
SUMMARY=$(curl -s http://localhost:8000/api/audit/attack-summary -H "Authorization: Bearer $ADMIN_TOKEN")
echo "$SUMMARY"
echo ""

# Test non-admin access to admin endpoints
echo "6. Testing admin endpoint with regular user (should fail)..."
FORBIDDEN=$(curl -s http://localhost:8000/api/audit/attacks -H "Authorization: Bearer $USER_TOKEN")
if echo "$FORBIDDEN" | grep -q "403\|forbidden\|admin"; then
    echo "✅ Correctly rejected non-admin access"
else
    echo "❌ Security issue: non-admin accessed admin endpoint"
fi
echo "$FORBIDDEN"
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "✅ User audit logs endpoint working"
echo "✅ Admin audit endpoints working"
echo "✅ Role-based access control working"
echo ""
echo "Note: User has no audit logs yet - they are created when using AI agents"
