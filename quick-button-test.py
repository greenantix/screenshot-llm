#!/usr/bin/env python3
"""
Quick test to see what button events your Rival 3 sends
Run this and press buttons on your mouse to see the codes
"""

import evdev
from evdev import InputDevice, ecodes

def test_buttons():
    device_path = "/dev/input/event9"
    
    try:
        device = InputDevice(device_path)
        print(f"Monitoring: {device.name}")
        print("Press mouse buttons - I'll show you the codes")
        print("Press Ctrl+C when done\n")
        
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:  # Button press
                button_names = {
                    272: "LEFT", 273: "RIGHT", 274: "MIDDLE",
                    275: "SIDE", 276: "EXTRA/FORWARD", 277: "BACK"
                }
                name = button_names.get(event.code, f"UNKNOWN_{event.code}")
                print(f"Button: {name} (code: {event.code})")
                
                if event.code == 276:
                    print("  ★ This is the button we need for screenshots!")
                    
    except PermissionError:
        print("Permission denied. You might need to run with sudo or be in input group")
    except FileNotFoundError:
        print(f"Device {device_path} not found")
    except KeyboardInterrupt:
        print("\nDone!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_buttons()