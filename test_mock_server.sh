#!/bin/bash

# Test script for Mock Theorem Similarity Search API
# Usage: ./test_mock_server.sh
# Make sure to run: chmod +x test_mock_server.sh

set -e  # Exit on any error

BASE_URL="http://localhost:8001"
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}🧪 Testing Mock Theorem Similarity Search API${NC}"
echo "Base URL: $BASE_URL"
echo "================================================"

# Function to run test with pretty output
run_test() {
    local test_name="$1"
    local curl_cmd="$2"
    local expected_status="${3:-200}"

    echo -e "\n${BOLD}Testing: $test_name${NC}"
    echo "Command: $curl_cmd"
    echo "Expected Status: $expected_status"
    echo "----------------------------------------"

    # Run curl and capture both status and response
    local response
    local status_code

    if command -v jq &> /dev/null; then
        response=$(eval "$curl_cmd" 2>/dev/null)
        status_code=$(eval "$curl_cmd -w '%{http_code}' -o /dev/null -s" 2>/dev/null)
        echo "$response" | jq .
    else
        response=$(eval "$curl_cmd" 2>/dev/null)
        status_code=$(eval "$curl_cmd -w '%{http_code}' -o /dev/null -s" 2>/dev/null)
        echo "$response"
    fi

    # Check status code
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ Status: $status_code (Expected: $expected_status)${NC}"
    else
        echo -e "${RED}❌ Status: $status_code (Expected: $expected_status)${NC}"
    fi
}

# Check if server is running
echo -e "\n${YELLOW}🔍 Checking if server is running...${NC}"
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ Server is not running at $BASE_URL${NC}"
    echo "Please start the server with: uv run mock_server.py"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"

# Test 1: Health Check
run_test "Health Check" \
    "curl -s -X GET '$BASE_URL/health' -H 'Content-Type: application/json'"

# Test 2: Root Endpoint
run_test "Root Endpoint" \
    "curl -s -X GET '$BASE_URL/' -H 'Content-Type: application/json'"

# Test 3: Mock Info
run_test "Mock Info Endpoint" \
    "curl -s -X GET '$BASE_URL/mock-info' -H 'Content-Type: application/json'"

# Test 4: Basic Search
run_test "Basic Theorem Search" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"forall (a b : Nat), a + b = b + a\"}'"

# Test 5: Search with Custom k
run_test "Search with Custom k Value" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"forall (x y : Real), x * y = y * x\", \"k\": 10}'"

# Test 6: Search with Node Ratio
run_test "Search with Node Ratio" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"forall (A B : Set), A ∪ B = B ∪ A\", \"k\": 15, \"node_ratio\": 1.5}'"

# Test 7: Empty Expression (Should return 400)
run_test "Empty Expression Error" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"\"}'" \
    "400"

# Test 8: Too Long Expression (Should return 400)
LONG_EXPR=$(printf 'a%.0s' {1..1001})
run_test "Too Long Expression Error" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"$LONG_EXPR\"}'" \
    "400"

# Test 9: Invalid k Value (Should return 422)
run_test "Invalid k Value Error" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"simple theorem\", \"k\": 150}'" \
    "422"

# Test 10: Invalid JSON (Should return 422)
run_test "Invalid JSON Error" \
    "curl -s -X POST '$BASE_URL/find-similar-theorems' -H 'Content-Type: application/json' -d '{\"expression\": \"test\", \"k\": \"not_a_number\"}'" \
    "422"

# Test 11: Consistency Test - Same input should give same results
echo -e "\n${BOLD}🔄 Testing Result Consistency${NC}"
echo "Running the same query twice to verify consistent results..."
echo "----------------------------------------"

CONSISTENT_QUERY='{"expression": "consistency test theorem"}'

echo "First request:"
RESULT1=$(curl -s -X POST "$BASE_URL/find-similar-theorems" -H 'Content-Type: application/json' -d "$CONSISTENT_QUERY")

echo "Second request:"
RESULT2=$(curl -s -X POST "$BASE_URL/find-similar-theorems" -H 'Content-Type: application/json' -d "$CONSISTENT_QUERY")

# Compare results (excluding processing time sensitive fields)
if command -v jq &> /dev/null; then
    HASH1=$(echo "$RESULT1" | jq -S '.results | map({name, similarity_score, statement, node_count})' | md5sum)
    HASH2=$(echo "$RESULT2" | jq -S '.results | map({name, similarity_score, statement, node_count})' | md5sum)

    if [ "$HASH1" = "$HASH2" ]; then
        echo -e "${GREEN}✅ Results are consistent across requests${NC}"
    else
        echo -e "${RED}❌ Results differ between requests${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  jq not available, skipping consistency check${NC}"
fi

# Summary
echo -e "\n${BOLD}📊 Test Summary${NC}"
echo "================================================"
echo -e "${GREEN}✅ All basic endpoint tests completed${NC}"
echo -e "${GREEN}✅ Error handling tests completed${NC}"
echo -e "${GREEN}✅ Consistency test completed${NC}"
echo ""
echo "🔗 API Documentation: $BASE_URL/docs"
echo "🔧 Mock Info Endpoint: $BASE_URL/mock-info"

if ! command -v jq &> /dev/null; then
    echo ""
    echo -e "${YELLOW}💡 Tip: Install jq for prettier JSON output:${NC}"
    echo "   macOS: brew install jq"
    echo "   Ubuntu: apt install jq"
fi

echo -e "\n${BOLD}🎉 Testing completed!${NC}"
