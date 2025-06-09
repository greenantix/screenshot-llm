#!/usr/bin/env python3
"""
Screenshot LLM Assistant - GUI Process

Separate process for the persistent chat window that communicates
with the main daemon via IPC.
"""

import asyncio
import logging
import os
import sys
import signal
import argparse
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from chat_window import PersistentChatWindow

logger = logging.getLogger(__name__)

def setup_logging(config_dir: str, debug: bool = False):
    """Setup logging for GUI process"""
    log_dir = os.path.join(config_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'screenshot-llm-gui.log')
    
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info("Screenshot LLM Assistant GUI starting...")

def main():
    """Main entry point for GUI process"""
    parser = argparse.ArgumentParser(description="Screenshot LLM Assistant - GUI")
    parser.add_argument('--config-dir', default="~/.local/share/screenshot-llm",
                       help='Configuration directory')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--minimized', action='store_true',
                       help='Start minimized to system tray')
    
    args = parser.parse_args()
    
    config_dir = os.path.expanduser(args.config_dir)
    
    # Setup logging
    setup_logging(config_dir, args.debug)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down GUI...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and run chat window
        chat_window = PersistentChatWindow(config_dir)
        
        if args.minimized:
            # Start minimized
            chat_window.create_window()
            chat_window._minimize_to_tray()
        
        # Run the GUI
        chat_window.run()
        
    except KeyboardInterrupt:
        logger.info("GUI stopped by user")
    except Exception as e:
        logger.error(f"GUI error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()