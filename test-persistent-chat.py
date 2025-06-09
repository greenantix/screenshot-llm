#!/usr/bin/env python3
"""
Test script for persistent chat functionality
"""

import os
import sys
import time
import asyncio
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from conversation import ConversationManager
from ipc_handler import IPCManager, IPCMessage

def test_conversation_manager():
    """Test conversation manager functionality"""
    print("Testing ConversationManager...")
    
    conv = ConversationManager()
    
    # Test new conversation
    conv_id = conv.create_new_conversation()
    print(f"Created conversation: {conv_id}")
    
    # Test adding messages
    screenshot_msg = conv.add_screenshot_message(
        "/tmp/test_screenshot.png",
        {"app": "terminal", "window_title": "test"}
    )
    print(f"Added screenshot message: {screenshot_msg['timestamp']}")
    
    user_msg = conv.add_user_message("What do you see in this screenshot?")
    print(f"Added user message: {user_msg['timestamp']}")
    
    assistant_msg = conv.add_assistant_message("I can see a terminal window.")
    print(f"Added assistant message: {assistant_msg['timestamp']}")
    
    # Test API messages
    api_messages = conv.get_messages_for_api()
    print(f"API messages: {len(api_messages)}")
    
    # Test save/load
    save_path = conv.save_conversation()
    print(f"Saved conversation to: {save_path}")
    
    # Test listing conversations
    conversations = conv.list_conversations()
    print(f"Found {len(conversations)} conversations")
    
    print("ConversationManager test completed ✓\n")
    return True

async def test_ipc():
    """Test IPC functionality"""
    print("Testing IPC...")
    
    manager = IPCManager()
    
    # Test server/client creation
    server = manager.create_server()
    client = manager.create_client()
    
    print("IPC objects created ✓")
    
    # Test message creation
    test_msg = IPCMessage("test_command", {"data": "test_data"})
    json_str = test_msg.to_json()
    parsed_msg = IPCMessage.from_json(json_str)
    
    assert parsed_msg.command == "test_command"
    assert parsed_msg.data["data"] == "test_data"
    
    print("IPC message serialization test passed ✓")
    
    print("IPC test completed ✓\n")
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        "lib/conversation.py",
        "lib/ipc_handler.py", 
        "lib/chat_window.py",
        "screenshot-llm.py",
        "screenshot-llm-gui.py",
        "start-screenshot-llm.py"
    ]
    
    base_dir = Path(__file__).parent
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing required file: {file_path}")
            return False
        else:
            print(f"✓ Found: {file_path}")
    
    print("File structure test completed ✓\n")
    return True

def main():
    """Run all tests"""
    print("Starting persistent chat system tests...\n")
    
    tests = [
        test_file_structure,
        test_conversation_manager,
        lambda: asyncio.run(test_ipc())
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            result = test()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            all_passed = False
    
    if all_passed:
        print("🎉 All tests passed! The persistent chat system is ready.")
        print("\nTo start the system:")
        print("  python start-screenshot-llm.py")
        print("\nTo start just the GUI:")
        print("  python screenshot-llm-gui.py")
        print("\nTo start just the daemon:")
        print("  python screenshot-llm.py")
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())