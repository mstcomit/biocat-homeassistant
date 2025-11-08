#!/usr/bin/env python3
"""
Troubleshooting script for WaterCryst API empty response issues.

This script helps diagnose and fix the "API endpoint returned empty response" error
that can occur during Home Assistant configuration setup.

Usage:
    python troubleshoot_empty_responses.py <API_KEY>
"""

import asyncio
import aiohttp
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE_URL = "https://appapi.watercryst.com/v1"
API_TIMEOUT = 30

class TroubleshootResults:
    """Container for troubleshooting results."""
    
    def __init__(self):
        self.working_endpoints: List[str] = []
        self.empty_endpoints: List[str] = []
        self.error_endpoints: List[str] = []
        self.authentication_valid = False
        self.connectivity_issues = False
        self.recommendations: List[str] = []

async def test_endpoint_detailed(session: aiohttp.ClientSession, api_key: str, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Test a specific endpoint with detailed analysis.
    
    Returns:
        Tuple of (success, details) where details contains diagnostic information
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"X-API-KEY": api_key}
    
    details = {
        "endpoint": endpoint,
        "url": url,
        "status_code": None,
        "content_length": None,
        "content_type": None,
        "response_text": None,
        "response_length": 0,
        "is_empty": False,
        "is_json": False,
        "error": None
    }
    
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as response:
            details["status_code"] = response.status
            details["content_length"] = response.headers.get('content-length')
            details["content_type"] = response.headers.get('content-type', '')
            
            if response.status == 200:
                text = await response.text()
                details["response_text"] = text
                details["response_length"] = len(text)
                details["is_empty"] = not text or text.strip() == ""
                
                if 'application/json' in details["content_type"]:
                    details["is_json"] = True
                    try:
                        json.loads(text)
                    except json.JSONDecodeError as e:
                        details["error"] = f"Invalid JSON: {e}"
                        return False, details
                
                return not details["is_empty"], details
            elif response.status == 401:
                details["error"] = "Authentication failed - Invalid API key"
                return False, details
            elif response.status == 403:
                details["error"] = "Forbidden - API endpoint may be disabled"
                return False, details
            elif response.status == 429:
                details["error"] = "Rate limit exceeded"
                return False, details
            else:
                error_text = await response.text()
                details["error"] = f"HTTP {response.status}: {error_text}"
                return False, details
                
    except asyncio.TimeoutError:
        details["error"] = "Request timeout"
        return False, details
    except Exception as e:
        details["error"] = f"Connection error: {e}"
        return False, details

async def test_all_endpoints(api_key: str) -> TroubleshootResults:
    """Test all known endpoints and categorize results."""
    
    endpoints = [
        "state",
        "measurements/direct",
        "measurements/now",
        "statistics/daily/direct", 
        "statistics/daily",
        "statistics/cumulative/daily",
        "statistics/cumulative/total",
    ]
    
    results = TroubleshootResults()
    
    print(f"\n{'='*60}")
    print("TESTING ALL ENDPOINTS")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\nTesting /{endpoint}...")
            
            success, details = await test_endpoint_detailed(session, api_key, endpoint)
            
            # Print summary
            if success:
                print(f"  ✓ SUCCESS - Response length: {details['response_length']}")
                results.working_endpoints.append(endpoint)
            elif details["status_code"] == 401:
                print(f"  ✗ AUTHENTICATION ERROR: {details['error']}")
                results.error_endpoints.append(endpoint)
                return results  # Stop testing if auth fails
            elif details["is_empty"]:
                print(f"  ⚠ EMPTY RESPONSE - Status: {details['status_code']}")
                results.empty_endpoints.append(endpoint)
            else:
                print(f"  ✗ ERROR: {details['error']}")
                results.error_endpoints.append(endpoint)
            
            # Print detailed info for debugging
            if details["status_code"]:
                print(f"    Status: {details['status_code']}")
                print(f"    Content-Type: {details['content_type']}")
                print(f"    Content-Length: {details['content_length']}")
                if details["response_text"] and len(details["response_text"]) < 200:
                    print(f"    Response: '{details['response_text']}'")
    
    # Check if authentication worked at least once
    results.authentication_valid = len(results.working_endpoints) > 0 or len(results.empty_endpoints) > 0
    results.connectivity_issues = len(results.error_endpoints) == len(endpoints)
    
    return results

