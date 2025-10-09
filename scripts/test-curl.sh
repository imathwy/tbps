#!/usr/bin/env bash
set -eu -o pipefail

BASE_URL="http://localhost:8000"

echo "Health check:"
curl -s "$BASE_URL/health" | jq .
echo

echo "Search for '1 + 1 = 2':"
RESPONSE=$(curl -s "$BASE_URL/find-similar-theorems" \
  -H "Content-Type: application/json" \
  -d '{"expression": "1 + 1 = 2", "k": 5}')

echo "$RESPONSE" | jq .

RESULT_COUNT=$(echo "$RESPONSE" | jq '.results | length')

if [ "$RESULT_COUNT" -eq 0 ]; then
  echo "Error: results is empty"
  exit 1
fi

echo
echo "$RESULT_COUNT results found"
