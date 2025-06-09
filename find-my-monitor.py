#!/usr/bin/env python3
"""
Run this in your GUI session to find your monitor outputs
"""

import subprocess
import tempfile
import os

def find_monitor_outputs():
    """Find available monitor outputs for grim"""
    print("🖥️  Finding your monitor outputs...")
    print("Run this in your GUI session (not SSH)")
    print("=" * 50)
    
    # Test if we can capture at all
    try:
        with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
            result = subprocess.run(['grim', tmp.name], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                size = os.path.getsize(tmp.name)
                print(f"✅ Full screen capture works ({size} bytes)")
                print("This is currently capturing ALL monitors")
            else:
                print(f"❌ grim failed: {result.stderr}")
                return
    except Exception as e:
        print(f"❌ Error testing grim: {e}")
        return
    
    # Try common output patterns
    output_patterns = [
        # COSMIC/modern patterns  
        "HDMI-A-1", "HDMI-A-2", "HDMI-A-3",
        "DP-1", "DP-2", "DP-3", "DP-4", "DP-5",
        "eDP-1",  # Laptop screen
        # Legacy patterns
        "HDMI1", "HDMI2", "HDMI3",
        "DVI1", "DVI2", "VGA1"
    ]
    
    print("\n🔍 Testing individual outputs...")
    working_outputs = []
    
    for output in output_patterns:
        try:
            with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
                result = subprocess.run(['grim', '-o', output, tmp.name], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    size = os.path.getsize(tmp.name)
                    working_outputs.append((output, size))
                    print(f"✅ {output} - Works ({size} bytes)")
                
        except subprocess.TimeoutExpired:
            print(f"⏱️  {output} - Timeout")
        except Exception as e:
            pass  # Silent fail for most
    
    print(f"\n📊 Summary:")
    print(f"Working outputs: {[out[0] for out in working_outputs]}")
    
    if working_outputs:
        print(f"\n💡 To capture just one monitor, add this to your config.json:")
        print(f'   "screenshot_output": "{working_outputs[0][0]}"')
        print(f"\nOr change screenshot_mode to 'active_window' for just the current window")
    else:
        print("No individual outputs found. You may need to use 'active_window' mode.")

if __name__ == "__main__":
    find_monitor_outputs()