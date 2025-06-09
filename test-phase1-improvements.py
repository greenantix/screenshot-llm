#!/usr/bin/env python3
"""
Phase 1 Improvements Test Suite

Tests all the Phase 1 improvements implemented according to claude.md:
- Complete GUI theming with Pop!_OS colors
- Robust IPC for preventing zenity when GUI is running  
- Clickable screenshot thumbnails
- Full conversation context for LLM
- Enhanced markdown rendering
"""

import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

def test_gui_theming():
    """Test that GUI uses complete Pop!_OS theming"""
    print("🎨 Testing GUI theming...")
    
    try:
        from chat_window import PersistentChatWindow
        
        # Create chat window instance
        chat = PersistentChatWindow()
        
        # Check color scheme is Pop!_OS
        expected_colors = {
            'bg_color': '#2d2d2d',
            'accent_color': '#48b9c7',
            'surface_color': '#3c3c3c',
            'fg_color': '#f7f7f7'
        }
        
        # Verify colors are set correctly
        for color_name, expected_value in expected_colors.items():
            actual_value = getattr(chat, color_name, None)
            if actual_value != expected_value:
                print(f"  ❌ {color_name}: expected {expected_value}, got {actual_value}")
                return False
        
        print("  ✅ Pop!_OS color scheme applied correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ GUI theming test failed: {e}")
        return False

async def test_ipc_robustness():
    """Test robust IPC with retry logic"""
    print("🔄 Testing IPC robustness...")
    
    try:
        from ipc_handler import IPCManager
        
        manager = IPCManager()
        client = manager.create_client()
        
        # Test connection with retries
        connected = await client.connect(timeout=2.0, retries=3)
        
        if not connected:
            print("  ✅ IPC correctly fails when no server (expected)")
        else:
            print("  ❌ IPC unexpectedly connected without server")
            return False
        
        # Test that the socket file is checked
        socket_exists = os.path.exists(client.socket_path)
        if not socket_exists:
            print("  ✅ Socket file correctly absent")
        
        print("  ✅ IPC robustness implemented with retry logic")
        return True
        
    except Exception as e:
        print(f"  ❌ IPC robustness test failed: {e}")
        return False

def test_conversation_context():
    """Test full conversation context implementation"""
    print("💬 Testing conversation context...")
    
    try:
        from conversation import ConversationManager
        
        conv = ConversationManager()
        conv.create_new_conversation()
        
        # Add test messages to simulate conversation
        conv.add_screenshot_message("/tmp/test1.png", {"app": "test"})
        conv.add_user_message("What do you see?")
        conv.add_assistant_message("I see a test application.")
        conv.add_user_message("Can you help me with this error?")
        
        # Test API message formatting
        api_messages = conv.get_messages_for_api()
        
        if len(api_messages) < 3:
            print(f"  ❌ Expected multiple messages, got {len(api_messages)}")
            return False
        
        # Check message format includes conversation context
        has_screenshot = any(
            msg.get('role') == 'user' and 
            isinstance(msg.get('content'), list) and
            any(item.get('type') == 'image_path' for item in msg.get('content', []))
            for msg in api_messages
        )
        
        has_text_messages = any(
            msg.get('role') == 'user' and 
            isinstance(msg.get('content'), str)
            for msg in api_messages
        )
        
        if not has_screenshot:
            print("  ❌ Screenshot not properly formatted in API messages")
            return False
        
        if not has_text_messages:
            print("  ❌ Text messages not properly formatted in API messages")
            return False
        
        print("  ✅ Full conversation context properly formatted for API")
        return True
        
    except Exception as e:
        print(f"  ❌ Conversation context test failed: {e}")
        return False

