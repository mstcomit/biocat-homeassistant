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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WaterCryst BIOCAT from a config entry."""
    _LOGGER.debug("Setting up WaterCryst BIOCAT integration")
    session = async_get_clientsession(hass)
    client = WaterCrystClient(entry.data[CONF_API_KEY], session)

    # Create coordinators for different data types
    _LOGGER.debug("Creating coordinators")
    state_coordinator = WaterCrystStateCoordinator(hass, client)
    measurements_coordinator = WaterCrystMeasurementsCoordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    # Use exponential backoff for resilient setup
    _LOGGER.debug("Performing initial data refresh with retry logic")
    
    max_setup_retries = 3
    base_delay = 2  # seconds
    
    for attempt in range(max_setup_retries):
        try:
            _LOGGER.debug("Setup attempt %d/%d", attempt + 1, max_setup_retries)
            
            # Try state coordinator first
            await state_coordinator.async_config_entry_first_refresh()
            _LOGGER.debug("State coordinator first refresh completed")
            
            # Try measurements coordinator
            try:
                await measurements_coordinator.async_config_entry_first_refresh()
                _LOGGER.debug("Measurements coordinator first refresh completed")
            except UpdateFailed as err:
                # Measurements might not be available on all devices
                if "empty response" in str(err).lower() or "not supported" in str(err).lower():
                    _LOGGER.warning("Measurements coordinator failed (device may not support this): %s", err)
                    # Continue setup without measurements for now
                else:
                    raise
            
            # If we get here, setup was successful
            break
            
        except UpdateFailed as err:
            if attempt < max_setup_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                _LOGGER.warning(
                    "Initial data refresh failed on attempt %d/%d: %s - retrying in %d seconds", 
                    attempt + 1, max_setup_retries, err, delay
                )
                await asyncio.sleep(delay)
            else:
                _LOGGER.error("Initial data refresh failed after %d attempts: %s", max_setup_retries, err)
                raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "state_coordinator": state_coordinator,
        "measurements_coordinator": measurements_coordinator,
    }

    # Set up all platforms
    _LOGGER.debug("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services
    _LOGGER.debug("Setting up services")
    await async_setup_services(hass)

    _LOGGER.info("WaterCryst BIOCAT integration setup completed successfully")
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
            _LOGGER.debug("Fetching device state from WaterCryst API")
            # Get device state and consumption data
            state = await self.client.get_state()
            _LOGGER.debug("Successfully fetched state: %s", state)
            
            # Also fetch consumption statistics
            try:
                _LOGGER.debug("Fetching consumption statistics")
                daily_consumption = await self.client.get_daily_consumption()
                total_consumption = await self.client.get_total_consumption()
                state["daily_consumption"] = daily_consumption
                state["total_consumption"] = total_consumption
                _LOGGER.debug("Successfully fetched consumption data: daily=%s, total=%s", daily_consumption, total_consumption)
            except WaterCrystAPIError as err:
                # Some devices might not support consumption endpoints
                _LOGGER.warning("Consumption data not available for this device: %s", err)
                state["daily_consumption"] = None
                state["total_consumption"] = None

            _LOGGER.debug("Final coordinator state data: %s", state)
            return state
        except WaterCrystConnectionError as err:
            _LOGGER.error("Error communicating with WaterCryst API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except WaterCrystAPIError as err:
            # For setup phase, treat API errors as potentially transient
            if "empty response" in str(err).lower():
                _LOGGER.warning("Empty response from API, this may be transient: %s", err)
                raise UpdateFailed(f"API returned empty response (may be transient): {err}") from err
            else:
                _LOGGER.error("API error during state fetch: %s", err)
                raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error in state coordinator: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err


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
            _LOGGER.debug("Fetching measurements data from WaterCryst API")
            # Use direct measurements endpoint (newer devices)
            measurements = await self.client.get_measurements_direct()
            _LOGGER.debug("Successfully fetched direct measurements: %s", measurements)
            return measurements
        except WaterCrystConnectionError as err:
            _LOGGER.error("Error communicating with WaterCryst API (measurements): %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except WaterCrystAPIError as err:
            # For setup phase, treat API errors as potentially transient
            if "empty response" in str(err).lower():
                _LOGGER.warning("Empty response from measurements API, this may be transient: %s", err)
                raise UpdateFailed(f"Measurements API returned empty response (may be transient): {err}") from err
            else:
                _LOGGER.error("API error during measurements fetch: %s", err)
                raise UpdateFailed(f"Measurements API error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error in measurements coordinator: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err