async def test_retry_mechanism(api_key: str, endpoint: str = "state", max_attempts: int = 3) -> bool:
    """Test if empty responses are transient by retrying."""
    
    print(f"\n{'='*60}")
    print(f"TESTING RETRY MECHANISM FOR /{endpoint}")
    print(f"{'='*60}")
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1}/{max_attempts}")
            
            success, details = await test_endpoint_detailed(session, api_key, endpoint)
            
            if success:
                print(f"  ✓ SUCCESS on attempt {attempt + 1}")
                return True
            elif details["is_empty"]:
                print(f"  ⚠ Empty response on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    print("  Waiting 2 seconds before retry...")
                    await asyncio.sleep(2)
            else:
                print(f"  ✗ Error on attempt {attempt + 1}: {details['error']}")
                return False
    
    print(f"  ✗ All {max_attempts} attempts returned empty responses")
    return False

def generate_recommendations(results: TroubleshootResults) -> List[str]:
    """Generate troubleshooting recommendations based on test results."""
    
    recommendations = []
    
    if not results.authentication_valid:
        recommendations.extend([
            "❌ API key appears to be invalid",
            "  → Double-check your API key in the WaterCryst app",
            "  → Ensure the API key is copied correctly without extra spaces",
            "  → Try generating a new API key in the app"
        ])
        return recommendations
    
    if results.connectivity_issues:
        recommendations.extend([
            "❌ Network connectivity issues detected",
            "  → Check your internet connection",
            "  → Verify firewall settings allow HTTPS traffic to appapi.watercryst.com",
            "  → Try again later in case of temporary server issues"
        ])
        return recommendations
    
    if results.working_endpoints:
        recommendations.extend([
            f"✅ API key is valid - {len(results.working_endpoints)} endpoints working",
            f"  Working endpoints: {', '.join(results.working_endpoints)}"
        ])
    
    if results.empty_endpoints:
        recommendations.extend([
            f"⚠️  {len(results.empty_endpoints)} endpoints return empty responses",
            f"  Empty endpoints: {', '.join(results.empty_endpoints)}",
            "  This might indicate:",
            "    • Device is not fully initialized or ready",
            "    • Device model doesn't support these specific endpoints", 
            "    • Temporary server-side issues",
            "    • Device is in a special mode (maintenance, update, etc.)"
        ])
        
        recommendations.extend([
            "",
            "📋 IMMEDIATE FIXES FOR HOME ASSISTANT SETUP:",
            "1. Try setting up the integration anyway - it may work despite empty responses",
            "2. Wait 10-15 minutes and try setup again (device may be initializing)",
            "3. Check device status in the official WaterCryst app",
            "4. Restart your WaterCryst device if possible",
            "5. Contact WaterCryst support if the issue persists"
        ])
    
    if results.error_endpoints:
        recommendations.extend([
            f"❌ {len(results.error_endpoints)} endpoints have errors",
            f"  Error endpoints: {', '.join(results.error_endpoints)}",
            "  These endpoints may not be supported by your device model"
        ])
    
    return recommendations

async def main():
    """Main troubleshooting function."""
    
    if len(sys.argv) != 2:
        print("Usage: python troubleshoot_empty_responses.py <API_KEY>")
        print("\nThis script helps diagnose 'empty response' errors during")
        print("Home Assistant WaterCryst integration setup.")
        sys.exit(1)
    
    api_key = sys.argv[1].strip()
    
    print("WaterCryst API Troubleshooting Tool")
    print("=" * 40)
    print(f"API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else '***'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"API Base URL: {API_BASE_URL}")
    
    # Test all endpoints
    results = await test_all_endpoints(api_key)
    
    # Test retry mechanism for problematic endpoints
    if results.empty_endpoints:
        retry_success = await test_retry_mechanism(api_key, results.empty_endpoints[0])
        if retry_success:
            results.recommendations.append("✅ Retry mechanism can resolve empty responses")
    
    # Generate recommendations
    recommendations = generate_recommendations(results)
    results.recommendations.extend(recommendations)
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    print(f"Working endpoints: {len(results.working_endpoints)}")
    print(f"Empty response endpoints: {len(results.empty_endpoints)}")
    print(f"Error endpoints: {len(results.error_endpoints)}")
    print(f"Authentication valid: {'✅' if results.authentication_valid else '❌'}")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    for recommendation in results.recommendations:
        print(recommendation)
    
    # Exit code for scripting
    if results.authentication_valid and not results.connectivity_issues:
        sys.exit(0)  # Success - API key works
    elif not results.authentication_valid:
        sys.exit(1)  # Authentication failure
    else:
        sys.exit(2)  # Connectivity issues

if __name__ == "__main__":
    asyncio.run(main())