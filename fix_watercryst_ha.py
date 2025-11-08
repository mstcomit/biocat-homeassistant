#!/usr/bin/env python3
"""
Direct fix for WaterCryst Home Assistant integration empty response issue.
Run this script on your Home Assistant system to apply the fix.
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

def find_config_flow_file():
    """Find the WaterCryst config_flow.py file in Home Assistant."""
    
    possible_paths = [
        "/config/custom_components/watercryst/config_flow.py",
        "/homeassistant/custom_components/watercryst/config_flow.py", 
        "/usr/share/hassio/homeassistant/custom_components/watercryst/config_flow.py",
        os.path.expanduser("~/.homeassistant/custom_components/watercryst/config_flow.py"),
        "/opt/homeassistant/custom_components/watercryst/config_flow.py",
    ]
    
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    
    return None

def backup_file(file_path):
    """Create a backup of the file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup.{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def apply_fix(file_path):
    """Apply the fix to the config_flow.py file."""
    
    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if fix is already applied
    if 'validation_endpoints' in content:
        print("✅ Fix appears to already be applied!")
        return True
    
    # The new validate_input function
    new_function = '''async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
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
        await client.close()'''
    
    # Find and replace the validate_input function
    pattern = r'async def validate_input\(.*?\n    finally:\n        await client\.close\(\)'
    new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    # Verify the replacement worked
    if 'validation_endpoints' not in new_content:
        print("❌ Failed to apply fix - function pattern not found")
        print("The validate_input function may have a different structure than expected.")
        return False
    
    # Write back the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    print("🔧 WaterCryst Home Assistant Integration Fix")
    print("=" * 50)
    
    # Find the config flow file
    config_flow_path = find_config_flow_file()
    
    if not config_flow_path:
        print("❌ Could not find WaterCryst integration config_flow.py")
        print("\nPlease ensure:")
        print("1. WaterCryst integration is installed in Home Assistant")
        print("2. You're running this script on the Home Assistant system")
        print("3. The integration is in custom_components/watercryst/")
        return 1
    
    print(f"✅ Found config_flow.py at: {config_flow_path}")
    
    # Check if we can write to the file
    if not os.access(config_flow_path, os.W_OK):
        print(f"❌ Cannot write to {config_flow_path}")
        print("Please run this script with appropriate permissions")
        print("Try: sudo python3 fix_watercryst_ha.py")
        return 1
    
    # Create backup
    try:
        backup_path = backup_file(config_flow_path)
        print(f"💾 Created backup: {backup_path}")
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return 1
    
    # Apply the fix
    try:
        if apply_fix(config_flow_path):
            print("✅ Fix applied successfully!")
            print()
            print("🔄 Next steps:")
            print("1. Restart Home Assistant")
            print("2. Go to Settings > Devices & Services > Add Integration")  
            print("3. Search for 'WaterCryst' and add it with your API key")
            print()
            print("The integration should now handle empty API responses gracefully.")
            return 0
        else:
            print("❌ Failed to apply fix")
            print(f"Restoring backup from: {backup_path}")
            shutil.copy2(backup_path, config_flow_path)
            return 1
            
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        print(f"Restoring backup from: {backup_path}")
        shutil.copy2(backup_path, config_flow_path)
        return 1

if __name__ == "__main__":
    exit(main())