#!/usr/bin/env python3
"""
Test button events from the Rival 3 mouse to identify working button codes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

import evdev
from evdev import InputDevice, categorize, ecodes

async def test_rival3_buttons():
    """Test all button events from the Rival 3 mouse"""
    device_path = "/dev/input/event9"  # Your Rival 3
    
    try:
        device = InputDevice(device_path)
        print(f"Listening to: {device.name}")
        print(f"Path: {device.path}")
        print("\nPress any mouse buttons and we'll show the event codes...")
        print("Press Ctrl+C to stop\n")
        
        async for event in device.async_read_loop():
            if event.type == ecodes.EV_KEY:
                categorized = categorize(event)
                if hasattr(categorized, 'keycode'):
                    if event.value == 1:  # Button press (not release)
                        print(f"Button pressed: {categorized.keycode} (code: {event.code})")
                        
                        # Check if this is button 276
                        if event.code == 276:
                            print("  *** This is button 276 (BTN_EXTRA) - the one we want! ***")
                        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have permission to read input devices")
        print("Try: sudo usermod -a -G input $USER")
        print("Then log out and back in")

if __name__ == "__main__":
    try:
        asyncio.run(test_rival3_buttons())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Error: {e}")