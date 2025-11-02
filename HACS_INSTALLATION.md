# HACS Installation Guide

This document provides detailed instructions for installing the WaterCryst BIOCAT integration via HACS (Home Assistant Community Store).

## Prerequisites

1. **Home Assistant** (version 2023.4.0 or higher)
2. **HACS** installed and configured ([Installation Guide](https://hacs.xyz/docs/setup/download))
3. **WaterCryst API Key** from [app.watercryst.com](https://app.watercryst.com/)

## Installation Steps

### Step 1: Add Custom Repository (Temporary)

Until this integration is added to the default HACS repository:

1. Open Home Assistant and navigate to **HACS**
2. Click on **Integrations**
3. Click the **⋮** (three dots) menu in the top right corner
4. Select **Custom repositories**
5. Add the following information:
   - **Repository**: `https://github.com/YOUR_USERNAME/biocat`
   - **Category**: `Integration`
6. Click **Add**

### Step 2: Install the Integration

1. In HACS → Integrations, search for "WaterCryst BIOCAT"
2. Click on the integration when it appears
3. Click **Install**
4. Select the latest version
5. Click **Install** again
6. **Restart Home Assistant** when prompted

### Step 3: Configure the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "WaterCryst BIOCAT"
4. Click on it to start the configuration

### Step 4: Enter Your Credentials

1. **API Key**: Enter your WaterCryst API key
   - Get this from [app.watercryst.com](https://app.watercryst.com/)
   - Go to your device → REST API tab → Add
2. **Device Name**: Enter a friendly name (e.g., "Kitchen BIOCAT")
3. Click **Submit**

## Verification

After successful installation, you should see:

### Entities Created
- **11 Sensors**: Temperature, pressure, flow rate, consumption, etc.
- **7 Binary Sensors**: Online status, absence mode, leakage detection, etc.
- **3 Switches**: Absence mode, water supply, leakage protection
- **3 Buttons**: Self-test, microleakage test, acknowledge event

### Device Information
- Device appears in **Settings** → **Devices & Services** → **WaterCryst BIOCAT**
- All entities are properly named and functional
- Diagnostic information is available

## Troubleshooting

### Integration Not Found in HACS
- Ensure you added the custom repository correctly
- Check that the repository URL is correct
- Refresh HACS: **⋮** menu → **Reload**

### Installation Failed
- Check Home Assistant logs: **Settings** → **System** → **Logs**
- Ensure your Home Assistant version is supported (2023.4.0+)
- Try restarting Home Assistant and reinstalling

### Configuration Issues
- Verify your API key is correct and active
- Check that your BIOCAT device is online
- Ensure the device is properly configured in your WaterCryst account

### Entity Issues
- Some entities may not be available on older firmware versions
- Consumption data requires specific firmware versions:
  - KLS-C/KS-C: v01.03.01+
  - LS-C: v01.00.08+

## Updates

HACS will automatically notify you when updates are available:

1. Go to **HACS** → **Integrations**
2. Look for the update notification on "WaterCryst BIOCAT"
3. Click **Update**
4. Restart Home Assistant when prompted

## Getting Help

- **Integration Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/biocat/issues)
- **HACS Support**: [HACS Documentation](https://hacs.xyz/)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)
- **WaterCryst Device Support**: appservice@watercryst.com

## Advanced Configuration

For advanced automations and configurations, see:
- [README.md](README.md) - Complete documentation
- [examples/configuration.yaml](examples/configuration.yaml) - Example automations
- [Home Assistant Documentation](https://www.home-assistant.io/docs/) - General HA help