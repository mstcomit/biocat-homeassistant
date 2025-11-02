#!/bin/bash
# Check the exact JSON structure returned by the API

if [ -z "$1" ]; then
    echo "Usage: $0 <API_KEY>"
    exit 1
fi

API_KEY="$1"
BASE_URL="https://appapi.watercryst.com/v1"

echo "=== Full API Response Structure ==="
echo

echo "1. /state endpoint:"
curl -s -H "X-API-KEY: $API_KEY" "$BASE_URL/state" | python3 -m json.tool
echo

echo "2. /measurements/direct endpoint:"
curl -s -H "X-API-KEY: $API_KEY" "$BASE_URL/measurements/direct" | python3 -m json.tool
echo

echo "3. /statistics/cumulative/daily endpoint:"
curl -s -H "X-API-KEY: $API_KEY" "$BASE_URL/statistics/cumulative/daily"
echo

echo "4. /statistics/cumulative/total endpoint:"
curl -s -H "X-API-KEY: $API_KEY" "$BASE_URL/statistics/cumulative/total"
echo