"""Diagnostics support for WaterCryst BIOCAT integration."""
from __future__ import annotations

from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> Dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    state_coordinator = data["state_coordinator"]
    measurements_coordinator = data["measurements_coordinator"]

    diagnostics = {
        "config_entry": {
            "title": config_entry.title,
            "version": config_entry.version,
            "domain": config_entry.domain,
            "unique_id": config_entry.unique_id,
        },
        "coordinators": {
            "state": {
                "last_update_success": state_coordinator.last_update_success,
                "last_exception": str(state_coordinator.last_exception) if state_coordinator.last_exception else None,
                "update_interval": str(state_coordinator.update_interval),
                "data": state_coordinator.data,
            },
            "measurements": {
                "last_update_success": measurements_coordinator.last_update_success,
                "last_exception": str(measurements_coordinator.last_exception) if measurements_coordinator.last_exception else None,
                "update_interval": str(measurements_coordinator.update_interval),
                "data": measurements_coordinator.data,
            },
        },
    }

    return diagnostics