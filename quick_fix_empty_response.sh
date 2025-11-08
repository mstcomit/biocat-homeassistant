#!/bin/bash

# Quick fix script for WaterCryst empty response issue
# This script applies a patch to make the Home Assistant config flow more tolerant

echo "Applying quick fix for WaterCryst empty response issue..."

CONFIG_FLOW_FILE="/config/custom_components/watercryst/config_flow.py"

if [[ ! -f "$CONFIG_FLOW_FILE" ]]; then
    echo "Error: $CONFIG_FLOW_FILE not found!"
    echo "Make sure the WaterCryst integration is installed in your Home Assistant."
    exit 1
fi

# Create backup
cp "$CONFIG_FLOW_FILE" "${CONFIG_FLOW_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "Created backup: ${CONFIG_FLOW_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Apply the patch
cat > /tmp/config_flow_patch.py << 'EOF'
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

# Extract the function from current file and replace it
python3 << 'EOF'
import re
import sys

# Read the current file
with open('/config/custom_components/watercryst/config_flow.py', 'r') as f:
    content = f.read()

# Read the new function
with open('/tmp/config_flow_patch.py', 'r') as f:
    new_function = f.read()

# Replace the validate_input function
pattern = r'async def validate_input\(.*?\n    finally:\n        await client\.close\(\)'
new_content = re.sub(pattern, new_function.strip(), content, flags=re.DOTALL)

# Write back the file
with open('/config/custom_components/watercryst/config_flow.py', 'w') as f:
    f.write(new_content)

print("Config flow patched successfully!")
EOF

if [[ $? -eq 0 ]]; then
    echo "✅ Quick fix applied successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Restart Home Assistant"
    echo "2. Try adding the WaterCryst integration again"
    echo "3. If you still have issues, run: python3 troubleshoot_empty_responses.py <YOUR_API_KEY>"
    echo ""
    echo "The fix makes the integration more tolerant of empty API responses during setup."
    echo "This should allow you to complete the configuration even if some endpoints"
    echo "are temporarily unavailable or returning empty responses."
else
    echo "❌ Failed to apply quick fix!"
    echo "You may need to manually edit the config_flow.py file."
fi

# Clean up
rm -f /tmp/config_flow_patch.py