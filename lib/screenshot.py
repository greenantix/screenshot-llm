#!/usr/bin/env python3
"""
Screenshot capture utilities for Screenshot LLM Assistant
"""

import os
import subprocess
import tempfile
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ScreenshotCapture:
    """Handles screenshot capture across different desktop environments"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or tempfile.gettempdir()
        self.screenshot_tools = self._detect_screenshot_tools()
        
    def _detect_screenshot_tools(self) -> dict:
        """Detect available screenshot tools"""
        tools = {}
        
        # Check for Wayland tools
        if self._command_exists('grim'):
            tools['grim'] = True
        if self._command_exists('wlr-randr'):
            tools['wlr-randr'] = True
            
        # Check for X11 tools
        if self._command_exists('maim'):
            tools['maim'] = True
        if self._command_exists('scrot'):
            tools['scrot'] = True
        if self._command_exists('import'):  # ImageMagick
            tools['import'] = True
            
        # Check for generic tools
        if self._command_exists('gnome-screenshot'):
            tools['gnome-screenshot'] = True
        if self._command_exists('spectacle'):  # KDE
            tools['spectacle'] = True
            
        logger.info(f"Available screenshot tools: {list(tools.keys())}")
        return tools
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            subprocess.run(['which', command], 
                         capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _is_wayland(self) -> bool:
        """Check if running under Wayland"""
        return 'WAYLAND_DISPLAY' in os.environ
    
    def capture_screen(self, monitor: int = None) -> str:
        """Capture a screenshot and return the file path"""
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        success = False
        
        if self._is_wayland():
            success = self._capture_wayland(filepath, monitor)
        else:
            success = self._capture_x11(filepath, monitor)
        
        if not success:
            # Fallback to generic tools
            success = self._capture_generic(filepath)
        
        if success and os.path.exists(filepath):
            logger.info(f"Screenshot captured: {filepath}")
            return filepath
        else:
            raise Exception("Failed to capture screenshot with any available tool")
    
    def _capture_wayland(self, filepath: str, monitor: int = None) -> bool:
        """Capture screenshot on Wayland"""
        if 'grim' in self.screenshot_tools:
            try:
                cmd = ['grim']
                if monitor is not None:
                    # Get output info with wlr-randr if available
                    if 'wlr-randr' in self.screenshot_tools:
                        try:
                            result = subprocess.run(['wlr-randr'], 
                                                  capture_output=True, text=True)
                            outputs = self._parse_wlr_outputs(result.stdout)
                            if monitor < len(outputs):
                                cmd.extend(['-o', outputs[monitor]])
                        except Exception as e:
                            logger.warning(f"Failed to get monitor info: {e}")
                
                cmd.append(filepath)
                subprocess.run(cmd, check=True)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"grim failed: {e}")
        
        return False
    
    def _capture_x11(self, filepath: str, monitor: int = None) -> bool:
        """Capture screenshot on X11"""
        # Try maim first (preferred)
        if 'maim' in self.screenshot_tools:
            try:
                cmd = ['maim']
                if monitor is not None:
                    # Get display info
                    displays = self._get_x11_displays()
                    if monitor < len(displays):
                        display = displays[monitor]
                        cmd.extend(['-g', f"{display['width']}x{display['height']}+{display['x']}+{display['y']}"])
                
                cmd.append(filepath)
                subprocess.run(cmd, check=True)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"maim failed: {e}")
        
        # Try scrot as fallback
        if 'scrot' in self.screenshot_tools:
            try:
                cmd = ['scrot']
                if monitor is not None:
                    # scrot uses different syntax
                    cmd.extend(['-s'])  # Select area (simplified)
                
                cmd.append(filepath)
                subprocess.run(cmd, check=True)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"scrot failed: {e}")
        
        # Try ImageMagick import
        if 'import' in self.screenshot_tools:
            try:
                cmd = ['import', '-window', 'root', filepath]
                subprocess.run(cmd, check=True)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"import failed: {e}")
        
        return False
    
    def _capture_generic(self, filepath: str) -> bool:
        """Capture using generic desktop tools"""
        # Try gnome-screenshot
        if 'gnome-screenshot' in self.screenshot_tools:
            try:
                subprocess.run(['gnome-screenshot', '-f', filepath], check=True)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"gnome-screenshot failed: {e}")
        
        # Try spectacle (KDE)
        if 'spectacle' in self.screenshot_tools:
            try:
                subprocess.run(['spectacle', '-b', '-n', '-o', filepath], check=True)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"spectacle failed: {e}")
        
        return False
    
    def _parse_wlr_outputs(self, output: str) -> list:
        """Parse wlr-randr output to get display names"""
        outputs = []
        for line in output.split('\n'):
            if line and not line.startswith(' '):
                # Output name is the first word
                output_name = line.split()[0]
                if output_name and output_name != 'Output':
                    outputs.append(output_name)
        return outputs
    
    def _get_x11_displays(self) -> list:
        """Get X11 display information"""
        displays = []
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ' connected ' in line and '+' in line:
                    # Parse geometry like "1920x1080+0+0"
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and '+' in part:
                            # Extract dimensions and position
                            geom = part.split('+')
                            if len(geom) >= 3:
                                dims = geom[0].split('x')
                                if len(dims) == 2:
                                    displays.append({
                                        'width': int(dims[0]),
                                        'height': int(dims[1]),
                                        'x': int(geom[1]),
                                        'y': int(geom[2])
                                    })
                            break
        except Exception as e:
            logger.error(f"Failed to get X11 display info: {e}")
        
        return displays
    
    def get_cursor_monitor(self) -> int:
        """Get the monitor containing the mouse cursor"""
        try:
            if self._is_wayland():
                # This is more complex on Wayland, return 0 for now
                return 0
            else:
                # Use xdotool to get cursor position
                if self._command_exists('xdotool'):
                    result = subprocess.run(['xdotool', 'getmouselocation'], 
                                          capture_output=True, text=True)
                    # Parse output like "x:960 y:540 screen:0 window:123"
                    for part in result.stdout.split():
                        if part.startswith('screen:'):
                            return int(part.split(':')[1])
        except Exception as e:
            logger.error(f"Failed to get cursor monitor: {e}")
        
        return 0  # Default to first monitor

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    capturer = ScreenshotCapture()
    try:
        filepath = capturer.capture_screen()
        print(f"Screenshot saved to: {filepath}")
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")