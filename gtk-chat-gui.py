#!/usr/bin/env python3
"""
GTK Chat GUI Launcher - Phase 2 Implementation
New GTK-based main chat interface launcher

This replaces screenshot-llm-gui.py as part of the Phase 2 migration
from Tkinter to GTK as outlined in claude.md.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def load_config(config_dir: str = "~/.local/share/screenshot-llm") -> dict:
    """Load configuration from file"""
    config_dir = os.path.expanduser(config_dir)
    config_path = os.path.join(config_dir, "config", "config.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"Loaded configuration from: {config_path}")
            return config
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Using default configuration")
        return {}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
        print("Using default configuration")
        return {}

def setup_logging(config: dict):
    """Setup logging configuration"""
    config_dir = os.path.expanduser("~/.local/share/screenshot-llm")
    log_dir = os.path.join(config_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'gtk-chat-gui.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for GTK chat GUI"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Screenshot LLM Assistant - GTK Chat GUI")
    parser.add_argument('--config-dir', default="~/.local/share/screenshot-llm",
                       help='Configuration directory')
    parser.add_argument('--minimized', action='store_true',
                       help='Start minimized (not implemented yet)')
    
    args = parser.parse_args()
    
    print("Starting Screenshot LLM Assistant - GTK Chat GUI")
    
    # Load configuration
    config = load_config(args.config_dir)
    
    # Setup logging
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Screenshot LLM Assistant GTK GUI")
    
    try:
        # Import and create GTK window
        try:
            from gtk_chat_window import GTKChatWindow
            logger.info("Successfully imported GTKChatWindow")
        except ImportError as e:
            logger.error(f"Failed to import GTKChatWindow: {e}")
            return 1
        
        # Create window directly
        logger.info("Creating GTK Chat window...")
        window = GTKChatWindow(None, config)
        window.connect("destroy", Gtk.main_quit)
        
        # Ensure window is actually visible
        window.realize()
        window.show_all()
        window.present()
        
        logger.info("GTK Chat window created and shown")
        
        # Run GTK main loop
        Gtk.main()
        
        logger.info("GTK main loop exited")
        return 0
        
    except KeyboardInterrupt:
        logger.info("GTK GUI stopped by user")
        return 0
    except Exception as e:
        logger.error(f"GTK GUI crashed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())