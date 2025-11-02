#!/usr/bin/env python3
"""Enhanced debug script to diagnose empty response issues with WaterCryst API."""

import asyncio
import aiohttp
import sys
import os
import json
import logging
from datetime import datetime

# Add the custom_components path to Python path
sys.path.insert(0, '/home/mschobel/repos/biocat/custom_components')

from watercryst.api import WaterCrystClient, WaterCrystAuthenticationError, WaterCrystConnectionError, WaterCrystAPIError

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def detailed_api_test(api_key: str, endpoint: str):
    """Test a specific API endpoint with detailed debugging."""
    base_url = "https://appapi.watercryst.com/v1"
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    print(f"\n{'='*60}")
    print(f"Testing endpoint: {endpoint}")
    print(f"Full URL: {url}")
    print(f"{'='*60}")
    
    headers = {"X-API-KEY": api_key}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                print(f"Status Code: {response.status}")
                print(f"Status Reason: {response.reason}")
                print(f"Headers: {dict(response.headers)}")
                
                # Check content length
                content_length = response.headers.get('content-length', 'Not specified')
                print(f"Content-Length: {content_length}")
                
                # Check content type
                content_type = response.headers.get('content-type', 'Not specified')
                print(f"Content-Type: {content_type}")
                
                # Read response body
                try:
                    if 'application/json' in content_type:
                        data = await response.json()
                        print(f"JSON Response: {json.dumps(data, indent=2)}")
                        return data
                    else:
                        text = await response.text()
                        print(f"Text Response: '{text}'")
                        print(f"Response Length: {len(text)} characters")
                        if len(text) == 0:
                            print("⚠️  EMPTY RESPONSE DETECTED!")
                        return text
                except Exception as e:
                    print(f"Error reading response: {e}")
                    return None
                    
        except Exception as e:
            print(f"Request failed: {e}")
            return None

async def test_with_client(api_key: str):
    """Test using the WaterCryst client to reproduce the exact error."""
    print(f"\n{'='*60}")
    print("Testing with WaterCryst Client (reproducing HA setup)")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        client = WaterCrystClient(api_key, session)
        
        endpoints_to_test = [
            ("get_state", "state"),
            ("get_measurements_direct", "measurements/direct"),
            ("get_measurements_now", "measurements/now"),
            ("get_daily_consumption", "statistics/cumulative/daily"),
            ("get_total_consumption", "statistics/cumulative/total"),
        ]
        
        for method_name, endpoint in endpoints_to_test:
            print(f"\n--- Testing {method_name} (/{endpoint}) ---")
            try:
                method = getattr(client, method_name)
                result = await method()
                print(f"✓ Success: {result}")
            except WaterCrystAPIError as e:
                if "empty response" in str(e).lower():
                    print(f"✗ EMPTY RESPONSE ERROR: {e}")
                else:
                    print(f"✗ API Error: {e}")
            except Exception as e:
                print(f"✗ Unexpected Error: {e}")

async def test_retry_mechanism(api_key: str):
    """Test if empty responses are transient by retrying."""
    print(f"\n{'='*60}")
    print("Testing retry mechanism for transient empty responses")
    print(f"{'='*60}")
    
    endpoint = "state"
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1}/{max_retries}")
        result = await detailed_api_test(api_key, endpoint)
        
        if result is not None and (isinstance(result, dict) or (isinstance(result, str) and len(result) > 0)):
            print(f"✓ Success on attempt {attempt + 1}")
            return True
        else:
            print(f"✗ Empty or null response on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                print("Waiting 2 seconds before retry...")
                await asyncio.sleep(2)
    
    print("✗ All retry attempts failed")
    return False

async def test_different_endpoints(api_key: str):
    """Test all available endpoints to see which ones work."""
    print(f"\n{'='*60}")
    print("Testing all available endpoints")
    print(f"{'='*60}")
    
    endpoints = [
        "state",
        "measurements/direct",
        "measurements/now", 
        "statistics/daily/direct",
        "statistics/daily",
        "statistics/cumulative/daily",
        "statistics/cumulative/total",
    ]
    
    working_endpoints = []
    empty_endpoints = []
    error_endpoints = []
    
    for endpoint in endpoints:
        print(f"\n--- Testing /{endpoint} ---")
        result = await detailed_api_test(api_key, endpoint)
        
        if result is None:
            error_endpoints.append(endpoint)
        elif (isinstance(result, str) and len(result) == 0) or (isinstance(result, dict) and len(result) == 0):
            empty_endpoints.append(endpoint)
        else:
            working_endpoints.append(endpoint)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Working endpoints: {working_endpoints}")
    print(f"Empty response endpoints: {empty_endpoints}")
    print(f"Error endpoints: {error_endpoints}")
    
    return working_endpoints, empty_endpoints, error_endpoints

async def main():
    """Main debugging function."""
    if len(sys.argv) != 2:
        print("Usage: python debug_empty_response.py <API_KEY>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    print(f"Debugging WaterCryst API with key: {api_key[:8]}...{api_key[-8:]}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Direct endpoint testing
    working, empty, error = await test_different_endpoints(api_key)
    
    # Test 2: Client testing (reproducing HA behavior)
    await test_with_client(api_key)
    
    # Test 3: Retry mechanism
    if empty or error:
        await test_retry_mechanism(api_key)
    
    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if working:
        print(f"✓ Some endpoints are working: {working}")
        print("  Consider using alternative endpoints or implementing fallback logic")
    
    if empty:
        print(f"⚠️  Empty response endpoints: {empty}")
        print("  These may be device-specific or require different parameters")
        print("  Consider implementing retry logic with exponential backoff")
    
    if error:
        print(f"✗ Error endpoints: {error}")
        print("  These endpoints may not be supported by your device model")
    
    print("\nSuggested fixes:")
    print("1. Implement retry logic with exponential backoff")
    print("2. Add fallback to alternative endpoints")
    print("3. Make empty responses non-fatal during setup")
    print("4. Add device model detection to use appropriate endpoints")

if __name__ == "__main__":
    asyncio.run(main())