"""WaterCryst BIOCAT API client."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

import aiohttp
from aiohttp import ClientError, ClientTimeout

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://appapi.watercryst.com/v1"
API_TIMEOUT = 30


class WaterCrystAPIError(Exception):
    """Exception to indicate a general API error."""


class WaterCrystAuthenticationError(WaterCrystAPIError):
    """Exception to indicate an authentication error."""


class WaterCrystConnectionError(WaterCrystAPIError):
    """Exception to indicate a connection error."""


class WaterCrystRateLimitError(WaterCrystAPIError):
    """Exception to indicate rate limit exceeded."""


class WaterCrystClient:
    """WaterCryst BIOCAT API client."""

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the WaterCryst client."""
        self._api_key = api_key
        self._session = session
        self._close_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp client session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=ClientTimeout(total=API_TIMEOUT),
                headers={"X-API-KEY": self._api_key},
            )
            self._close_session = True
        return self._session

    async def close(self) -> None:
        """Close the client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the WaterCryst API."""
        session = await self._get_session()
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise WaterCrystAuthenticationError("Invalid API key")
                elif response.status == 403:
                    raise WaterCrystAPIError("API endpoint is disabled")
                elif response.status == 429:
                    raise WaterCrystRateLimitError("API rate limit exceeded")
                elif response.status == 400:
                    raise WaterCrystAPIError("Operation not supported")
                else:
                    raise WaterCrystAPIError(f"API request failed with status {response.status}")
        except ClientError as err:
            raise WaterCrystConnectionError(f"Connection error: {err}") from err

    # State and measurements
    async def get_state(self) -> Dict[str, Any]:
        """Get the current device state."""
        return await self._request("state")

    async def get_measurements_direct(self) -> Dict[str, Any]:
        """Get current measurement data directly."""
        return await self._request("measurements/direct")

    async def get_measurements_now(self) -> Dict[str, Any]:
        """Get current measurement data (legacy, via webhook)."""
        return await self._request("measurements/now")

    # Statistics
    async def get_daily_statistics_direct(self) -> Dict[str, Any]:
        """Get daily statistics directly."""
        return await self._request("statistics/daily/direct")

    async def get_daily_statistics(self) -> Dict[str, Any]:
        """Get daily statistics (legacy, via webhook)."""
        return await self._request("statistics/daily")

    async def get_daily_consumption(self) -> float:
        """Get total water consumption today in liters."""
        result = await self._request("statistics/cumulative/daily")
        return float(result) if isinstance(result, (int, float)) else 0.0

    async def get_total_consumption(self) -> float:
        """Get total water consumption since installation in liters."""
        result = await self._request("statistics/cumulative/total")
        return float(result) if isinstance(result, (int, float)) else 0.0

    # Absence mode
    async def enable_absence_mode(self) -> Dict[str, Any]:
        """Enable absence mode."""
        return await self._request("absence/enable")

    async def disable_absence_mode(self) -> Dict[str, Any]:
        """Disable absence mode."""
        return await self._request("absence/disable")

    # Leakage protection
    async def pause_leakage_protection(self, minutes: int) -> Dict[str, Any]:
        """Pause leakage protection for specified minutes (1-4320)."""
        if not 1 <= minutes <= 4320:
            raise ValueError("Minutes must be between 1 and 4320")
        return await self._request("leakageprotection/pause", {"minutes": minutes})

    async def unpause_leakage_protection(self) -> Dict[str, Any]:
        """Unpause leakage protection."""
        return await self._request("leakageprotection/unpause")

    # Water supply
    async def open_water_supply(self) -> Dict[str, Any]:
        """Open water supply."""
        return await self._request("watersupply/open")

    async def close_water_supply(self) -> Dict[str, Any]:
        """Close water supply."""
        return await self._request("watersupply/close")

    # Tests and maintenance
    async def start_self_test(self) -> Dict[str, Any]:
        """Start self test."""
        return await self._request("selftest")

    async def start_microleakage_measurement(self) -> Dict[str, Any]:
        """Start micro-leakage measurement."""
        return await self._request("mlmeasurement/start")

    async def acknowledge_event(self) -> Dict[str, Any]:
        """Acknowledge the current device event."""
        return await self._request("ackevent")

    # Utility methods
    @staticmethod
    def parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string to datetime object."""
        if not dt_string:
            return None
        try:
            return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def get_mode_name(mode_id: str) -> str:
        """Get human-readable mode name from mode ID."""
        mode_names = {
            "SU": "Start Up",
            "RS": "Rinse",
            "ST": "Self Test",
            "UD": "Firmware Update",
            "FS": "Failsafe",
            "ER": "Error Mode",
            "WO": "Water Off",
            "WT": "Water Treatment",
            "TD": "Thermal Disinfection",
            "MC": "Maintenance Cleaning",
        }
        return mode_names.get(mode_id, mode_id)

    @staticmethod
    def get_ml_state_name(ml_state: str) -> str:
        """Get human-readable microleakage state name."""
        ml_state_names = {
            "idle": "Idle",
            "running": "Running",
            "success": "No Leakage",
            "leakage": "Leakage Detected",
            "cancelled": "Cancelled",
            "failure-pressure-drop": "Pressure Drop",
            "failure-water-tap": "Water Tap Opened",
            "failure-start-pressure": "Low Start Pressure",
            "failure-unknown": "Unknown Failure",
        }
        return ml_state_names.get(ml_state, ml_state)

    @staticmethod
    def get_event_category_icon(category: str) -> str:
        """Get icon for event category."""
        icons = {
            "error": "mdi:alert-circle",
            "warning": "mdi:alert",
            "info": "mdi:information",
        }
        return icons.get(category, "mdi:information")