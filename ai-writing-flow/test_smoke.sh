#!/bin/bash

# AI Writing Flow Smoke Test Script
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AIWF_HOST=${AIWF_HOST:-localhost}
AIWF_PORT=${AIWF_PORT:-8003}
ORCHESTRATOR_HOST=${ORCHESTRATOR_HOST:-localhost}
ORCHESTRATOR_PORT=${ORCHESTRATOR_PORT:-8042}

echo "========================================="
echo "AI Writing Flow Integration Smoke Test"
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

# Test AI Writing Flow directly
echo "1. Testing AI Writing Flow Service"
echo "   Host: $AIWF_HOST:$AIWF_PORT"
echo ""

check_endpoint "http://$AIWF_HOST:$AIWF_PORT/health" "AIWF Health"
check_endpoint "http://$AIWF_HOST:$AIWF_PORT/" "AIWF Root"
check_endpoint "http://$AIWF_HOST:$AIWF_PORT/metrics" "AIWF Metrics"

echo ""

# Check health details
echo "2. Checking AIWF Health Details"
echo ""

health_response=$(curl -s "http://$AIWF_HOST:$AIWF_PORT/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
    echo -n "Overall Status: "
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}$status${NC}"
    elif [ "$status" = "degraded" ]; then
        echo -e "${YELLOW}$status${NC} (can still function)"
    else
        echo -e "${RED}$status${NC}"
    fi
    
    # Check Editorial Service dependency
    editorial_status=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('dependencies', {}).get('editorial_service', {}).get('status', 'unknown'))" 2>/dev/null)
    echo -n "Editorial Service Dependency: "
    if [ "$editorial_status" = "healthy" ]; then
        echo -e "${GREEN}$editorial_status${NC}"
    else
        echo -e "${YELLOW}$editorial_status${NC} (non-critical)"
    fi
else
    echo -e "${RED}Failed to get health response${NC}"
fi

echo ""

# Test content generation
echo "3. Testing Content Generation"
echo ""

generation_payload='{
    "topic": {
        "title": "The Future of AI",
        "description": "An exploration of emerging AI technologies and their impact on society",
        "content_type": "STANDALONE",
        "content_ownership": "ORIGINAL"
    },
    "platform": "linkedin",
    "mode": "selective",
    "checkpoints_enabled": true,
    "skip_research": false
}'

echo -n "AIWF Content Generation (selective): "
response=$(curl -s -X POST "http://$AIWF_HOST:$AIWF_PORT/generate" \
    -H "Content-Type: application/json" \
    -d "$generation_payload" \
    -o /tmp/aiwf_response.json \
    -w "%{http_code}" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} (HTTP $response)"
    
    # Check response details
    if [ -f /tmp/aiwf_response.json ]; then
        content_id=$(python3 -c "import json; data=json.load(open('/tmp/aiwf_response.json')); print(data.get('content_id', 'N/A'))" 2>/dev/null)
        status=$(python3 -c "import json; data=json.load(open('/tmp/aiwf_response.json')); print(data.get('status', 'N/A'))" 2>/dev/null)
        checkpoints=$(python3 -c "import json; data=json.load(open('/tmp/aiwf_response.json')); print(len(data.get('checkpoints_passed', {})))" 2>/dev/null)
        
        echo "  Content ID: $content_id"
        echo "  Status: $status"
        echo "  Checkpoints: $checkpoints"
    fi
else
    echo -e "${RED}✗${NC} (HTTP $response)"
fi

echo ""

# Test Orchestrator integration
echo "4. Testing Orchestrator Integration"
echo "   Host: $ORCHESTRATOR_HOST:$ORCHESTRATOR_PORT"
echo ""

check_endpoint "http://$ORCHESTRATOR_HOST:$ORCHESTRATOR_PORT/health" "Orchestrator Health"

# Test flow with direct_content=false
flow_payload='{
    "content": "Artificial Intelligence and Machine Learning Trends",
    "platform": "linkedin",
    "direct_content": false
}'

echo -n "Orchestrator Flow (direct_content=false): "
response=$(curl -s -X POST "http://$ORCHESTRATOR_HOST:$ORCHESTRATOR_PORT/flows/execute" \
    -H "Content-Type: application/json" \
    -d "$flow_payload" \
    -o /tmp/flow_response.json \
    -w "%{http_code}" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} (HTTP $response)"
    
    if [ -f /tmp/flow_response.json ]; then
        flow_id=$(python3 -c "import json; data=json.load(open('/tmp/flow_response.json')); print(data.get('flow_id', 'N/A'))" 2>/dev/null)
        ai_enabled=$(python3 -c "import json; data=json.load(open('/tmp/flow_response.json')); print(data.get('ai_writing_flow_enabled', False))" 2>/dev/null)
        
        echo "  Flow ID: $flow_id"
        echo -n "  AI Writing Flow Enabled: "
        if [ "$ai_enabled" = "True" ]; then
            echo -e "${GREEN}Yes${NC}"
        else
            echo -e "${RED}No${NC}"
        fi
        
        # Check flow status after a short delay
        if [ "$flow_id" != "N/A" ]; then
            sleep 2
            echo -n "  Flow Status Check: "
            status_response=$(curl -s "http://$ORCHESTRATOR_HOST:$ORCHESTRATOR_PORT/flows/status/$flow_id" 2>/dev/null)
            if [ $? -eq 0 ]; then
                flow_status=$(echo "$status_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
                if [ "$flow_status" = "completed" ]; then
                    echo -e "${GREEN}$flow_status${NC}"
                elif [ "$flow_status" = "running" ]; then
                    echo -e "${YELLOW}$flow_status${NC}"
                else
                    echo -e "${RED}$flow_status${NC}"
                fi
            else
                echo -e "${RED}Failed${NC}"
            fi
        fi
    fi
else
    echo -e "${RED}✗${NC} (HTTP $response)"
fi

echo ""

# Test flow with direct_content=true (traditional)
flow_payload_traditional='{
    "content": "Traditional content generation test",
    "platform": "linkedin",
    "direct_content": true
}'

echo -n "Orchestrator Flow (direct_content=true): "
response=$(curl -s -X POST "http://$ORCHESTRATOR_HOST:$ORCHESTRATOR_PORT/flows/execute" \
    -H "Content-Type: application/json" \
    -d "$flow_payload_traditional" \
    -o /tmp/flow_traditional.json \
    -w "%{http_code}" 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✓${NC} (HTTP $response)"
    
    if [ -f /tmp/flow_traditional.json ]; then
        ai_enabled=$(python3 -c "import json; data=json.load(open('/tmp/flow_traditional.json')); print(data.get('ai_writing_flow_enabled', True))" 2>/dev/null)
        echo -n "  AI Writing Flow Enabled: "
        if [ "$ai_enabled" = "False" ]; then
            echo -e "${GREEN}No (as expected)${NC}"
        else
            echo -e "${RED}Yes (unexpected!)${NC}"
        fi
    fi
else
    echo -e "${RED}✗${NC} (HTTP $response)"
fi

echo ""
echo "========================================="
echo "Smoke Test Complete"
echo "========================================="

# Cleanup
rm -f /tmp/aiwf_response.json /tmp/flow_response.json /tmp/flow_traditional.json