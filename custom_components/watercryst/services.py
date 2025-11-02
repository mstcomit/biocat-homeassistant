"""Services for WaterCryst BIOCAT integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .api import WaterCrystAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service schemas
PAUSE_LEAKAGE_PROTECTION_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): cv.entity_ids,
        vol.Required("minutes"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4320)),
    }
)

SERVICE_PAUSE_LEAKAGE_PROTECTION = "pause_leakage_protection"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for WaterCryst integration."""

    async def pause_leakage_protection(call: ServiceCall) -> None:
        """Handle pause leakage protection service call."""
        entity_ids = call.data["entity_id"]
        minutes = call.data["minutes"]

        for entity_id in entity_ids:
            # Find the integration entry for this entity
            for entry_id, entry_data in hass.data[DOMAIN].items():
                if entity_id.startswith(f"{DOMAIN}."):
                    client = entry_data["client"]
                    state_coordinator = entry_data["state_coordinator"]
                    
                    try:
                        await client.pause_leakage_protection(minutes)
                        await state_coordinator.async_request_refresh()
                        _LOGGER.info(
                            "Paused leakage protection for %d minutes via service call",
                            minutes
                        )
                    except WaterCrystAPIError as err:
                        _LOGGER.error(
                            "Failed to pause leakage protection via service: %s", err
                        )
                    break

    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_PAUSE_LEAKAGE_PROTECTION,
        pause_leakage_protection,
        schema=PAUSE_LEAKAGE_PROTECTION_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for WaterCryst integration."""
    hass.services.async_remove(DOMAIN, SERVICE_PAUSE_LEAKAGE_PROTECTION)