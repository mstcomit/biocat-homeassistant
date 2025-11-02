#!/bin/bash
# Debug script to test WaterCryst API authentication

if [ -z "$1" ]; then
    echo "Usage: $0 <API_KEY>"
    exit 1
fi

API_KEY="$1"
BASE_URL="https://appapi.watercryst.com/v1"

echo "Testing API key: ${API_KEY:0:8}...${API_KEY: -8}"
echo "Base URL: $BASE_URL"
echo

# Test different endpoints
endpoints=("state" "measurements/direct" "measurements/now" "statistics/daily")

for endpoint in "${endpoints[@]}"; do
    url="$BASE_URL/$endpoint"
    echo "Testing endpoint: $url"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "X-API-KEY: $API_KEY" "$url")
    
    # Extract HTTP status
    http_code=$(echo "$response" | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    
    echo "  Status: $http_code"
    
    if [ "$http_code" = "200" ]; then
        echo "  Success! Response: ${body:0:200}..."
    else
        echo "  Error response: $body"
    fi
    echo
done