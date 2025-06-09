#!/usr/bin/env python3
"""
Screenshot to LLM Assistant - Main Daemon

Captures screenshots on mouse button 9 press and sends them to an LLM
with context-aware prompts for intelligent assistance.
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
import signal
import argparse
from pathlib import Path
from typing import Dict

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from mouse_listener import MouseListener
from screenshot import ScreenshotCapture
from context_detector import ContextDetector
from llm_client import LLMClient
from ipc_handler import IPCManager
from cursor_utils import get_cursor_position

logger = logging.getLogger(__name__)

class ScreenshotLLMDaemon:
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm"):
        self.config_dir = os.path.expanduser(config_dir)
        self.running = False
        self.config = self._load_full_config()
        
        # Initialize components
        self.mouse_listener = None
        self.screenshot_capture = ScreenshotCapture()
        self.context_detector = ContextDetector()
        self.llm_client = LLMClient(self.config.get('llm', {}))
        self.ipc_manager = IPCManager(config_dir)
        self.ipc_client = None
        
        # Setup logging
        self._setup_logging()

    def _load_full_config(self) -> Dict:
        """Load the entire configuration file."""
        config_path = os.path.join(self.config_dir, "config", "config.json")
        if not os.path.exists(config_path):
            # Fallback to current directory for local testing
            config_path = "config/config.json"

        try:
            with open(config_path, 'r') as f:
                logger.info(f"Loading configuration from: {config_path}")
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}
        
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

            # Get cursor position early
            cursor_pos = get_cursor_position()
            logger.info(f"Cursor position: {cursor_pos}")
            
            # Check if GUI is running
            gui_available = self.ipc_manager.is_server_running()
            
            # Capture screenshot first - we'll need it either way
            logger.info("Capturing screenshot...")
            
            # Get screenshot mode from config
            screenshot_mode = self.config.get("advanced", {}).get("screenshot_mode", "all_monitors")
            
            if screenshot_mode == "active_window":
                screenshot_path = self.screenshot_capture.capture_screen(active_window=True)
                logger.info(f"Active window screenshot saved to: {screenshot_path}")
            elif screenshot_mode == "focused_monitor":
                # For focused monitor, we'll modify grim to capture current monitor
                screenshot_path = self.screenshot_capture.capture_screen(monitor=0)  # Will be handled by focused output logic
                logger.info(f"Focused monitor screenshot saved to: {screenshot_path}")
            else:
                # Default: all monitors
                screenshot_path = self.screenshot_capture.capture_screen()
                logger.info(f"Full screenshot saved to: {screenshot_path}")
            
            # Detect context
            logger.info("Detecting application context...")
            context_data = self.context_detector.get_active_window_info()
            logger.info(f"Context: {context_data}")
            
            # Get LLM response using quick prompt for pop-up
            logger.info("Getting LLM response for pop-up...")
            quick_prompt = self.config.get("llm", {}).get("quick_prompt", "Provide a brief analysis of the screenshot.")
            context_prompt = self.context_detector.build_context_prompt()
            full_prompt = f"{quick_prompt}\n\n{context_prompt}"
            
            llm_response = await self.llm_client.send_screenshot(screenshot_path, full_prompt)
            
            # Always show Quick Answer pop-up first
            logger.info("Showing Quick Answer pop-up...")
            self._show_quick_answer(llm_response, cursor_pos)
            
            # Clean up screenshot after pop-up processing
            try:
                os.unlink(screenshot_path)
            except Exception as e:
                logger.warning(f"Failed to clean up screenshot: {e}")
            
        except Exception as e:
            logger.error(f"Error processing screenshot request: {e}")
            cursor_pos = get_cursor_position() # Get cursor pos again for error
            error_response = (
                f"Error: {str(e)}\n\n"
                "Please check logs for details."
            )
            self._show_quick_answer(error_response, cursor_pos)

    def _show_quick_answer(self, response_text: str, cursor_pos: tuple):
        """Launch the GTK Quick Answer window."""
        try:
            logger.info("Launching Quick Answer window...")
            quick_answer_script = os.path.join(lib_path, "quick_answer_window.py")
            
            subprocess.run([
                sys.executable,
                quick_answer_script,
                response_text,
                f"--x={cursor_pos[0]}",
                f"--y={cursor_pos[1]}",
                f"--config-dir={self.config_dir}"
            ], check=True)
            
        except Exception as e:
            logger.error(f"Failed to launch Quick Answer window: {e}")
    
    async def start(self):
        """Start the daemon"""
        logger.info("Starting Screenshot LLM Assistant daemon")
        
        # Check if API key is configured
        if not self.llm_client.config.get('api_key'):
            logger.error("No API key configured. Please set your API key:")
            logger.error("1. Edit ~/.local/share/screenshot-llm/config/config.json")
            logger.error("2. Or set ANTHROPIC_API_KEY environment variable")
            return
        
        # Get mouse device path from the full config
        mouse_device_path = self.config.get("advanced", {}).get("mouse_device_path", "")

        # Initialize mouse listener
        self.mouse_listener = MouseListener(
            button_code=276,
            callback=self.handle_screenshot_request,
            device_path=mouse_device_path or None  # Pass None if path is empty
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