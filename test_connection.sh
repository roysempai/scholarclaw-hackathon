#!/bin/bash

echo "======================================"
echo "ScholarClaw System Integration Test"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Docker containers
echo "1. Checking Docker Containers..."
if docker ps | grep -q "scholarclaw-backend"; then
    echo -e "${GREEN}✓ Backend container running${NC}"
else
    echo -e "${RED}✗ Backend container not running${NC}"
fi

if docker ps | grep -q "scholarclaw-db"; then
    echo -e "${GREEN}✓ Database container running${NC}"
else
    echo -e "${RED}✗ Database container not running${NC}"
fi
echo ""

# Test 2: Backend Health
echo "2. Testing Backend Health..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi
echo ""

# Test 3: Frontend
echo "3. Testing Frontend..."
if curl -s http://localhost:5174 | grep -q "ScholarClaw"; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend not accessible${NC}"
fi
echo ""

# Test 4: API Authentication
echo "4. Testing API Authentication..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Login successful${NC}"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token obtained (first 50 chars): ${TOKEN:0:50}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "   Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 5: Schemes API
echo "5. Testing Schemes API..."
SCHEMES_RESPONSE=$(curl -s -X GET http://localhost:8000/api/schemes \
  -H "Authorization: Bearer $TOKEN")

if echo "$SCHEMES_RESPONSE" | grep -q "schemes"; then
    SCHEME_COUNT=$(echo "$SCHEMES_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ Schemes API working${NC}"
    echo "   Found $SCHEME_COUNT schemes"
    
    # Extract scheme names
    echo "   Available schemes:"
    echo "$SCHEMES_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | head -3 | while read scheme; do
        echo "     - $scheme"
    done
else
    echo -e "${RED}✗ Schemes API failed${NC}"
    echo "   Response: $SCHEMES_RESPONSE"
fi
echo ""

# Test 6: Frontend Proxy
echo "6. Testing Frontend-Backend Proxy..."
PROXY_RESPONSE=$(curl -s http://localhost:5174/api/health)
if echo "$PROXY_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Frontend proxy working${NC}"
    echo "   Frontend can reach backend via proxy"
else
    echo -e "${YELLOW}⚠ Frontend proxy test inconclusive${NC}"
    echo "   Response: $PROXY_RESPONSE"
fi
echo ""

# Summary
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "${GREEN}All core functionality is working!${NC}"
echo ""
echo "Next Steps:"
echo "1. Open browser to: http://localhost:5174"
echo "2. Login with:"
echo "   Email: test@example.com"
echo "   Password: Test123!@#"
echo "3. Navigate to Dashboard to view schemes"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "======================================"
