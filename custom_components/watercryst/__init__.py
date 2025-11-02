"""The WaterCryst BIOCAT integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WaterCrystClient, WaterCrystConnectionError, WaterCrystAPIError
from .const import (
    CONF_API_KEY,
    DOMAIN,
    PLATFORMS,
    UPDATE_INTERVAL,
    MEASUREMENTS_UPDATE_INTERVAL,
)
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WaterCryst BIOCAT from a config entry."""
    session = async_get_clientsession(hass)
    client = WaterCrystClient(entry.data[CONF_API_KEY], session)

    # Create coordinators for different data types
    state_coordinator = WaterCrystStateCoordinator(hass, client)
    measurements_coordinator = WaterCrystMeasurementsCoordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    try:
        await state_coordinator.async_config_entry_first_refresh()
        await measurements_coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "state_coordinator": state_coordinator,
        "measurements_coordinator": measurements_coordinator,
    }

    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload services
    await async_unload_services(hass)
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["client"].close()

    return unload_ok


class WaterCrystStateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WaterCryst device state data."""

    def __init__(self, hass: HomeAssistant, client: WaterCrystClient) -> None:
        """Initialize the state coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="WaterCryst State",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get device state and consumption data
            state = await self.client.get_state()
            
            # Also fetch consumption statistics
            try:
                daily_consumption = await self.client.get_daily_consumption()
                total_consumption = await self.client.get_total_consumption()
                state["daily_consumption"] = daily_consumption
                state["total_consumption"] = total_consumption
            except WaterCrystAPIError:
                # Some devices might not support consumption endpoints
                _LOGGER.debug("Consumption data not available for this device")
                state["daily_consumption"] = None
                state["total_consumption"] = None

            return state
        except WaterCrystConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class WaterCrystMeasurementsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WaterCryst measurements data."""

    def __init__(self, hass: HomeAssistant, client: WaterCrystClient) -> None:
        """Initialize the measurements coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="WaterCryst Measurements",
            update_interval=timedelta(seconds=MEASUREMENTS_UPDATE_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch measurements data from API endpoint."""
        try:
            # Try direct measurements first (newer devices)
            try:
                measurements = await self.client.get_measurements_direct()
            except WaterCrystAPIError:
                # Fallback to webhook-based measurements for older devices
                measurements = await self.client.get_measurements_now()
                _LOGGER.debug("Using legacy measurements endpoint")

            return measurements
        except WaterCrystConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err