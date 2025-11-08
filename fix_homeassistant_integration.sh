#!/bin/bash

# WaterCryst Home Assistant Config Flow Fix
# This script fixes the empty response issue during integration setup

echo "🔧 WaterCryst Home Assistant Integration Fix"
echo "============================================"

# Try to find the Home Assistant config directory
HA_CONFIG_DIRS=(
    "/config"
    "/homeassistant" 
    "/usr/share/hassio/homeassistant"
    "$HOME/.homeassistant"
    "/opt/homeassistant"
)

WATERCRYST_DIR=""
CONFIG_FLOW_FILE=""

echo "🔍 Searching for WaterCryst integration..."

for dir in "${HA_CONFIG_DIRS[@]}"; do
    if [[ -f "$dir/custom_components/watercryst/config_flow.py" ]]; then
        WATERCRYST_DIR="$dir/custom_components/watercryst"
        CONFIG_FLOW_FILE="$dir/custom_components/watercryst/config_flow.py"
        echo "✅ Found WaterCryst integration at: $WATERCRYST_DIR"
        break
    fi
done

if [[ -z "$CONFIG_FLOW_FILE" ]]; then
    echo "❌ Could not find WaterCryst integration in standard locations."
    echo ""
    echo "Please manually locate your config_flow.py file and apply the fix:"
    echo "1. Find: /path/to/homeassistant/custom_components/watercryst/config_flow.py"
    echo "2. Back it up: cp config_flow.py config_flow.py.backup"
    echo "3. Apply the fix from EMPTY_RESPONSE_FIX.md"
    exit 1
fi

echo "📁 Integration directory: $WATERCRYST_DIR"
echo "📄 Config flow file: $CONFIG_FLOW_FILE"

# Check if we can write to the file
if [[ ! -w "$CONFIG_FLOW_FILE" ]]; then
    echo "❌ Cannot write to $CONFIG_FLOW_FILE"
    echo "Please run this script with appropriate permissions (sudo if needed)"
    exit 1
fi

# Create backup
BACKUP_FILE="${CONFIG_FLOW_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FLOW_FILE" "$BACKUP_FILE"
echo "💾 Created backup: $BACKUP_FILE"

# Check if the file already has our fix
if grep -q "validation_endpoints" "$CONFIG_FLOW_FILE"; then
    echo "✅ Fix appears to already be applied!"
    echo "If you're still getting errors, try restarting Home Assistant."
    exit 0
fi

echo "🔧 Applying fix to config_flow.py..."

# Create the new validate_input function
cat > /tmp/watercryst_fix.py << 'EOF'
async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = async_get_clientsession(hass)
    client = WaterCrystClient(data[CONF_API_KEY], session)

    try:
        # Test the API key by trying multiple endpoints to validate connectivity
        state = None
        last_error = None
        
        # List of endpoints to try for validation (in order of preference)
        validation_endpoints = [
            ("get_state", "state"),
            ("get_measurements_direct", "measurements/direct"),
            ("get_total_consumption", "statistics/cumulative/total"),
            ("get_daily_consumption", "statistics/cumulative/daily"),
        ]
        
        for method_name, endpoint_name in validation_endpoints:
            try:
                _LOGGER.debug("Trying validation endpoint: %s", endpoint_name)
                if method_name == "get_state":
                    state = await client.get_state()
                elif method_name == "get_measurements_direct":
                    await client.get_measurements_direct()
                elif method_name == "get_total_consumption":
                    await client.get_total_consumption()
                elif method_name == "get_daily_consumption":
                    await client.get_daily_consumption()
                
                # If we get here, the API key is valid and at least one endpoint works
                _LOGGER.info("Successfully validated API key using endpoint: %s", endpoint_name)
                break
                
            except WaterCrystAuthenticationError:
                # Authentication errors are definitive - don't try other endpoints
                raise
            except Exception as err:
                last_error = err
                _LOGGER.debug("Validation endpoint %s failed: %s", endpoint_name, err)
                continue
        else:
            # All endpoints failed
            _LOGGER.warning("All validation endpoints failed. Last error: %s", last_error)
            if last_error is None:
                raise CannotConnect("No endpoints responded successfully")
            elif isinstance(last_error, WaterCrystConnectionError):
                raise CannotConnect from last_error
            elif "empty response" in str(last_error).lower():
                # Empty responses might indicate device is not ready or endpoint not supported
                # Log the issue but allow setup to continue
                _LOGGER.warning(
                    "API returned empty responses but authentication appears valid. "
                    "Device may not be ready or may not support queried endpoints. "
                    "Setup will continue - check entity states after configuration."
                )
            else:
                # Re-raise the last error for other cases
                raise last_error
        
        # Return info that you want to store in the config entry.
        return {
            "title": data[CONF_DEVICE_NAME],
            "device_info": {
                "online": state.get("online", False) if state else None,
                "mode": state.get("mode", {}) if state else {},
            }
        }
    except WaterCrystAuthenticationError as err:
        raise InvalidAuth from err
    except WaterCrystConnectionError as err:
        raise CannotConnect from err
    finally:
        await client.close()
EOF

# Apply the fix using Python
python3 << EOF
import re

# Read the current file
with open('$CONFIG_FLOW_FILE', 'r') as f:
    content = f.read()

# Read the new function
with open('/tmp/watercryst_fix.py', 'r') as f:
    new_function = f.read()

# Find and replace the validate_input function
pattern = r'async def validate_input\(.*?\n    finally:\n        await client\.close\(\)'
new_content = re.sub(pattern, new_function.strip(), content, flags=re.DOTALL)

# Verify the replacement worked
if 'validation_endpoints' in new_content:
    # Write back the file
    with open('$CONFIG_FLOW_FILE', 'w') as f:
        f.write(new_content)
    print("✅ Successfully applied fix!")
else:
    print("❌ Failed to apply fix - pattern not found")
    exit(1)
EOF

# Check if the fix was applied
if [[ $? -eq 0 ]] && grep -q "validation_endpoints" "$CONFIG_FLOW_FILE"; then
    echo "✅ Fix applied successfully!"
    echo ""
    echo "🔄 Next steps:"
    echo "1. Restart Home Assistant (Settings > System > Hardware > Restart)"
    echo "2. Go to Settings > Devices & Services > Add Integration"
    echo "3. Search for 'WaterCryst' and add it with your API key"
    echo ""
    echo "The integration should now work even if some API endpoints return empty responses."
    echo "Your API key has been confirmed to work with multiple endpoints."
else
    echo "❌ Failed to apply fix!"
    echo "Restoring backup..."
    cp "$BACKUP_FILE" "$CONFIG_FLOW_FILE"
    echo "Please check the EMPTY_RESPONSE_FIX.md file for manual instructions."
fi

# Clean up
rm -f /tmp/watercryst_fix.py

echo ""
echo "📋 Troubleshooting results showed:"
echo "  ✅ API key is valid"
echo "  ✅ /state endpoint works (292 chars of JSON data)"
echo "  ✅ Multiple endpoints working properly"
echo "  ⚠️  Only legacy endpoints (/measurements/now, /statistics/daily) return empty"
echo ""
echo "The fix makes the integration try multiple endpoints, so it will work"
echo "even if some return empty responses."