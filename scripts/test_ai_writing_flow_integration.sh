#!/bin/bash

# AI Writing Flow Integration Smoke Test
# Task 1.6.5: Smoke test for GET /health and POST /generate

set -e

echo "========================================="
echo "AI Writing Flow Integration Smoke Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service URLs
AI_WRITING_FLOW_URL="${AI_WRITING_FLOW_URL:-http://localhost:8003}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://localhost:8042}"
EDITORIAL_URL="${EDITORIAL_URL:-http://localhost:8040}"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" "$url" 2>/dev/null || echo "000")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (Status: $status_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} (Expected: $expected_status, Got: $status_code)"
        echo "Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "1. Testing Editorial Service Health"
echo "------------------------------------"
test_endpoint "Editorial /health" "$EDITORIAL_URL/health" "GET" "" "200"
echo ""

echo "2. Testing AI Writing Flow Service"
echo "-----------------------------------"
test_endpoint "AI Writing Flow /health" "$AI_WRITING_FLOW_URL/health" "GET" "" "200"

# Test /generate endpoint
generate_payload='{
    "topic_title": "AI Integration Test",
    "topic_description": "Testing AI Writing Flow integration with orchestrator",
    "platform": "linkedin",
    "viral_score": 8.5
}'
test_endpoint "AI Writing Flow /generate" "$AI_WRITING_FLOW_URL/generate" "POST" "$generate_payload" "200"

# Test /process endpoint (selective path)
process_payload='{
    "content": "This is test content for processing",
    "platform": "linkedin",
    "validation_mode": "selective"
}'
test_endpoint "AI Writing Flow /process" "$AI_WRITING_FLOW_URL/process" "POST" "$process_payload" "200"
echo ""

echo "3. Testing Orchestrator Integration"
echo "------------------------------------"
test_endpoint "Orchestrator /health" "$ORCHESTRATOR_URL/health" "GET" "" "200"
test_endpoint "AI Writing Flow health via Orchestrator" "$ORCHESTRATOR_URL/health/ai-writing-flow" "GET" "" "200"
echo ""

echo "4. Testing /publish with direct_content=false"
echo "----------------------------------------------"
# Test E2E publish with AI Writing Flow generation
publish_payload='{
    "topic": {
        "title": "E2E Integration Test",
        "description": "Testing complete flow from AI Writing Flow to publication",
        "viral_score": 9.0
    },
    "platform": "linkedin",
    "direct_content": false
}'
test_endpoint "Orchestrator /publish (AI Writing Flow)" "$ORCHESTRATOR_URL/publish" "POST" "$publish_payload" "200"

# Test with direct_content=true for comparison
direct_payload='{
    "topic": {
        "title": "Direct Content Test",
        "description": "Testing direct content publication"
    },
    "platform": "linkedin",
    "direct_content": true,
    "content": "This is direct content for testing"
}'
test_endpoint "Orchestrator /publish (Direct)" "$ORCHESTRATOR_URL/publish" "POST" "$direct_payload" "200"
echo ""

echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    echo "AI Writing Flow integration is working correctly."
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed!${NC}"
    echo "Please check the service logs for more details."
    exit 1
fi