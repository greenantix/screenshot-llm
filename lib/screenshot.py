#!/usr/bin/env python3
import subprocess
import os
import tempfile
import logging
from typing import Tuple, Optional
from PIL import Image
import json

logger = logging.getLogger(__name__)

class ScreenshotCapture:
    def __init__(self, cache_dir: str = "~/.local/share/screenshot-llm/cache"):
        self.cache_dir = os.path.expanduser(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.is_wayland = self._detect_wayland()
        
    def _detect_wayland(self) -> bool:
        """Detect if running on Wayland"""
        return os.environ.get('WAYLAND_DISPLAY') is not None
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position"""
        try:
            if self.is_wayland:
                # Use GNOME Shell extension or alternative method
                result = subprocess.run([
                    'gdbus', 'call', '--session',
                    '--dest', 'org.gnome.Shell',
                    '--object-path', '/org/gnome/Shell',
                    '--method', 'org.gnome.Shell.Eval',
                    'global.get_pointer()'
                ], capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    # Parse the result to extract coordinates
                    output = result.stdout.strip()
                    # This is a simplified parser - might need adjustment
                    if '[' in output and ']' in output:
                        coords_str = output.split('[')[1].split(']')[0]
                        x, y = map(int, coords_str.split(',')[:2])
                        return x, y
            else:
                # X11 method
                result = subprocess.run(['xdotool', 'getmouselocation'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    for part in result.stdout.split():
                        if part.startswith('x:'):
                            x = int(part.split(':')[1])
                        elif part.startswith('y:'):
                            y = int(part.split(':')[1])
                    return x, y
        except Exception as e:
            logger.warning(f"Could not get cursor position: {e}")
        
        return 0, 0  # Fallback
    
    def get_monitor_info(self) -> list:
        """Get information about connected monitors"""
        monitors = []
        try:
            if self.is_wayland:
                # Use wlr-randr or swaymsg for Sway, or try GNOME-specific method
                result = subprocess.run(['wlr-randr'], capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    # Fallback: assume standard setup
                    monitors = [
                        {'name': 'DP-1', 'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
                        {'name': 'DP-2', 'x': 1920, 'y': 0, 'width': 1920, 'height': 1080}, 
                        {'name': 'HDMI-A-1', 'x': 3840, 'y': 0, 'width': 2560, 'height': 1440}
                    ]
                else:
                    # Parse wlr-randr output
                    current_monitor = {}
                    for line in result.stdout.split('\n'):
                        if line and not line.startswith(' '):
                            if current_monitor:
                                monitors.append(current_monitor)
                            current_monitor = {'name': line.split()[0]}
                        elif 'current' in line:
                            parts = line.strip().split()
                            for i, part in enumerate(parts):
                                if 'x' in part and '+' in part:
                                    dims, pos = part.split('+', 1)
                                    width, height = map(int, dims.split('x'))
                                    x, y = map(int, pos.split('+'))
                                    current_monitor.update({
                                        'width': width, 'height': height,
                                        'x': x, 'y': y
                                    })
                    if current_monitor:
                        monitors.append(current_monitor)
            else:
                # X11 method
                result = subprocess.run(['xrandr', '--current'], 
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if ' connected ' in line and '+' in line:
                        parts = line.split()
                        name = parts[0]
                        for part in parts:
                            if 'x' in part and '+' in part:
                                dims, pos = part.split('+', 1)
                                width, height = map(int, dims.split('x'))
                                x, y = map(int, pos.split('+'))
                                monitors.append({
                                    'name': name, 'x': x, 'y': y,
                                    'width': width, 'height': height
                                })
                                break
        except Exception as e:
            logger.warning(f"Could not get monitor info: {e}")
            # Fallback to single monitor
            monitors = [{'name': 'default', 'x': 0, 'y': 0, 'width': 1920, 'height': 1080}]
        
        return monitors
    
    def find_active_monitor(self, cursor_x: int, cursor_y: int, monitors: list) -> dict:
        """Find which monitor contains the cursor"""
        for monitor in monitors:
            if (monitor['x'] <= cursor_x < monitor['x'] + monitor['width'] and
                monitor['y'] <= cursor_y < monitor['y'] + monitor['height']):
                return monitor
        return monitors[0] if monitors else {'name': 'default', 'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
    
    def capture_screen(self) -> str:
        """Capture screenshot of the monitor containing the cursor"""
        try:
            # Get cursor position and monitor info
            cursor_x, cursor_y = self.get_cursor_position()
            monitors = self.get_monitor_info()
            active_monitor = self.find_active_monitor(cursor_x, cursor_y, monitors)
            
            logger.info(f"Capturing screen on monitor: {active_monitor['name']} "
                       f"({active_monitor['width']}x{active_monitor['height']})")
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.cache_dir, filename)
            
            if self.is_wayland:
                self._capture_wayland(active_monitor, filepath)
            else:
                self._capture_x11(active_monitor, filepath)
            
            # Optimize image size
            self._optimize_image(filepath)
            
            return filepath
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise
    
    def _capture_wayland(self, monitor: dict, filepath: str):
        """Capture screenshot on Wayland"""
        # Try grim with geometry
        geometry = f"{monitor['x']},{monitor['y']} {monitor['width']}x{monitor['height']}"
        
        try:
            result = subprocess.run([
                'grim', '-g', geometry, filepath
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Fallback: capture entire screen
                logger.warning("Could not capture specific monitor, capturing all screens")
                subprocess.run(['grim', filepath], check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"grim failed: {e}")
            # Try gnome-screenshot as last resort
            subprocess.run(['gnome-screenshot', '-f', filepath], check=True, timeout=10)
    
    def _capture_x11(self, monitor: dict, filepath: str):
        """Capture screenshot on X11"""
        geometry = f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}"
        
        try:
            # Try maim first
            result = subprocess.run([
                'maim', '-g', geometry, filepath
            ], capture_output=True, timeout=10)
            
            if result.returncode != 0:
                # Fallback to scrot
                subprocess.run(['scrot', '-a', 
                              f"{monitor['x']},{monitor['y']},{monitor['width']},{monitor['height']}", 
                              filepath], check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Final fallback to gnome-screenshot
            subprocess.run(['gnome-screenshot', '-f', filepath], check=True, timeout=10)
    
    def _optimize_image(self, filepath: str):
        """Optimize image size for API transmission"""
        try:
            with Image.open(filepath) as img:
                # If image is larger than 1080p, resize
                if img.width > 1920 or img.height > 1080:
                    img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
                    img.save(filepath, "PNG", optimize=True)
                    logger.info(f"Resized image to {img.width}x{img.height}")
        except Exception as e:
            logger.warning(f"Could not optimize image: {e}")

import time

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    capturer = ScreenshotCapture()
    screenshot_path = capturer.capture_screen()
    print(f"Screenshot saved to: {screenshot_path}")