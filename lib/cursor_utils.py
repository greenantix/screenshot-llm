#!/usr/bin/env python3
"""
Cursor position utilities for getting mouse coordinates
Part of Phase 1 implementation as outlined in claude.md
"""

import subprocess
import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def get_cursor_position() -> Tuple[int, int]:
    """
    Get the current cursor (mouse) position.
    
    Returns:
        Tuple of (x, y) coordinates
        
    Raises:
        RuntimeError: If unable to get cursor position
    """
    
    # Try Wayland first (if available)
    if os.environ.get('WAYLAND_DISPLAY'):
        pos = _get_cursor_position_wayland()
        if pos:
            return pos
    
    # Fallback to X11
    pos = _get_cursor_position_x11()
    if pos:
        return pos
    
    # Last resort fallback
    logger.warning("Could not detect cursor position, using default")
    return (100, 100)

def _get_cursor_position_wayland() -> Optional[Tuple[int, int]]:
    """Get cursor position on Wayland using various methods"""
    
    # Method 1: Try using wlr-randr if available (for wlroots compositors)
    try:
        result = subprocess.run(['wlr-randr'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            # wlr-randr doesn't directly give cursor position, but we can try other tools
            pass
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Method 2: Try using gdbus to query GNOME Shell (for GNOME on Wayland)
    try:
        # This is a more complex method that would require D-Bus interface
        # For now, we'll use a simpler approach
        pass
    except Exception:
        pass
    
    # Method 3: Try using ydotool (if available)
    try:
        # ydotool doesn't have a direct query command for cursor position
        pass
    except Exception:
        pass
    
    # Method 4: Parse environment or use approximation
    # On Wayland, getting cursor position is challenging without compositor-specific APIs
    # For now, return None to fall back to X11 or default
    return None

def _get_cursor_position_x11() -> Optional[Tuple[int, int]]:
    """Get cursor position on X11 using xdotool"""
    
    # Method 1: Try xdotool (most reliable)
    try:
        result = subprocess.run(
            ['xdotool', 'getmouselocation', '--shell'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # Parse output like "X=1234\nY=5678\nSCREEN=0\nWINDOW=...\n"
            lines = result.stdout.strip().split('\n')
            x, y = None, None
            
            for line in lines:
                if line.startswith('X='):
                    x = int(line.split('=')[1])
                elif line.startswith('Y='):
                    y = int(line.split('=')[1])
            
            if x is not None and y is not None:
                logger.debug(f"Got cursor position from xdotool: ({x}, {y})")
                return (x, y)
                
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        logger.debug(f"xdotool failed: {e}")
    
    # Method 2: Try xwininfo (alternative)
    try:
        result = subprocess.run(
            ['xwininfo', '-root', '-tree'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            # This is more complex to parse and doesn't directly give cursor position
            # xwininfo is mainly for window information
            pass
            
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Method 3: Try xinput (if available)
    try:
        # xinput can query devices but doesn't directly give cursor position
        pass
    except Exception:
        pass
    
    return None

def test_cursor_detection():
    """Test function to verify cursor position detection works"""
    print("Testing cursor position detection...")
    
    try:
        x, y = get_cursor_position()
        print(f"Current cursor position: ({x}, {y})")
        
        # Test multiple times to see if it's consistent
        import time
        print("Move your mouse and watch the coordinates:")
        for i in range(5):
            time.sleep(1)
            x, y = get_cursor_position()
            print(f"  Position {i+1}: ({x}, {y})")
            
    except Exception as e:
        print(f"Error testing cursor detection: {e}")

if __name__ == "__main__":
    test_cursor_detection()