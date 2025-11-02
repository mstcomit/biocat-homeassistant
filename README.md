# WaterCryst BIOCAT Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

A comprehensive Home Assistant integration for WaterCryst BIOCAT water treatment and leakage protection systems. This integration provides complete control and monitoring of your BIOCAT device through the WaterCryst REST API.

## Features

### 🌊 Complete Device Monitoring
- Real-time water temperature, pressure, and flow rate monitoring
- Water consumption tracking (daily and total)
- Device operational status and mode tracking
- Microleakage detection and measurement state

### 🛡️ Advanced Protection Controls
- Absence mode activation/deactivation with enhanced sensitivity
- Leakage protection pause/unpause functionality
- Water supply control (open/close)
- Emergency shutoff capability

### 🔧 Maintenance and Testing
- Self-test initiation and monitoring
- Microleakage measurement testing
- Event acknowledgment for warnings and errors
- Comprehensive diagnostic information

### 📊 Rich Data and Automation
- Multiple sensor types for comprehensive monitoring
- Binary sensors for status monitoring and automation triggers
- Switch entities for easy control
- Button entities for one-click actions
- Service calls for advanced automation scenarios

## Installation

### HACS Installation (Recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed and configured
2. In the HACS panel, go to **Integrations**
3. Click the **⋮** menu in the top right corner and select **Custom repositories**
4. Add this repository URL: `https://github.com/mstcomit/biocat`
5. Select **Integration** as the category
6. Click **Add**
7. Find "WaterCryst BIOCAT" in the list and click **Install**
8. Restart Home Assistant
9. Add the integration through the UI (Configuration → Integrations → Add Integration → WaterCryst BIOCAT)

### Manual Installation

1. Copy the `watercryst` folder to your `custom_components` directory:
   ```
   config/
   └── custom_components/
       └── watercryst/
           ├── __init__.py
           ├── api.py
           ├── binary_sensor.py
           ├── button.py
           ├── config_flow.py
           ├── const.py
           ├── diagnostics.py
           ├── manifest.json
           ├── sensor.py
           ├── services.py
           ├── services.yaml
           ├── switch.py
           └── translations/
               └── en.json
   ```

2. Restart Home Assistant

3. Add the integration through the UI (Configuration → Integrations → Add Integration → WaterCryst BIOCAT)

### HACS Installation (Future)

Once this integration is published to the default HACS repository, it will be available directly through HACS without adding a custom repository.

## Configuration

### Initial Setup

