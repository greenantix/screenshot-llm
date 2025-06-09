#!/usr/bin/env python3
"""
System tray manager for Screenshot LLM Assistant
"""

import threading
from typing import Callable
from .logger import get_logger, log_exception

logger = get_logger(__name__)

class TrayManager:
    """Manages system tray functionality"""
    
    def __init__(self, show_window: Callable, quit_app: Callable):
        self.show_window = show_window
        self.quit_app = quit_app
        self.icon = None
        self.running = False
        
        self._setup_tray()
    
    def _setup_tray(self):
        """Set up the system tray icon"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            def create_icon():
                # Create a simple 64x64 icon
                width = 64
                height = 64
                
                # Create image with transparent background
                image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # Draw a simple camera icon
                # Camera body
                draw.rectangle([8, 20, 56, 48], fill=(72, 185, 199, 255), outline=(255, 255, 255, 255))
                
                # Lens
                draw.ellipse([20, 26, 44, 42], fill=(45, 45, 45, 255), outline=(255, 255, 255, 255))
                draw.ellipse([24, 28, 40, 40], fill=(30, 30, 30, 255))
                
                # Flash
                draw.rectangle([12, 16, 20, 20], fill=(255, 255, 255, 255))
                
                return image
            
            # Create menu
            def create_menu():
                return pystray.Menu(
                    pystray.MenuItem("Show Window", self._on_show),
                    pystray.MenuItem("Hide Window", self._on_hide),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Quit", self._on_quit)
                )
            
            # Create icon
            self.icon = pystray.Icon(
                "screenshot-llm",
                create_icon(),
                "Screenshot LLM Assistant",
                create_menu()
            )
            
            # Set up click handler
            self.icon.default_action = self._on_show
            
            logger.info("System tray icon created")
            
        except ImportError:
            logger.warning("pystray not available, tray functionality disabled")
            self.icon = None
        except Exception as e:
            log_exception(e, "Failed to create system tray icon")
            self.icon = None
    
    def start(self):
        """Start the tray icon in a separate thread"""
        if not self.icon:
            return
            
        def run_tray():
            try:
                self.running = True
                self.icon.run()
            except Exception as e:
                log_exception(e, "Tray icon crashed")
        
        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()
        logger.info("System tray started")
    
    def stop(self):
        """Stop the tray icon"""
        if self.icon and self.running:
            self.running = False
            self.icon.stop()
            logger.info("System tray stopped")
    
    def _on_show(self, icon=None, item=None):
        """Handle show window from tray"""
        try:
            self.show_window()
        except Exception as e:
            log_exception(e, "Failed to show window from tray")
    
    def _on_hide(self, icon=None, item=None):
        """Handle hide window from tray"""
        # This will be handled by the main window
        pass
    
    def _on_quit(self, icon=None, item=None):
        """Handle quit from tray"""
        try:
            self.stop()
            self.quit_app()
        except Exception as e:
            log_exception(e, "Failed to quit from tray")
    
    def cleanup(self):
        """Clean up tray resources"""
        self.stop()

if __name__ == "__main__":
    # Test the tray manager
    import time
    
    def show_callback():
        print("Show window called")
    
    def quit_callback():
        print("Quit called")
    
    tray = TrayManager(show_callback, quit_callback)
    tray.start()
    
    try:
        time.sleep(10)  # Run for 10 seconds
    except KeyboardInterrupt:
        pass
    finally:
        tray.cleanup()