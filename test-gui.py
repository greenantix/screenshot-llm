#!/usr/bin/env python3
"""
Test script for Screenshot LLM Assistant GUI
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing imports...")
        
        from lib.logger import get_logger
        print("✓ Logger module")
        
        from lib.image_processor import get_image_processor
        print("✓ Image processor module")
        
        from lib.conversation_manager import ConversationManager
        print("✓ Conversation manager module")
        
        from lib.conversation_browser import ConversationBrowser
        print("✓ Conversation browser module")
        
        from lib.tray_manager import TrayManager
        print("✓ Tray manager module")
        
        from lib.tab_manager import TabManager
        print("✓ Tab manager module")
        
        from lib.llm_client import LLMClient
        print("✓ LLM client module")
        
        from lib.ipc_handler import IPCManager
        print("✓ IPC handler module")
        
        from lib.chat_window import PersistentChatWindow
        print("✓ Chat window module")
        
        print("All imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    try:
        print("\nTesting configuration...")
        
        import json
        config_path = "config/config.json"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            print("✓ Configuration file loaded")
            
            # Check for required sections
            if 'llm' in config:
                print("✓ LLM configuration found")
            else:
                print("⚠ LLM configuration missing")
                
            if 'ui' in config:
                print("✓ UI configuration found")
            else:
                print("⚠ UI configuration missing")
                
            return True
        else:
            print("✗ Configuration file not found")
            return False
            
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_directories():
    """Test that required directories exist or can be created"""
    try:
        print("\nTesting directories...")
        
        directories = ["logs", "conversations", "config"]
        
        for directory in directories:
            if os.path.exists(directory):
                print(f"✓ {directory}/ exists")
            else:
                try:
                    os.makedirs(directory, exist_ok=True)
                    print(f"✓ {directory}/ created")
                except Exception as e:
                    print(f"✗ Failed to create {directory}/: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Directory error: {e}")
        return False

def test_gui_startup():
    """Test GUI startup"""
    try:
        print("\nTesting GUI startup...")
        
        from lib.chat_window import PersistentChatWindow
        
        # Create window
        window = PersistentChatWindow()
        print("✓ Chat window created")
        
        # Test basic functionality
        if hasattr(window, 'tab_manager'):
            print("✓ Tab manager initialized")
        else:
            print("✗ Tab manager not found")
            
        if hasattr(window, 'status_bar'):
            print("✓ Status bar initialized")
        else:
            print("✗ Status bar not found")
            
        # Close window after a short delay
        def close_window():
            time.sleep(2)
            try:
                window.quit()
            except:
                pass
        
        threading.Thread(target=close_window, daemon=True).start()
        
        print("✓ Starting GUI (will close automatically in 2 seconds)")
        window.mainloop()
        
        print("✓ GUI test completed")
        return True
        
    except Exception as e:
        print(f"✗ GUI startup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Screenshot LLM Assistant - GUI Test Suite")
    print("=" * 50)
    
    success_count = 0
    total_tests = 4
    
    # Run tests
    if test_imports():
        success_count += 1
    
    if test_configuration():
        success_count += 1
    
    if test_directories():
        success_count += 1
    
    if test_gui_startup():
        success_count += 1
    
    # Results
    print("\n" + "=" * 50)
    print(f"Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! The GUI should be working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())