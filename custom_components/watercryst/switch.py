"""Switch platform for WaterCryst BIOCAT integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WaterCrystClient, WaterCrystAPIError
from .const import (
    CONF_DEVICE_NAME,
    DOMAIN,
    ICON_ABSENCE_MODE,
    ICON_WATER_SUPPLY,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WaterCryst switches based on a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    state_coordinator = data["state_coordinator"]
    client = data["client"]
    device_name = config_entry.data[CONF_DEVICE_NAME]

    entities = [
        WaterCrystAbsenceModeSwitch(state_coordinator, client, device_name),
        WaterCrystWaterSupplySwitch(state_coordinator, client, device_name),
    ]

    async_add_entities(entities)


class WaterCrystSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base WaterCryst switch entity."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str, switch_type: str):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._client = client
        self._device_name = device_name
        self._switch_type = switch_type
        self._attr_unique_id = f"{device_name}_{switch_type}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_name)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )


class WaterCrystAbsenceModeSwitch(WaterCrystSwitchEntity):
    """Switch for controlling absence mode."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the absence mode switch."""
        super().__init__(coordinator, client, device_name, "absence_mode")
        self._attr_name = f"{device_name} Absence Mode"
        self._attr_icon = ICON_ABSENCE_MODE

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if absence mode is enabled."""
        water_protection = self.coordinator.data.get("waterProtection", {})
        return water_protection.get("absenceModeEnabled", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on absence mode."""
        try:
            await self._client.enable_absence_mode()
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to enable absence mode: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off absence mode."""
        try:
            await self._client.disable_absence_mode()
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to disable absence mode: %s", err)


class WaterCrystWaterSupplySwitch(WaterCrystSwitchEntity):
    """Switch for controlling water supply."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the water supply switch."""
        super().__init__(coordinator, client, device_name, "water_supply")
        self._attr_name = f"{device_name} Water Supply"
        self._attr_icon = ICON_WATER_SUPPLY

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if water supply is open."""
        mode = self.coordinator.data.get("mode", {})
        # Water supply is off if mode is "WO" (Water Off)
        return mode.get("id") != "WO"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Open water supply."""
        try:
            await self._client.open_water_supply()
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to open water supply: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Close water supply."""
        try:
            await self._client.close_water_supply()
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to close water supply: %s", err)


class WaterCrystLeakageProtectionSwitch(WaterCrystSwitchEntity):
    """Switch for controlling leakage protection (pause/unpause)."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the leakage protection switch."""
        super().__init__(coordinator, client, device_name, "leakage_protection")
        self._attr_name = f"{device_name} Leakage Protection"
        self._attr_icon = "mdi:shield-check"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if leakage protection is active."""
        water_protection = self.coordinator.data.get("waterProtection", {})
        pause_until = water_protection.get("pauseLeakageProtectionUntilUTC")
        
        if not pause_until:
            return True  # Active if no pause time set
        
        # Check if pause time is in the past (protection is active)
        pause_datetime = WaterCrystClient.parse_datetime(pause_until)
        if pause_datetime:
            return datetime.now(pause_datetime.tzinfo) > pause_datetime
        
        return True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate leakage protection (unpause)."""
        try:
            await self._client.unpause_leakage_protection()
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to unpause leakage protection: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Pause leakage protection for 60 minutes."""
        try:
            # Default pause for 60 minutes when turned off
            await self._client.pause_leakage_protection(60)
            # Request an immediate update
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to pause leakage protection: %s", err)

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        water_protection = self.coordinator.data.get("waterProtection", {})
        pause_until = water_protection.get("pauseLeakageProtectionUntilUTC")
        
        attributes = {}
        if pause_until:
            attributes["paused_until"] = pause_until
            pause_datetime = WaterCrystClient.parse_datetime(pause_until)
            if pause_datetime:
                is_paused = datetime.now(pause_datetime.tzinfo) < pause_datetime
                attributes["is_paused"] = is_paused
        
        return attributes