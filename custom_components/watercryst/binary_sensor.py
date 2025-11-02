"""Binary sensor platform for WaterCryst BIOCAT integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WaterCrystClient
from .const import (
    CONF_DEVICE_NAME,
    DOMAIN,
    ICON_ABSENCE_MODE,
    ICON_LEAKAGE_PROTECTION,
    ICON_OFFLINE,
    ICON_ONLINE,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WaterCryst binary sensors based on a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    state_coordinator = data["state_coordinator"]
    device_name = config_entry.data[CONF_DEVICE_NAME]

    entities = [
        WaterCrystOnlineBinarySensor(state_coordinator, device_name),
        WaterCrystAbsenceModeBinarySensor(state_coordinator, device_name),
        WaterCrystLeakageProtectionBinarySensor(state_coordinator, device_name),
        WaterCrystWaterSupplyBinarySensor(state_coordinator, device_name),
        WaterCrystErrorBinarySensor(state_coordinator, device_name),
        WaterCrystWarningBinarySensor(state_coordinator, device_name),
        WaterCrystMicroleakageDetectedBinarySensor(state_coordinator, device_name),
    ]

    async_add_entities(entities)


class WaterCrystBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Base WaterCryst binary sensor entity."""

    def __init__(self, coordinator, device_name: str, sensor_type: str):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_name = device_name
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{device_name}_{sensor_type}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_name)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )


class WaterCrystOnlineBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for device online status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the online status sensor."""
        super().__init__(coordinator, device_name, "online")
        self._attr_name = f"{device_name} Online"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the device is online."""
        return self.coordinator.data.get("online", False)

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return ICON_ONLINE if self.is_on else ICON_OFFLINE


class WaterCrystAbsenceModeBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for absence mode status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the absence mode sensor."""
        super().__init__(coordinator, device_name, "absence_mode")
        self._attr_name = f"{device_name} Absence Mode"
        self._attr_icon = ICON_ABSENCE_MODE

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if absence mode is enabled."""
        water_protection = self.coordinator.data.get("waterProtection", {})
        return water_protection.get("absenceModeEnabled", False)


class WaterCrystLeakageProtectionBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for leakage protection status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the leakage protection sensor."""
        super().__init__(coordinator, device_name, "leakage_protection")
        self._attr_name = f"{device_name} Leakage Protection"
        self._attr_icon = ICON_LEAKAGE_PROTECTION

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


class WaterCrystWaterSupplyBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for water supply status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the water supply sensor."""
        super().__init__(coordinator, device_name, "water_supply")
        self._attr_name = f"{device_name} Water Supply"
        self._attr_icon = "mdi:water-pump"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if water supply is open."""
        mode = self.coordinator.data.get("mode", {})
        # Water supply is off if mode is "WO" (Water Off)
        return mode.get("id") != "WO"


class WaterCrystErrorBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for error status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the error status sensor."""
        super().__init__(coordinator, device_name, "error")
        self._attr_name = f"{device_name} Error"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:alert-circle"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if there is an error."""
        event = self.coordinator.data.get("event", {})
        return event.get("category") == "error"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        event = self.coordinator.data.get("event", {})
        if event.get("category") == "error":
            return {
                "event_id": event.get("eventId"),
                "title": event.get("title"),
                "description": event.get("description"),
                "timestamp": event.get("timestamp"),
            }
        return {}


class WaterCrystWarningBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for warning status."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the warning status sensor."""
        super().__init__(coordinator, device_name, "warning")
        self._attr_name = f"{device_name} Warning"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:alert"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if there is a warning."""
        event = self.coordinator.data.get("event", {})
        return event.get("category") == "warning"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        event = self.coordinator.data.get("event", {})
        if event.get("category") == "warning":
            return {
                "event_id": event.get("eventId"),
                "title": event.get("title"),
                "description": event.get("description"),
                "timestamp": event.get("timestamp"),
            }
        return {}


class WaterCrystMicroleakageDetectedBinarySensor(WaterCrystBinarySensorEntity):
    """Binary sensor for microleakage detection."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the microleakage detection sensor."""
        super().__init__(coordinator, device_name, "microleakage_detected")
        self._attr_name = f"{device_name} Microleakage Detected"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:leak"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if microleakage is detected."""
        ml_state = self.coordinator.data.get("mlState")
        return ml_state == "leakage"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        ml_state = self.coordinator.data.get("mlState")
        return {
            "ml_state": ml_state,
            "ml_state_name": WaterCrystClient.get_ml_state_name(ml_state) if ml_state else None,
        }