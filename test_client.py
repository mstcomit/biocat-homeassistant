#!/usr/bin/env python3
"""Test script to verify the WaterCryst API client works like Home Assistant."""

import asyncio
import aiohttp
import sys
import os

# Add the custom_components path to Python path
sys.path.insert(0, '/home/mschobel/repos/biocat/custom_components')

from watercryst.api import WaterCrystClient, WaterCrystAuthenticationError, WaterCrystConnectionError

async def test_api_client(api_key: str):
    """Test the API client like Home Assistant does."""
    print(f"Testing API client with key: {api_key[:8]}...{api_key[-8:]}")
    
    # Test 1: Client creates its own session (like in direct usage)
    print("\n=== Test 1: Client creates own session ===")
    client1 = WaterCrystClient(api_key)
    try:
        state = await client1.get_state()
        print(f"✓ Success! Device online: {state.get('online')}, Mode: {state.get('mode', {}).get('name')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    finally:
        await client1.close()
    
    # Test 2: External session provided (like Home Assistant does)
    print("\n=== Test 2: External session provided (Home Assistant style) ===")
    async with aiohttp.ClientSession() as session:
        client2 = WaterCrystClient(api_key, session)
        try:
            state = await client2.get_state()
            print(f"✓ Success! Device online: {state.get('online')}, Mode: {state.get('mode', {}).get('name')}")
        except Exception as e:
            print(f"✗ Failed: {e}")
        # No need to close client2 since we manage the session

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_client.py <API_KEY>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    asyncio.run(test_api_client(api_key))