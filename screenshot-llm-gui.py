#!/usr/bin/env python3

import sys
import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path
import argparse
import json
from typing import Optional, Dict

from lib.chat_window import PersistentChatWindow
from lib.logger import get_logger, log_exception
from lib.image_processor import get_image_processor
from lib.conversation_manager import ConversationManager

logger = get_logger()

def check_dependencies() -> bool:
    """Check if all required dependencies are available"""
    try:
        import PIL
        import pygments
        import pystray
        return True
    except ImportError as e:
        log_exception(e, "Missing required dependency")
        messagebox.showerror(
            "Missing Dependencies",
            "Please install required dependencies:\n\n" +
            "pip install Pillow pygments pystray"
        )
        return False

def load_config() -> Optional[Dict]:
    """Load configuration from config.json"""
    try:
        config_path = Path("config/config.json")
        if not config_path.exists():
            logger.error("Configuration file not found")
            messagebox.showerror(
                "Configuration Error",
                "config.json not found. Please ensure it exists in the config directory."
            )
            return None
            
        with open(config_path, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        log_exception(e, "Failed to load configuration")
        messagebox.showerror(
            "Configuration Error",
            "Failed to load configuration. Please check config.json is valid."
        )
        return None

def setup_directories() -> bool:
    """Create necessary directories if they don't exist"""
    try:
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Create conversations directory
        Path("conversations").mkdir(exist_ok=True)
        
        return True
        
    except Exception as e:
        log_exception(e, "Failed to create required directories")
        messagebox.showerror(
            "Setup Error",
            "Failed to create required directories. Please check permissions."
        )
        return False

def main():
    """Initialize and run the application"""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Screenshot LLM Assistant GUI")
        parser.add_argument("--minimized", 
                          action="store_true",
                          help="Start minimized to system tray")
        args = parser.parse_args()
        
        # Setup logging
        logger.info("Starting Screenshot LLM Assistant GUI")
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
            
        # Create required directories
        if not setup_directories():
            sys.exit(1)
            
        # Load configuration
        config = load_config()
        if not config:
            sys.exit(1)
            
        # Create main window, passing the full config
        window = PersistentChatWindow(config)
        
        # Start minimized if requested
        if args.minimized:
            window.after(0, window._minimize_to_tray)
        
        # Start main loop
        window.mainloop()
        
    except Exception as e:
        log_exception(e, "Fatal error in main")
        messagebox.showerror(
            "Fatal Error",
            "An unexpected error occurred. Please check the logs for details."
        )
        sys.exit(1)
    finally:
        # Cleanup
        try:
            get_image_processor().cleanup()
        except:
            pass

if __name__ == "__main__":
    main()