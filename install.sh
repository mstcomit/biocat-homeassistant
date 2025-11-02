#!/bin/bash

# WaterCryst BIOCAT Home Assistant Integration Installation Script
# This script will copy the integration files to your Home Assistant custom_components directory

set -e

# Default Home Assistant config directory
HA_CONFIG_DIR="${HOME}/.homeassistant"

# Check if a custom config directory was provided
if [ $# -eq 1 ]; then
    HA_CONFIG_DIR="$1"
fi

# Verify Home Assistant config directory exists
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo "❌ Home Assistant config directory not found: $HA_CONFIG_DIR"
    echo "Usage: $0 [/path/to/homeassistant/config]"
    exit 1
fi

echo "📁 Using Home Assistant config directory: $HA_CONFIG_DIR"

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
mkdir -p "$CUSTOM_COMPONENTS_DIR"

# Create watercryst integration directory
INTEGRATION_DIR="$CUSTOM_COMPONENTS_DIR/watercryst"
mkdir -p "$INTEGRATION_DIR"
mkdir -p "$INTEGRATION_DIR/translations"

echo "📦 Installing WaterCryst BIOCAT integration..."

# Copy integration files
cp custom_components/watercryst/*.py "$INTEGRATION_DIR/"
cp custom_components/watercryst/*.json "$INTEGRATION_DIR/"
cp custom_components/watercryst/*.yaml "$INTEGRATION_DIR/"
cp custom_components/watercryst/translations/*.json "$INTEGRATION_DIR/translations/"

echo "✅ Integration files installed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Configuration → Integrations"
echo "3. Click 'Add Integration' and search for 'WaterCryst BIOCAT'"
echo "4. Enter your API key from https://app.watercryst.com/"
echo ""
echo "📖 For detailed setup instructions, see README.md"
echo "💡 Example configurations are available in examples/configuration.yaml"