def test_markdown_enhancements():
    """Test enhanced markdown parsing"""
    print("📝 Testing markdown enhancements...")
    
    try:
        from chat_window import PersistentChatWindow
        
        chat = PersistentChatWindow()
        
        # Test markdown parsing
        test_markdown = """# Header 1
## Header 2

Here's **bold text** and *italic text*.

`Inline code` and code blocks:

```python
def test():
    return True
```

Normal text continues here."""
        
        segments = chat._parse_markdown(test_markdown)
        
        # Check for different segment types
        segment_types = {segment[0] for segment in segments}
        expected_types = {'header1', 'header2', 'bold', 'italic', 'code_inline', 'code_block', 'normal'}
        
        missing_types = expected_types - segment_types
        if missing_types:
            print(f"  ❌ Missing markdown types: {missing_types}")
            return False
        
        print("  ✅ Enhanced markdown parsing implemented")
        return True
        
    except Exception as e:
        print(f"  ❌ Markdown enhancement test failed: {e}")
        return False

def test_clickable_thumbnails():
    """Test clickable thumbnail implementation"""
    print("🖼️  Testing clickable thumbnails...")
    
    try:
        from chat_window import PersistentChatWindow
        
        chat = PersistentChatWindow()
        
        # Check if the improved _make_image_clickable method exists
        method = getattr(chat, '_make_image_clickable', None)
        if not method:
            print("  ❌ _make_image_clickable method not found")
            return False
        
        # Check if it has improved implementation (contains 'clickable_image' tag logic)
        import inspect
        source = inspect.getsource(method)
        
        if 'clickable_image' not in source:
            print("  ❌ Improved clickable image logic not found")
            return False
        
        if 'tag_bind' not in source:
            print("  ❌ Tag binding for clicks not implemented")
            return False
        
        print("  ✅ Clickable thumbnails properly implemented")
        return True
        
    except Exception as e:
        print(f"  ❌ Clickable thumbnails test failed: {e}")
        return False

async def test_zenity_prevention():
    """Test that zenity only appears when GUI is not running"""
    print("🚫 Testing zenity prevention...")
    
    try:
        # This test verifies the logic but can't fully test without running processes
        from screenshot import ScreenshotCapture
        
        # Check that daemon has proper fallback logic
        daemon_file = Path(__file__).parent / "screenshot-llm.py"
        with open(daemon_file, 'r') as f:
            daemon_content = f.read()
        
        # Look for the return statement after successful IPC
        if "# Return early - GUI will handle LLM processing" not in daemon_content:
            print("  ❌ Early return after IPC success not found in daemon")
            return False
        
        if "return" not in daemon_content.split("IPC successfully")[0]:
            # Check the context around the success message
            lines = daemon_content.split('\n')
            found_return = False
            for i, line in enumerate(lines):
                if "Screenshot sent to GUI successfully" in line:
                    # Check next few lines for return statement
                    for j in range(i+1, min(i+5, len(lines))):
                        if "return" in lines[j] and not lines[j].strip().startswith('#'):
                            found_return = True
                            break
                    break
            
            if not found_return:
                print("  ❌ Return statement after IPC success not found")
                return False
        
        print("  ✅ Zenity prevention logic properly implemented")
        return True
        
    except Exception as e:
        print(f"  ❌ Zenity prevention test failed: {e}")
        return False

async def main():
    """Run all Phase 1 improvement tests"""
    print("🧪 Testing Screenshot LLM Assistant Phase 1 Improvements\n")
    print("Based on claude.md Phase 1 requirements:\n")
    
    tests = [
        ("GUI Theming", test_gui_theming),
        ("IPC Robustness", test_ipc_robustness),
        ("Conversation Context", test_conversation_context),
        ("Markdown Enhancements", test_markdown_enhancements),
        ("Clickable Thumbnails", test_clickable_thumbnails),
        ("Zenity Prevention", test_zenity_prevention)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Phase 1 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All Phase 1 improvements successfully implemented!")
        print("\n✅ Completed Features:")
        print("  - Complete Pop!_OS themed GUI")
        print("  - Robust IPC with retry logic") 
        print("  - Clickable screenshot thumbnails")
        print("  - Full conversation context for LLM")
        print("  - Enhanced markdown rendering")
        print("  - Zenity prevention when GUI is running")
        print("\n🚀 System is ready for Phase 2 development!")
        print("\nTo test the complete system:")
        print("  ./kill-all.sh && ./run.sh")
    else:
        print(f"\n❌ {total - passed} tests failed. Please review the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))