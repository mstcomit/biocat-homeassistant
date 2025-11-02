"""Button platform for WaterCryst BIOCAT integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WaterCrystClient, WaterCrystAPIError
from .const import (
    CONF_DEVICE_NAME,
    DOMAIN,
    ICON_ACK_EVENT,
    ICON_MICROLEAKAGE,
    ICON_SELF_TEST,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WaterCryst buttons based on a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    state_coordinator = data["state_coordinator"]
    client = data["client"]
    device_name = config_entry.data[CONF_DEVICE_NAME]

    entities = [
        WaterCrystSelfTestButton(state_coordinator, client, device_name),
        WaterCrystMicroleakageTestButton(state_coordinator, client, device_name),
        WaterCrystAcknowledgeEventButton(state_coordinator, client, device_name),
    ]

    async_add_entities(entities)


class WaterCrystButtonEntity(CoordinatorEntity, ButtonEntity):
    """Base WaterCryst button entity."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str, button_type: str):
        """Initialize the button."""
        super().__init__(coordinator)
        self._client = client
        self._device_name = device_name
        self._button_type = button_type
        self._attr_unique_id = f"{device_name}_{button_type}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_name)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )


class WaterCrystSelfTestButton(WaterCrystButtonEntity):
    """Button for starting self test."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the self test button."""
        super().__init__(coordinator, client, device_name, "self_test")
        self._attr_name = f"{device_name} Self Test"
        self._attr_icon = ICON_SELF_TEST

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self._client.start_self_test()
            _LOGGER.info("Self test started for %s", self._device_name)
            # Request an immediate update to reflect the new state
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to start self test: %s", err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only allow self test if device is online and not in error mode
        if not super().available:
            return False
        
        mode = self.coordinator.data.get("mode", {})
        online = self.coordinator.data.get("online", False)
        
        # Don't allow self test if already running, in error mode, or offline
        return (
            online 
            and mode.get("id") not in ["ST", "ER", "UD", "FS"]
        )


class WaterCrystMicroleakageTestButton(WaterCrystButtonEntity):
    """Button for starting microleakage measurement."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the microleakage test button."""
        super().__init__(coordinator, client, device_name, "microleakage_test")
        self._attr_name = f"{device_name} Microleakage Test"
        self._attr_icon = ICON_MICROLEAKAGE

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self._client.start_microleakage_measurement()
            _LOGGER.info("Microleakage measurement started for %s", self._device_name)
            # Request an immediate update to reflect the new state
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to start microleakage measurement: %s", err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only allow microleakage test if device is online and not already testing
        if not super().available:
            return False
        
        mode = self.coordinator.data.get("mode", {})
        online = self.coordinator.data.get("online", False)
        ml_state = self.coordinator.data.get("mlState", "idle")
        
        # Don't allow test if already running, in error mode, offline, or ml test is running
        return (
            online 
            and mode.get("id") not in ["ST", "ER", "UD", "FS", "WO"]
            and ml_state not in ["running"]
        )


class WaterCrystAcknowledgeEventButton(WaterCrystButtonEntity):
    """Button for acknowledging current event."""

    def __init__(self, coordinator, client: WaterCrystClient, device_name: str):
        """Initialize the acknowledge event button."""
        super().__init__(coordinator, client, device_name, "acknowledge_event")
        self._attr_name = f"{device_name} Acknowledge Event"
        self._attr_icon = ICON_ACK_EVENT

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self._client.acknowledge_event()
            _LOGGER.info("Event acknowledged for %s", self._device_name)
            # Request an immediate update to reflect the new state
            await self.coordinator.async_request_refresh()
        except WaterCrystAPIError as err:
            _LOGGER.error("Failed to acknowledge event: %s", err)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only show this button if there's an active event to acknowledge
        if not super().available:
            return False
        
        event = self.coordinator.data.get("event", {})
        online = self.coordinator.data.get("online", False)
        
        # Only available if there's an event and device is online
        return (
            online 
            and bool(event.get("eventId"))
            and event.get("category") in ["error", "warning"]
        )

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        event = self.coordinator.data.get("event", {})
        return {
            "event_id": event.get("eventId"),
            "event_category": event.get("category"),
            "event_title": event.get("title"),
            "event_description": event.get("description"),
            "event_timestamp": event.get("timestamp"),
        }