1. Navigate to **Configuration** → **Integrations**
2. Click **Add Integration** and search for "WaterCryst BIOCAT"
3. Enter your API credentials:
   - **API Key**: Your WaterCryst API key (obtain from https://app.watercryst.com/)
   - **Device Name**: A friendly name for your device (default: "BIOCAT")

### Getting Your API Key

1. Log in to your WaterCryst account at https://app.watercryst.com/
2. Go to your device's detail view
3. Open the **REST API** tab
4. Click **Add** to generate an API key
5. Copy the generated API key for use in Home Assistant

## Entities

The integration creates multiple types of entities to provide comprehensive control and monitoring:

### Sensors

| Entity | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| `sensor.{device}_mode` | Current operation mode | - | - |
| `sensor.{device}_water_temperature` | Water temperature | °C | Temperature |
| `sensor.{device}_pressure` | Water pressure | bar | Pressure |
| `sensor.{device}_flow_rate` | Current flow rate | L/min | Volume Flow Rate |
| `sensor.{device}_last_tap_volume` | Last tap volume | L | Volume |
| `sensor.{device}_last_tap_duration` | Last tap duration | s | Duration |
| `sensor.{device}_daily_consumption` | Daily water consumption | L | Volume |
| `sensor.{device}_total_consumption` | Total consumption since installation | L | Volume |
| `sensor.{device}_microleakage_state` | Microleakage test state | - | - |
| `sensor.{device}_event_title` | Current event title | - | - |
| `sensor.{device}_event_description` | Current event description | - | - |

### Binary Sensors

| Entity | Description | Device Class |
|--------|-------------|--------------|
| `binary_sensor.{device}_online` | Device connectivity status | Connectivity |
| `binary_sensor.{device}_absence_mode` | Absence mode status | - |
| `binary_sensor.{device}_leakage_protection` | Leakage protection active status | - |
| `binary_sensor.{device}_water_supply` | Water supply status | - |
| `binary_sensor.{device}_error` | Error condition present | Problem |
| `binary_sensor.{device}_warning` | Warning condition present | Problem |
| `binary_sensor.{device}_microleakage_detected` | Microleakage detection status | Problem |

### Switches

| Entity | Description | Function |
|--------|-------------|----------|
| `switch.{device}_absence_mode` | Control absence mode | Enable/disable enhanced sensitivity |
| `switch.{device}_water_supply` | Control water supply | Open/close water supply |
| `switch.{device}_leakage_protection` | Control leakage protection | Pause/unpause (60 min default) |

### Buttons

| Entity | Description | Function |
|--------|-------------|----------|
| `button.{device}_self_test` | Start self test | Initiate 2-minute self test routine |
| `button.{device}_microleakage_test` | Start microleakage test | Test for micro-leaks in piping |
| `button.{device}_acknowledge_event` | Acknowledge current event | Clear current warning/error |

## Services

### `watercryst.pause_leakage_protection`

Pause leakage protection for a specific duration.

**Parameters:**
- `entity_id`: The WaterCryst device entity
- `minutes`: Duration to pause (1-4320 minutes)

**Example:**
```yaml
service: watercryst.pause_leakage_protection
data:
  entity_id: sensor.biocat_mode
  minutes: 120
```

## Device Modes

The device operates in various modes depending on its current state:

| Mode ID | Mode Name | Description |
|---------|-----------|-------------|
| SU | Start Up | Device initialization |
| WT | Water Treatment | Normal operation mode |
| TD | Thermal Disinfection | Automated disinfection cycle |
| RS | Rinse | Post-disinfection rinse cycle |
| ST | Self Test | Running self-test routine |
| UD | Firmware Update | Device updating firmware |
| FS | Failsafe | Safety mode |
| ER | Error Mode | Error condition present |
| WO | Water Off | Water supply disconnected |
| MC | Maintenance Cleaning | Maintenance mode |

## Microleakage States

| State | Description |
|-------|-------------|
| idle | No measurement active |
| running | Measurement in progress |
| success | No leakage detected |
| leakage | Leakage detected |
| cancelled | Measurement cancelled |
| failure-pressure-drop | Pressure dropped during test |
| failure-water-tap | Water tap opened during test |
| failure-start-pressure | Insufficient pressure to start |
| failure-unknown | Unknown test failure |

## Automation Examples

### Water Leak Alert

```yaml
automation:
  - alias: "Water Leak Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.biocat_microleakage_detected
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Water Leak Detected!"
          message: "Microleakage detected on BIOCAT system"
          data:
            priority: high

### Absence Mode Automation

```yaml
automation:
  - alias: "Enable Absence Mode When Away"
    trigger:
      - platform: state
        entity_id: alarm_control_panel.home
        to: "armed_away"
    action:
      - service: switch.turn_on
        entity_id: switch.biocat_absence_mode

  - alias: "Disable Absence Mode When Home"
    trigger:
      - platform: state
        entity_id: alarm_control_panel.home
        to: "disarmed"
    action:
      - service: switch.turn_off
        entity_id: switch.biocat_absence_mode
```

### Daily Consumption Tracking

```yaml
automation:
  - alias: "Daily Water Consumption Report"
    trigger:
      - platform: time
        at: "23:59:00"
    action:
      - service: notify.email
        data:
          title: "Daily Water Consumption"
          message: >
            Today's water consumption: {{ states('sensor.biocat_daily_consumption') }} L
            Total consumption: {{ states('sensor.biocat_total_consumption') }} L
```

## Troubleshooting

### Common Issues

1. **API Key Authentication Failed**
   - Verify your API key is correct
   - Ensure the key was generated from https://app.watercryst.com/
   - Check that the API endpoint is enabled for your device

2. **Device Shows Offline**
   - Check your device's internet connection
   - Verify the device is powered on
   - Confirm the device is properly registered in your WaterCryst account

3. **Missing Consumption Data**
   - Consumption data is only available on newer firmware versions
   - KLS-C and KS-C devices need firmware v01.03.01+
   - LS-C devices need firmware v01.00.08+

4. **Rate Limit Errors**
   - The API has limits: 10 requests/second, 200 requests/15 minutes
   - Reduce update frequency if experiencing rate limits
   - Multiple Home Assistant instances with same API key can cause issues

### API Limitations

- Maximum 10 requests per second per customer and device
- Maximum 200 requests within 15 minutes
- Some features require specific firmware versions
- Webhook functionality requires external URL configuration

## Support

For issues with this integration:
- Check the Home Assistant logs for detailed error messages
- Verify your API key and device connectivity
- Ensure your device firmware is up to date

For WaterCryst device issues:
- Contact WaterCryst support: appservice@watercryst.com
- Visit: https://www.watercryst.com/

## License

This integration is licensed under the Apache 2.0 License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Links

- [WaterCryst Official Website](https://www.watercryst.com/)
- [WaterCryst App Portal](https://app.watercryst.com/)
- [Home Assistant Community](https://community.home-assistant.io/)

***

[releases-shield]: https://img.shields.io/github/release/mstcomit/biocat.svg?style=for-the-badge
[releases]: https://github.com/mstcomit/biocat/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/mstcomit/biocat.svg?style=for-the-badge
[commits]: https://github.com/mstcomit/biocat/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/mstcomit/biocat.svg?style=for-the-badge