#!/bin/bash
# Quick fix script to help diagnose WaterCryst API empty response issues

echo "WaterCryst API Quick Diagnosis Tool"
echo "==================================="

if [ -z "$1" ]; then
    echo "Usage: $0 <API_KEY>"
    echo "This script will test your API key and help diagnose empty response issues."
    exit 1
fi

API_KEY="$1"
echo "Testing API key: ${API_KEY:0:8}...${API_KEY: -8}"
echo

# Check if Python debug script exists
if [ -f "debug_empty_response.py" ]; then
    echo "Running detailed Python diagnostics..."
    python3 debug_empty_response.py "$API_KEY"
else
    echo "Python debug script not found, running basic curl tests..."
    
    # Basic curl tests
    BASE_URL="https://appapi.watercryst.com/v1"
    
    echo "Testing state endpoint..."
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -H "X-API-KEY: $API_KEY" "$BASE_URL/state")
    http_code=$(echo "$response" | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    
    echo "  Status: $http_code"
    if [ "$http_code" = "200" ]; then
        if [ -z "$body" ] || [ "$body" = "" ]; then
            echo "  ⚠️  EMPTY RESPONSE DETECTED!"
            echo "  This is the issue causing the Home Assistant integration to fail."
        else
            echo "  ✓ Success! Response: ${body:0:100}..."
        fi
    else
        echo "  ✗ Error: $body"
    fi
fi

echo
echo "Recommended actions:"
echo "1. If you see empty responses, try restarting your BIOCAT device"
echo "2. Check your device's internet connection"
echo "3. Verify your API key is correct"
echo "4. Try again in a few minutes - the API might be temporarily unavailable"
echo "5. The updated integration now has retry logic to handle transient issues"