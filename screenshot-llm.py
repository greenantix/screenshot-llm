#!/usr/bin/env python3
"""
Screenshot to LLM Assistant - Main Daemon

Captures screenshots on mouse button 9 press and sends them to an LLM
with context-aware prompts for intelligent assistance.
"""

import asyncio
import logging
import os
import sys
import subprocess
import signal
import argparse
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from mouse_listener import MouseListener
from screenshot import ScreenshotCapture
from context_detector import ContextDetector
from llm_client import LLMClient
from ipc_handler import IPCManager

logger = logging.getLogger(__name__)

class ScreenshotLLMDaemon:
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm"):
        self.config_dir = os.path.expanduser(config_dir)
        self.running = False
        
        # Initialize components
        self.mouse_listener = None
        self.screenshot_capture = ScreenshotCapture()
        self.context_detector = ContextDetector()
        self.llm_client = LLMClient()
        self.ipc_manager = IPCManager(config_dir)
        self.ipc_client = None
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(self.config_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'screenshot-llm.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger.info("Screenshot LLM Assistant daemon starting...")
    
    async def handle_screenshot_request(self):
        """Handle mouse button press - capture screenshot and process"""
        try:
            logger.info("Mouse button 9 pressed - processing screenshot request")
            
            # Check if GUI is running
            gui_available = self.ipc_manager.is_server_running()
            
            # Capture screenshot first - we'll need it either way
            logger.info("Capturing screenshot...")
            screenshot_path = self.screenshot_capture.capture_screen()
            logger.info(f"Screenshot saved to: {screenshot_path}")
            
            # Detect context
            logger.info("Detecting application context...")
            context_data = self.context_detector.get_active_window_info()
            logger.info(f"Context: {context_data}")
            
            if gui_available:
                # Try to send to GUI first
                try:
                    # Create new IPC client for fresh connection
                    self.ipc_client = self.ipc_manager.create_client()
                    
                    logger.info("Sending screenshot to GUI...")
                    success = await self.ipc_client.send_screenshot(screenshot_path, context_data)
                    
                    if success:
                        logger.info("Screenshot sent to GUI successfully")
                        return
                    else:
                        logger.warning("Failed to send to GUI despite server being available")
                        
                except Exception as ipc_error:
                    logger.error(f"IPC error: {ipc_error}")
                finally:
                    # Clean up IPC client
                    if self.ipc_client:
                        self.ipc_client.disconnect()
                        self.ipc_client = None
            
            # If we reach here, either GUI is not running or communication failed
            logger.info("Using zenity fallback for display")
            context_prompt = self.context_detector.build_context_prompt()
            llm_response = await self.llm_client.send_screenshot(screenshot_path, context_prompt)
            
            # Show response in zenity
            subprocess.run(
                [sys.executable,
                 os.path.join(os.path.dirname(__file__), "zenity_display.py"),
                 llm_response]
            )
            
            # Clean up screenshot after processing
            try:
                os.unlink(screenshot_path)
            except Exception as e:
                logger.warning(f"Failed to clean up screenshot: {e}")
            
        except Exception as e:
            logger.error(f"Error processing screenshot request: {e}")
            # Fallback to zenity for errors
            try:
                error_response = (
                    f"Error processing request: {str(e)}\n\n"
                    "Please check your configuration and try again."
                )
                subprocess.run(
                    [sys.executable,
                     os.path.join(os.path.dirname(__file__), "zenity_display.py"),
                     error_response]
                )
            except Exception as fallback_error:
                logger.error(f"Failed to show error via fallback: {fallback_error}")
    
    async def start(self):
        """Start the daemon"""
        logger.info("Starting Screenshot LLM Assistant daemon")
        
        # Check if API key is configured
        if not self.llm_client.config.get('api_key'):
            logger.error("No API key configured. Please set your API key:")
            logger.error("1. Edit ~/.local/share/screenshot-llm/config/config.json")
            logger.error("2. Or set ANTHROPIC_API_KEY environment variable")
            return
        
        # Initialize mouse listener
        self.mouse_listener = MouseListener(
            button_code=9,
            callback=self.handle_screenshot_request
        )
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start mouse listener
            await self.mouse_listener.listen()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the daemon"""
        logger.info("Stopping Screenshot LLM Assistant daemon")
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()

def setup_config():
    """Setup initial configuration"""
    config_dir = os.path.expanduser("~/.local/share/screenshot-llm")
    config_file = os.path.join(config_dir, "config", "config.json")
    
    if not os.path.exists(config_file):
        print("Configuration not found. Please run the setup first:")
        print("1. Ensure the config directory exists")
        print("2. Add your API key to config/config.json")
        return False
    
    return True

def install_systemd_service():
    """Install systemd service for autostart"""
    service_content = f"""[Unit]
Description=Screenshot to LLM Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {os.path.abspath(__file__)}
Restart=always
Environment="DISPLAY=:0"
Environment="WAYLAND_DISPLAY=wayland-0"
User={os.environ.get('USER', 'user')}

[Install]
WantedBy=default.target
"""
    
    service_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(service_dir, exist_ok=True)
    
    service_file = os.path.join(service_dir, "screenshot-llm.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"Systemd service installed to: {service_file}")
        print("To enable and start the service:")
        print("  systemctl --user enable screenshot-llm.service")
        print("  systemctl --user start screenshot-llm.service")
        
    except Exception as e:
        print(f"Failed to install systemd service: {e}")

def main():
    parser = argparse.ArgumentParser(description="Screenshot to LLM Assistant")
    parser.add_argument('--install-service', action='store_true',
                       help='Install systemd service for autostart')
    parser.add_argument('--test-screenshot', action='store_true',
                       help='Test screenshot capture')
    parser.add_argument('--test-context', action='store_true',
                       help='Test context detection')
    parser.add_argument('--config-dir', default="~/.local/share/screenshot-llm",
                       help='Configuration directory')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.install_service:
        install_systemd_service()
        return
    
    if args.test_screenshot:
        capturer = ScreenshotCapture()
        screenshot_path = capturer.capture_screen()
        print(f"Screenshot saved to: {screenshot_path}")
        return
    
    if args.test_context:
        detector = ContextDetector()
        window_info = detector.get_active_window_info()
        print(f"Window info: {window_info}")
        context_prompt = detector.build_context_prompt()
        print(f"Context prompt: {context_prompt}")
        return
    
    # Check configuration
    if not setup_config():
        return
    
    # Start daemon
    daemon = ScreenshotLLMDaemon(args.config_dir)
    
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as e:
        logger.error(f"Daemon crashed: {e}")

if __name__ == "__main__":
    main()