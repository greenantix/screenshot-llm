#!/usr/bin/env python3
"""
Test available outputs for screenshot capture
"""

import subprocess
import tempfile
import os

def test_grim_outputs():
    """Test what outputs grim can capture"""
    print("Testing grim output capture capabilities...")
    
    # Try to get a list of possible outputs by testing common ones
    common_outputs = [
        "DP-1", "DP-2", "DP-3", "DP-4",
        "HDMI-A-1", "HDMI-A-2", "HDMI-A-3",
        "eDP-1", "eDP-2",
        "DVI-D-1", "VGA-1"
    ]
    
    available_outputs = []
    
    for output in common_outputs:
        try:
            # Test with a tiny temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                cmd = ['grim', '-o', output, tmp.name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    available_outputs.append(output)
                    print(f"✅ {output} - Available")
                    os.unlink(tmp.name)  # Clean up
                else:
                    print(f"❌ {output} - Not available")
        except Exception as e:
            print(f"❌ {output} - Error: {e}")
    
    print(f"\nAvailable outputs: {available_outputs}")
    
    # Test full screen capture
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cmd = ['grim', tmp.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Full screen capture works")
                # Check file size to see if it captured multiple monitors
                size = os.path.getsize(tmp.name)
                print(f"   Screenshot size: {size} bytes")
                os.unlink(tmp.name)
            else:
                print(f"❌ Full screen capture failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Full screen test error: {e}")

if __name__ == "__main__":
    test_grim_outputs()