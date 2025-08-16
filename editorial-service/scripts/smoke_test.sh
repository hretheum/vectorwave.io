#!/bin/bash

# Editorial Service & ChromaDB Smoke Test Script
# Tests connectivity, health checks and basic validation

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CHROMADB_HOST=${CHROMADB_HOST:-localhost}
CHROMADB_PORT=${CHROMADB_PORT:-8000}
EDITORIAL_HOST=${EDITORIAL_HOST:-localhost}
EDITORIAL_PORT=${EDITORIAL_PORT:-8040}

echo "========================================="
echo "Editorial Service ChromaDB Connectivity Test"
echo "========================================="
echo ""

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name: "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Function to check JSON response
check_json_field() {
    local url=$1
    local field=$2
    local expected=$3
    local name=$4
    
    echo -n "Testing $name: "
    
    response=$(curl -s "$url" 2>/dev/null)
    value=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$field', 'NOT_FOUND'))" 2>/dev/null || echo "PARSE_ERROR")
    
    if [ "$value" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} ($field = $value)"
        return 0
    else
        echo -e "${RED}✗${NC} ($field = $value, expected $expected)"
        return 1
    fi
}

# Test ChromaDB directly
echo "1. Testing ChromaDB Direct Connection"
echo "   Host: $CHROMADB_HOST:$CHROMADB_PORT"
echo ""

check_endpoint "http://$CHROMADB_HOST:$CHROMADB_PORT/api/v2/heartbeat" "ChromaDB v2 Heartbeat"
check_endpoint "http://$CHROMADB_HOST:$CHROMADB_PORT/api/v1/heartbeat" "ChromaDB v1 Heartbeat (fallback)"
check_endpoint "http://$CHROMADB_HOST:$CHROMADB_PORT/api/v1/collections" "ChromaDB Collections"

echo ""

# Test Editorial Service
echo "2. Testing Editorial Service"
echo "   Host: $EDITORIAL_HOST:$EDITORIAL_PORT"
echo ""

check_endpoint "http://$EDITORIAL_HOST:$EDITORIAL_PORT/health" "Editorial Service Health"
check_endpoint "http://$EDITORIAL_HOST:$EDITORIAL_PORT/ready" "Editorial Service Readiness"
check_endpoint "http://$EDITORIAL_HOST:$EDITORIAL_PORT/info" "Editorial Service Info"
check_endpoint "http://$EDITORIAL_HOST:$EDITORIAL_PORT/metrics" "Editorial Service Metrics"

echo ""

# Check health details
echo "3. Checking Health Status Details"
echo ""

health_response=$(curl -s "http://$EDITORIAL_HOST:$EDITORIAL_PORT/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    # Check overall status
    status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
    echo -n "Overall Status: "
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}$status${NC}"
    elif [ "$status" = "degraded" ]; then
        echo -e "${YELLOW}$status${NC}"
    else
        echo -e "${RED}$status${NC}"
    fi
    
    # Check ChromaDB status
    chromadb_status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('checks', {}).get('chromadb', {}).get('status', 'unknown'))" 2>/dev/null)
    echo -n "ChromaDB Status: "
    if [ "$chromadb_status" = "healthy" ]; then
        echo -e "${GREEN}$chromadb_status${NC}"
    else
        echo -e "${RED}$chromadb_status${NC}"
    fi
    
    # Check if ChromaDB is initialized
    chromadb_initialized=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('checks', {}).get('chromadb', {}).get('initialized', False))" 2>/dev/null)
    echo -n "ChromaDB Initialized: "
    if [ "$chromadb_initialized" = "True" ]; then
        echo -e "${GREEN}Yes${NC}"
    else
        echo -e "${RED}No${NC}"
    fi
    
    # Check latency
    chromadb_latency=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('checks', {}).get('chromadb', {}).get('latency_ms', 'N/A'))" 2>/dev/null)
    echo "ChromaDB Latency: ${chromadb_latency}ms"
    
    # Check Redis status
    redis_status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('checks', {}).get('redis', {}).get('status', 'unknown'))" 2>/dev/null)
    echo -n "Redis Status: "
    if [ "$redis_status" = "healthy" ]; then
        echo -e "${GREEN}$redis_status${NC}"
    else
        echo -e "${YELLOW}$redis_status${NC} (non-critical)"
    fi
else
    echo -e "${RED}Failed to get health response${NC}"
fi

echo ""

# Test validation endpoints
echo "4. Testing Validation Endpoints"
echo ""

# Test comprehensive validation
comprehensive_payload='{"content": "Test article content for validation", "mode": "comprehensive"}'
echo -n "Comprehensive Validation: "
response=$(curl -s -X POST "http://$EDITORIAL_HOST:$EDITORIAL_PORT/validate/comprehensive" \
    -H "Content-Type: application/json" \
    -d "$comprehensive_payload" \
    -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} (HTTP $response)"
else
    echo -e "${RED}✗${NC} (HTTP $response)"
fi

# Test selective validation
selective_payload='{"content": "Test content", "mode": "selective", "checkpoint": "pre-writing"}'
echo -n "Selective Validation: "
response=$(curl -s -X POST "http://$EDITORIAL_HOST:$EDITORIAL_PORT/validate/selective" \
    -H "Content-Type: application/json" \
    -d "$selective_payload" \
    -o /dev/null -w "%{http_code}" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} (HTTP $response)"
else
    echo -e "${RED}✗${NC} (HTTP $response)"
fi

echo ""

# Check metrics
echo "5. Checking ChromaDB Metrics"
echo ""

metrics=$(curl -s "http://$EDITORIAL_HOST:$EDITORIAL_PORT/metrics" 2>/dev/null)
if [ $? -eq 0 ]; then
    # Extract ChromaDB metrics
    connection_status=$(echo "$metrics" | grep "chromadb_connection_status" | grep -v "#" | awk '{print $2}' | head -1)
    echo -n "ChromaDB Connection Metric: "
    if [ "$connection_status" = "1.0" ]; then
        echo -e "${GREEN}Connected (1.0)${NC}"
    else
        echo -e "${RED}Disconnected ($connection_status)${NC}"
    fi
    
    # Check for connection attempts
    attempts=$(echo "$metrics" | grep "chromadb_connect_attempts_total" | grep -v "#" | awk '{print $2}' | head -1)
    failures=$(echo "$metrics" | grep "chromadb_connect_failures_total" | grep -v "#" | awk '{print $2}' | head -1)
    
    if [ -n "$attempts" ]; then
        echo "Connection Attempts: $attempts"
    fi
    if [ -n "$failures" ]; then
        echo "Connection Failures: $failures"
    fi
else
    echo -e "${RED}Failed to get metrics${NC}"
fi

echo ""
echo "========================================="
echo "Smoke Test Complete"
echo "========================================="