"""Sensor platform for WaterCryst BIOCAT integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime, UnitOfVolume, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WaterCrystClient
from .const import (
    CONF_DEVICE_NAME,
    DEVICE_CLASS_PRESSURE,
    DOMAIN,
    ICON_CONSUMPTION,
    ICON_FLOW_RATE,
    ICON_PRESSURE,
    ICON_WATER_TEMP,
    MANUFACTURER,
    MODEL,
    UNIT_BAR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WaterCryst sensor based on a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    state_coordinator = data["state_coordinator"]
    measurements_coordinator = data["measurements_coordinator"]
    device_name = config_entry.data[CONF_DEVICE_NAME]

    entities = [
        # Device mode and status
        WaterCrystModeSensor(state_coordinator, device_name),
        WaterCrystMicroleakageStateSensor(state_coordinator, device_name),
        
        # Measurements
        WaterCrystTemperatureSensor(measurements_coordinator, device_name),
        WaterCrystPressureSensor(measurements_coordinator, device_name),
        WaterCrystFlowRateSensor(measurements_coordinator, device_name),
        WaterCrystLastTapVolumeSensor(measurements_coordinator, device_name),
        WaterCrystLastTapDurationSensor(measurements_coordinator, device_name),
        
        # Consumption statistics
        WaterCrystDailyConsumptionSensor(state_coordinator, device_name),
        WaterCrystTotalConsumptionSensor(state_coordinator, device_name),
        
        # Event information
        WaterCrystEventTitleSensor(state_coordinator, device_name),
        WaterCrystEventDescriptionSensor(state_coordinator, device_name),
    ]

    async_add_entities(entities)


class WaterCrystSensorEntity(CoordinatorEntity, SensorEntity):
    """Base WaterCryst sensor entity."""

    def __init__(self, coordinator, device_name: str, sensor_type: str):
        """Initialize the sensor."""
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


class WaterCrystModeSensor(WaterCrystSensorEntity):
    """Sensor for device operation mode."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the mode sensor."""
        super().__init__(coordinator, device_name, "mode")
        self._attr_name = f"{device_name} Mode"
        self._attr_icon = "mdi:state-machine"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        mode = self.coordinator.data.get("mode", {})
        return mode.get("name", mode.get("id"))


class WaterCrystMicroleakageStateSensor(WaterCrystSensorEntity):
    """Sensor for microleakage measurement state."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the microleakage state sensor."""
        super().__init__(coordinator, device_name, "ml_state")
        self._attr_name = f"{device_name} Microleakage State"
        self._attr_icon = "mdi:magnify"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        ml_state = self.coordinator.data.get("mlState")
        if ml_state:
            return WaterCrystClient.get_ml_state_name(ml_state)
        return None


class WaterCrystTemperatureSensor(WaterCrystSensorEntity):
    """Sensor for water temperature."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device_name, "water_temperature")
        self._attr_name = f"{device_name} Water Temperature"
        self._attr_icon = ICON_WATER_TEMP
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("waterTemp")


class WaterCrystPressureSensor(WaterCrystSensorEntity):
    """Sensor for water pressure."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the pressure sensor."""
        super().__init__(coordinator, device_name, "pressure")
        self._attr_name = f"{device_name} Pressure"
        self._attr_icon = ICON_PRESSURE
        self._attr_device_class = SensorDeviceClass.PRESSURE
        self._attr_native_unit_of_measurement = UNIT_BAR
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("pressure")


class WaterCrystFlowRateSensor(WaterCrystSensorEntity):
    """Sensor for water flow rate."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the flow rate sensor."""
        super().__init__(coordinator, device_name, "flow_rate")
        self._attr_name = f"{device_name} Flow Rate"
        self._attr_icon = ICON_FLOW_RATE
        self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.LITERS_PER_MINUTE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("flowRate")


class WaterCrystLastTapVolumeSensor(WaterCrystSensorEntity):
    """Sensor for last water tap volume."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the last tap volume sensor."""
        super().__init__(coordinator, device_name, "last_tap_volume")
        self._attr_name = f"{device_name} Last Tap Volume"
        self._attr_icon = ICON_CONSUMPTION
        self._attr_device_class = SensorDeviceClass.VOLUME
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
        # No state class for instantaneous volume measurements

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("lastWaterTapVolume")


class WaterCrystLastTapDurationSensor(WaterCrystSensorEntity):
    """Sensor for last water tap duration."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the last tap duration sensor."""
        super().__init__(coordinator, device_name, "last_tap_duration")
        self._attr_name = f"{device_name} Last Tap Duration"
        self._attr_icon = "mdi:timer"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("lastWaterTapDuration")


class WaterCrystDailyConsumptionSensor(WaterCrystSensorEntity):
    """Sensor for daily water consumption."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the daily consumption sensor."""
        super().__init__(coordinator, device_name, "daily_consumption")
        self._attr_name = f"{device_name} Daily Consumption"
        self._attr_icon = ICON_CONSUMPTION
        self._attr_device_class = SensorDeviceClass.VOLUME
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("daily_consumption")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available 
            and self.coordinator.data.get("daily_consumption") is not None
        )


class WaterCrystTotalConsumptionSensor(WaterCrystSensorEntity):
    """Sensor for total water consumption."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the total consumption sensor."""
        super().__init__(coordinator, device_name, "total_consumption")
        self._attr_name = f"{device_name} Total Consumption"
        self._attr_icon = ICON_CONSUMPTION
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        return self.coordinator.data.get("total_consumption")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available 
            and self.coordinator.data.get("total_consumption") is not None
        )


class WaterCrystEventTitleSensor(WaterCrystSensorEntity):
    """Sensor for current event title."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the event title sensor."""
        super().__init__(coordinator, device_name, "event_title")
        self._attr_name = f"{device_name} Event Title"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        event = self.coordinator.data.get("event", {})
        return event.get("title")

    @property
    def icon(self) -> str:
        """Return the icon based on event category."""
        event = self.coordinator.data.get("event", {})
        category = event.get("category", "info")
        return WaterCrystClient.get_event_category_icon(category)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        event = self.coordinator.data.get("event", {})
        return {
            "event_id": event.get("eventId"),
            "category": event.get("category"),
            "description": event.get("description"),
            "timestamp": event.get("timestamp"),
        }


class WaterCrystEventDescriptionSensor(WaterCrystSensorEntity):
    """Sensor for current event description."""

    def __init__(self, coordinator, device_name: str):
        """Initialize the event description sensor."""
        super().__init__(coordinator, device_name, "event_description")
        self._attr_name = f"{device_name} Event Description"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        event = self.coordinator.data.get("event", {})
        return event.get("description")

    @property
    def icon(self) -> str:
        """Return the icon based on event category."""
        event = self.coordinator.data.get("event", {})
        category = event.get("category", "info")
        return WaterCrystClient.get_event_category_icon(category)