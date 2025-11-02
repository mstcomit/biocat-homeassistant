# WaterCryst BIOCAT Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

**This integration provides complete control and monitoring of WaterCryst BIOCAT water treatment and leakage protection systems through Home Assistant.**

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

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. In the HACS panel, go to "Integrations"
3. Click the "+" button in the bottom right
4. Search for "WaterCryst BIOCAT"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
2. If you do not have a `custom_components` directory (folder) there, you need to create it
3. In the `custom_components` directory (folder) create a new folder called `watercryst`
4. Download _all_ the files from the `custom_components/watercryst/` directory (folder) in this repository
5. Place the files you downloaded in the new directory (folder) you created
6. Restart Home Assistant

## Configuration

### Getting Your API Key

1. Log in to your WaterCryst account at [https://app.watercryst.com/](https://app.watercryst.com/)
2. Go to your device's detail view
3. Open the **REST API** tab
4. Click **Add** to generate an API key
5. Copy the generated API key for use in Home Assistant

### Setup in Home Assistant

1. In Home Assistant, go to **Configuration** → **Integrations**
2. Click **Add Integration** and search for "WaterCryst BIOCAT"
3. Enter your API key and device name
4. The integration will automatically discover and set up all available entities

## Entities Created

### Sensors (11 total)
- Water temperature, pressure, flow rate
- Daily and total water consumption
- Device mode and microleakage state
- Event information (title and description)

### Binary Sensors (7 total)
- Online status, absence mode, leakage protection
- Water supply status, error/warning states
- Microleakage detection

### Controls
- **Switches (3)**: Absence mode, water supply, leakage protection
- **Buttons (3)**: Self-test, microleakage test, event acknowledgment
- **Services (1)**: Advanced leakage protection pause

## Quick Start Automation Examples

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
          title: "🚨 Water Leak Detected!"
          message: "Microleakage detected by BIOCAT system"
```

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
```

## Supported Devices

- WaterCryst BIOCAT KLS-C series
- WaterCryst BIOCAT KS-C series  
- WaterCryst BIOCAT LS-C series

**Note**: Some features require specific firmware versions:
- Consumption data: KLS-C/KS-C v01.03.01+, LS-C v01.00.08+
- Direct measurements: KLS-C/KS-C v01.03.01+, LS-C v01.00.08+

## Support

- **Integration Issues**: [GitHub Issues](https://github.com/mstcomit/biocat/issues)
- **WaterCryst Device Support**: appservice@watercryst.com
- **Documentation**: [Full README](https://github.com/mstcomit/biocat/blob/main/README.md)

[commits-shield]: https://img.shields.io/github/commit-activity/y/mstcomit/biocat.svg?style=for-the-badge
[commits]: https://github.com/mstcomit/biocat/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/mstcomit/biocat.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/mstcomit/biocat.svg?style=for-the-badge
[releases]: https://github.com/mstcomit/biocat/releases