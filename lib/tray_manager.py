import logging
from typing import Callable, Optional
import io
import base64
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import pystray, but don't fail if not available
try:
    import pystray
    TRAY_AVAILABLE = True
except (ImportError, ValueError) as e:
    logger.warning(f"System tray support not available: {e}")
    TRAY_AVAILABLE = False

class TrayManager:
    def __init__(self, show_window: Callable, quit_app: Callable):
        self.show_window = show_window
        self.quit_app = quit_app
        self.icon = None
        
        if TRAY_AVAILABLE:
            # Create and start tray icon in a separate thread
            self.setup_tray()
        else:
            logger.warning("System tray functionality disabled")

    def setup_tray(self):
        """Setup the system tray icon and menu"""
        try:
            # Create a simple icon (you should replace this with a proper icon file)
            icon_data = self._create_default_icon()
            
            # Create the menu
            menu = (
                pystray.MenuItem("Show Window", self._show_window),
                pystray.MenuItem("Quit", self._quit_app)
            )
            
            # Create the icon
            self.icon = pystray.Icon(
                "Screenshot LLM",
                icon_data,
                "Screenshot LLM Assistant",
                menu
            )
            
            # Run the icon in a separate thread
            import threading
            thread = threading.Thread(target=self._run_tray_icon, daemon=True)
            thread.start()
            logger.info("System tray icon initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup system tray: {e}")
            self.icon = None

    def _run_tray_icon(self):
        """Run the tray icon in a separate thread with error handling"""
        try:
            if self.icon:
                self.icon.run()
        except Exception as e:
            logger.error(f"Error running tray icon: {e}")
            self.icon = None

    def _create_default_icon(self) -> Image:
        """Create a simple default icon"""
        # Base64 encoded 16x16 PNG icon (replace with your actual icon)
        icon_base64 = """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
        AAAN1wAADdcBQiibeAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABSdEVY
        dENvcHlyaWdodABDQzAgUHVibGljIERvbWFpbiBEZWRpY2F0aW9uIGh0dHA6Ly9jcmVhdGl2ZWNv
        bW1vbnMub3JnL3B1YmxpY2RvbWFpbi96ZXJvLzEuMC/g6ZTpAAAAPklEQVQ4jWNgGGjAiE3wPxAw
        YYgzMWBK4gQsDAx4JXEBRnySyICJgYGBEZskMmBiYGD4z8DAQFASHcBVEgcAAKH5BRP1005kAAAA
        AElFTkSuQmCC
        """
        
        # Convert base64 to image
        icon_data = base64.b64decode(icon_base64)
        image = Image.open(io.BytesIO(icon_data))
        return image

    def _show_window(self, icon, item):
        """Show the main window"""
        if self.show_window:
            self.show_window()

    def _quit_app(self, icon, item):
        """Quit the application"""
        icon.stop()
        if self.quit_app:
            self.quit_app()

    def update_icon(self, icon_path: str):
        """Update the tray icon with a new image"""
        try:
            new_icon = Image.open(icon_path)
            self.icon.icon = new_icon
        except Exception as e:
            print(f"Error updating tray icon: {e}")

    def show_notification(self, title: str, message: str):
        """Show a system notification"""
        if self.icon:
            self.icon.notify(title, message)

    def cleanup(self):
        """Clean up the tray icon"""
        if self.icon:
            try:
                self.icon.stop()
            except Exception as e:
                logger.error(f"Error stopping tray icon: {e}")
            self.icon = None