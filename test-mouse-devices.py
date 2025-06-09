#!/usr/bin/env python3
"""
Test and debug mouse device detection for Screenshot LLM Assistant
"""

import sys
import os
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

try:
    import evdev
    from evdev import InputDevice, ecodes
    
    def list_all_devices():
        """List all available input devices"""
        print("🖱️  Available Input Devices:")
        print("=" * 60)
        
        devices = [InputDevice(path) for path in evdev.list_devices()]
        
        for i, device in enumerate(devices, 1):
            print(f"\n{i}. Device: {device.name}")
            print(f"   Path: {device.path}")
            
            # Check capabilities
            capabilities = device.capabilities()
            
            # Check for mouse buttons
            mouse_buttons = []
            if ecodes.EV_KEY in capabilities:
                keys = capabilities[ecodes.EV_KEY]
                
                if ecodes.BTN_LEFT in keys:
                    mouse_buttons.append("LEFT")
                if ecodes.BTN_RIGHT in keys:
                    mouse_buttons.append("RIGHT")
                if ecodes.BTN_MIDDLE in keys:
                    mouse_buttons.append("MIDDLE")
                if 272 in keys:  # Button 9
                    mouse_buttons.append("BUTTON_9")
                
                # Check for other buttons
                extra_buttons = []
                for btn_code in keys:
                    if btn_code >= 272 and btn_code <= 279:  # Mouse buttons range
                        extra_buttons.append(f"BTN_{btn_code}")
            
            if mouse_buttons:
                print(f"   Mouse buttons: {', '.join(mouse_buttons)}")
            if extra_buttons:
                print(f"   Extra buttons: {', '.join(extra_buttons)}")
            
            # Check for relative movement (mice have this)
            if ecodes.EV_REL in capabilities:
                print(f"   ✅ Has relative movement (likely a mouse)")
            
            # Check device type hints
            device_name_lower = device.name.lower()
            device_type_hints = []
            
            if 'mouse' in device_name_lower:
                device_type_hints.append("🖱️  MOUSE")
            if 'keyboard' in device_name_lower:
                device_type_hints.append("⌨️  KEYBOARD")
            if 'touchpad' in device_name_lower:
                device_type_hints.append("📱 TOUCHPAD")
            if 'rival' in device_name_lower:
                device_type_hints.append("🎮 RIVAL")
            
            if device_type_hints:
                print(f"   Type hints: {', '.join(device_type_hints)}")
    
    def test_mouse_listener():
        """Test the mouse listener detection logic with detailed scoring"""
        print("\n🔍 Testing Mouse Listener Detection:")
        print("=" * 60)
        
        from mouse_listener import MouseListener
        import logging
        
        # Enable debug logging to see scoring details
        logging.getLogger('mouse_listener').setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger('mouse_listener').addHandler(handler)
        
        # Create listener but don't start it
        listener = MouseListener(button_code=276)
        
        print("\n📊 Running device detection with scoring algorithm...")
        print("-" * 50)
        
        # Test device finding
        device = listener._find_mouse_device()
        
        print("-" * 50)
        
        if device:
            print(f"🎯 FINAL SELECTION: {device.name}")
            print(f"   📁 Path: {device.path}")
            
            # Check if it has the target button
            capabilities = device.capabilities()
            if ecodes.EV_KEY in capabilities:
                keys = capabilities[ecodes.EV_KEY]
                if 276 in keys:  # Button 9 (code 276)
                    print(f"   ✅ Has target button 9 (code 276)")
                else:
                    print(f"   ❌ Does not have target button 9 (code 276)")
                    print(f"   Available mouse buttons: {[k for k in keys if k >= 272 and k <= 279]}")
                
                # Show all mouse buttons for reference
                mouse_buttons = []
                button_names = {
                    272: "BTN_LEFT", 273: "BTN_RIGHT", 274: "BTN_MIDDLE",
                    275: "BTN_SIDE", 276: "BTN_EXTRA", 277: "BTN_FORWARD",
                    278: "BTN_BACK", 279: "BTN_TASK"
                }
                for code in keys:
                    if 272 <= code <= 279:
                        name = button_names.get(code, f"BTN_{code}")
                        mouse_buttons.append(f"{name}({code})")
                
                if mouse_buttons:
                    print(f"   🖱️  All mouse buttons: {', '.join(mouse_buttons)}")
        else:
            print("❌ No suitable device found")
            print("\n💡 Try running with sudo if no devices are detected")
            print("   or check that your mouse is connected.")
    
    def main():
        print("🖱️  Screenshot LLM Assistant - Mouse Device Tester")
        print("=" * 60)
        
        try:
            list_all_devices()
            test_mouse_listener()
            
            print("\n💡 How to Fix Mouse Detection:")
            print("1. Identify the correct device path for your 'Rival 3' mouse from the list above.")
            print("   (It should be something like '/dev/input/eventX')")
            print("\n2. Open 'config/config.json' and add the 'mouse_device_path' setting:")
            print("""
   "mouse_device_path": "/dev/input/event9"
   """)
            print("   (Replace with the correct path for your mouse)")
            print("\n3. Restart the daemon ('python screenshot-llm.py'). It will now use the specified device.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nMake sure you have evdev installed: pip install evdev")
            print("You may also need to run with appropriate permissions.")
    
    if __name__ == "__main__":
        main()

except ImportError:
    print("❌ evdev module not found. Install with: pip install evdev")
    sys.exit(1)