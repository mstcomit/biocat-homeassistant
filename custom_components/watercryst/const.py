"""Constants for the WaterCryst BIOCAT integration."""

DOMAIN = "watercryst"

# Configuration
CONF_API_KEY = "api_key"
CONF_DEVICE_NAME = "device_name"

# Update intervals
UPDATE_INTERVAL = 60  # seconds
MEASUREMENTS_UPDATE_INTERVAL = 30  # seconds

# Device information
MANUFACTURER = "WaterCryst Wassertechnik GmbH"
MODEL = "BIOCAT"

# Entity types
PLATFORMS = ["sensor", "binary_sensor", "switch", "button"]

# Icons
ICON_WATER_TEMP = "mdi:thermometer"
ICON_PRESSURE = "mdi:gauge"
ICON_FLOW_RATE = "mdi:water-pump"
ICON_CONSUMPTION = "mdi:water"
ICON_ONLINE = "mdi:cloud-check"
ICON_OFFLINE = "mdi:cloud-off"
ICON_ABSENCE_MODE = "mdi:home-minus"
ICON_WATER_SUPPLY = "mdi:water-boiler"
ICON_LEAKAGE_PROTECTION = "mdi:shield-check"
ICON_SELF_TEST = "mdi:test-tube"
ICON_MICROLEAKAGE = "mdi:magnify"
ICON_ACK_EVENT = "mdi:check-circle"

# Device classes
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_PRESSURE = "pressure"
DEVICE_CLASS_VOLUME = "volume"
DEVICE_CLASS_VOLUME_FLOW_RATE = "volume_flow_rate"
DEVICE_CLASS_DURATION = "duration"

# Units
UNIT_CELSIUS = "°C"
UNIT_BAR = "bar"
UNIT_LITERS = "L"
UNIT_LITERS_PER_MINUTE = "L/min"
UNIT_SECONDS = "s"

# State classes
STATE_CLASS_MEASUREMENT = "measurement"
STATE_CLASS_TOTAL_INCREASING = "total_increasing"