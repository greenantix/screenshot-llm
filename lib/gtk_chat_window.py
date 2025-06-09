#!/usr/bin/env python3
"""
GTK Chat Window - Phase 2 of Tkinter to GTK Migration
Main chat interface implementation using GTK instead of Tkinter

This replaces lib/chat_window.py with a modern GTK implementation
as outlined in claude.md Phase 2.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango, GLib
import sys
import os
import threading
import asyncio
import json
from typing import Optional, List, Dict, Any
from PIL import Image
import io
import subprocess
import re
from datetime import datetime

# Add lib directory to path for imports
lib_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, lib_path)

# Import modules individually to avoid fallback issues
import logging
logging.basicConfig(level=logging.INFO)

# Set up basic logger first
logger = logging.getLogger(__name__)

def log_exception(e, msg):
    logger.error(f"{msg}: {e}")

# Try importing each module individually
try:
    from conversation import ConversationManager
except ImportError as e:
    logger.warning(f"ConversationManager import failed: {e}")
    class ConversationManager:
        def __init__(self, config=None):
            self.messages = []
        def add_user_message(self, msg): pass
        def add_assistant_message(self, msg): pass
        def get_messages_for_api(self): return []

try:
    from llm_client import LLMClient
except ImportError as e:
    logger.warning(f"LLMClient import failed: {e}")
    class LLMClient:
        def __init__(self, config): pass
        async def send_screenshot(self, path, prompt): return "Mock response"

try:
    from ipc_handler import IPCManager
except ImportError as e:
    logger.warning(f"IPCManager import failed: {e}")
    class IPCManager:
        def create_server(self): return None

try:
    from image_processor import get_image_processor
except ImportError as e:
    logger.warning(f"get_image_processor import failed: {e}")
    def get_image_processor():
        return None

try:
    from settings_window import SettingsWindow
except ImportError as e:
    logger.warning(f"SettingsWindow import failed: {e}")
    class SettingsWindow:
        def __init__(self, *args, **kwargs): pass

try:
    from logger import get_logger
    logger = get_logger(__name__)
except ImportError as e:
    logger.warning(f"logger.get_logger failed: {e}")
    # Already have logging set up above

# Clean up old fallback code
if False:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def log_exception(e, msg):
        logger.error(f"{msg}: {e}")
    
    # Mock classes for testing
    class ConversationManager:
        def __init__(self, config=None):
            self.messages = []
        def add_user_message(self, msg): pass
        def add_assistant_message(self, msg): pass
        def get_messages_for_api(self): return []
    
    class LLMClient:
        def __init__(self, config): pass
        async def send_screenshot(self, path, prompt): return "Mock response"
    
    class IPCManager:
        def create_server(self): return None
    
    def get_image_processor():
        return None

try:
    logger = get_logger(__name__)
except NameError:
    logger = logging.getLogger(__name__)

class MessageBubble(Gtk.Box):
    """
    Custom GTK widget for displaying individual chat messages.
    Much cleaner than tkinter's text widget approach.
    """
    
    def __init__(self, sender: str, content: str, role: str, timestamp: str = None, config: Dict = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.sender = sender
        self.content = content
        self.role = role
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.config = config or {}
        
        # Get theme colors
        self.bg_color = "#2d2d2d"
        self.surface_color = "#3c3c3c"
        self.accent_color = "#48b9c7"
        self.text_color = "#ffffff"
        self.text_secondary = "#b0b0b0"
        
        self._create_bubble()
        self._apply_styles()
    
    def _create_bubble(self):
        """Create the message bubble UI"""
        # Main bubble container
        bubble_frame = Gtk.Frame()
        bubble_frame.set_shadow_type(Gtk.ShadowType.NONE)
        
        # Different styling based on role
        if self.role == "assistant":
            bubble_bg = self.surface_color
            sender_color = self.accent_color
        elif self.role == "system":
            bubble_bg = "#2a4a5a"  # Slightly different for system messages
            sender_color = "#70c0d0"
        else:
            bubble_bg = "#404040"
            sender_color = "#ffffff"
        
        # Bubble content box
        bubble_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        bubble_box.set_margin_left(12)
        bubble_box.set_margin_right(12)
        bubble_box.set_margin_top(8)
        bubble_box.set_margin_bottom(8)
        
        # Header with sender and timestamp
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        sender_label = Gtk.Label()
        sender_label.set_markup(f"<b>{self.sender}</b>")
        sender_label.set_halign(Gtk.Align.START)
        header_box.pack_start(sender_label, False, False, 0)
        
        timestamp_label = Gtk.Label(label=self.timestamp)
        timestamp_label.set_halign(Gtk.Align.END)
        timestamp_label.get_style_context().add_class("timestamp")
        header_box.pack_end(timestamp_label, False, False, 0)
        
        bubble_box.pack_start(header_box, False, False, 0)
        
        # Content area
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._parse_content()
        bubble_box.pack_start(self.content_area, True, True, 0)
        
        bubble_frame.add(bubble_box)
        self.pack_start(bubble_frame, True, True, 4)
    
    def _parse_content(self):
        """Parse and display message content with markdown support"""
        # Simple markdown parsing for GTK
        if self.role == "assistant":
            self._parse_markdown_content(self.content)
        else:
            # Simple text for user messages
            label = Gtk.Label(label=self.content)
            label.set_line_wrap(True)
            label.set_line_wrap_mode(Pango.WrapMode.WORD)
            label.set_halign(Gtk.Align.START)
            label.set_selectable(True)
            self.content_area.pack_start(label, False, False, 0)
    
    def _parse_markdown_content(self, text: str):
        """Parse markdown content and create appropriate GTK widgets"""
        # Split by code blocks first
        parts = re.split(r'(```[\w]*\n.*?\n```)', text, flags=re.DOTALL)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # Code block
                self._create_code_block(part)
            else:
                # Regular markdown text
                self._create_text_content(part)
    
    def _create_code_block(self, code_block: str):
        """Create a modern code block widget"""
        lines = code_block.strip().split('\n')
        if len(lines) < 2:
            return
        
        # Extract language and code
        first_line = lines[0]
        language = first_line[3:].strip() if len(first_line) > 3 else "text"
        code_content = '\n'.join(lines[1:-1])
        
        if not code_content.strip():
            return
        
        # Code block container
        code_frame = Gtk.Frame()
        code_frame.set_shadow_type(Gtk.ShadowType.IN)
        code_frame.get_style_context().add_class("code-block")
        
        code_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header with language and copy button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.set_margin_left(8)
        header_box.set_margin_right(8)
        header_box.set_margin_top(6)
        header_box.set_margin_bottom(6)
        header_box.get_style_context().add_class("code-header")
        
        lang_label = Gtk.Label()
        lang_label.set_markup(f"<small><b>{language.title() if language != 'text' else 'Code'}</b></small>")
        lang_label.set_halign(Gtk.Align.START)
        header_box.pack_start(lang_label, True, True, 0)
        
        copy_button = Gtk.Button(label="📋 Copy")
        copy_button.get_style_context().add_class("copy-button")
        copy_button.connect("clicked", lambda w: self._copy_code(code_content))
        header_box.pack_end(copy_button, False, False, 0)
        
        code_box.pack_start(header_box, False, False, 0)
        
        # Code content
        code_scroll = Gtk.ScrolledWindow()
        code_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        code_scroll.set_size_request(-1, min(200, max(50, code_content.count('\n') * 20 + 40)))
        
        code_text = Gtk.TextView()
        code_text.set_editable(False)
        code_text.set_cursor_visible(False)
        code_text.get_style_context().add_class("code-content")
        
        buffer = code_text.get_buffer()
        buffer.set_text(code_content)
        
        code_scroll.add(code_text)
        code_box.pack_start(code_scroll, True, True, 0)
        
        code_frame.add(code_box)
        self.content_area.pack_start(code_frame, False, False, 4)
    
    def _create_text_content(self, text: str):
        """Create text content with basic markdown formatting"""
        if not text.strip():
            return
        
        # Simple text view for now - can be enhanced later
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        text_view.get_style_context().add_class("message-text")
        
        buffer = text_view.get_buffer()
        
        # Basic markdown parsing
        formatted_text = text
        
        # Handle headers
        formatted_text = re.sub(r'^# (.+)$', r'<big><b>\1</b></big>', formatted_text, flags=re.MULTILINE)
        formatted_text = re.sub(r'^## (.+)$', r'<b>\1</b>', formatted_text, flags=re.MULTILINE)
        
        # Handle bold and italic
        formatted_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', formatted_text)
        formatted_text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', formatted_text)
        
        # Handle inline code
        formatted_text = re.sub(r'`([^`]+)`', r'<tt>\1</tt>', formatted_text)
        
        # Handle lists
        formatted_text = re.sub(r'^- (.+)$', r'  • \1', formatted_text, flags=re.MULTILINE)
        
        try:
            buffer.insert_markup(buffer.get_end_iter(), formatted_text, -1)
        except:
            # Fallback to plain text if markup fails
            buffer.set_text(text)
        
        # Adjust height based on content
        lines = len(text.split('\n'))
        text_view.set_size_request(-1, min(300, max(60, lines * 25)))
        
        self.content_area.pack_start(text_view, False, False, 0)
    
    def _copy_code(self, code: str):
        """Copy code to clipboard"""
        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(code, -1)
            
            # Visual feedback could be added here
            print(f"Copied {len(code)} characters to clipboard")
            
        except Exception as e:
            logger.error(f"Failed to copy code: {e}")
    
    def _apply_styles(self):
        """Apply GTK CSS styles to the bubble"""
        # Styles will be applied via CSS provider in main window
        pass

class GTKChatTab:
    """
    GTK implementation of a chat tab.
    Replaces the Tkinter ChatTab class.
    """
    
    def __init__(self, notebook: Gtk.Notebook, tab_id: str, config: Dict = None):
        self.tab_id = tab_id
        self.notebook = notebook
        self.config = config or {}
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager(config=config)
        
        # Create the tab content
        self._create_tab()
        
        # Add to notebook
        label = Gtk.Label(label=f"Chat {tab_id}")
        self.notebook.append_page(self.container, label)
    
    def _create_tab(self):
        """Create the tab's UI components"""
        # Main container
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Chat area (scrollable)
        self.chat_scroll = Gtk.ScrolledWindow()
        self.chat_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.chat_scroll.set_vexpand(True)
        
        # Messages container
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.messages_box.set_margin_left(8)
        self.messages_box.set_margin_right(8)
        self.messages_box.set_margin_top(8)
        
        self.chat_scroll.add(self.messages_box)
        self.container.pack_start(self.chat_scroll, True, True, 0)
        
        # Input area
        self._create_input_area()
    
    def _create_input_area(self):
        """Create the message input area"""
        input_frame = Gtk.Frame()
        input_frame.set_shadow_type(Gtk.ShadowType.IN)
        input_frame.get_style_context().add_class("input-area")
        
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        input_box.set_margin_left(8)
        input_box.set_margin_right(8)
        input_box.set_margin_top(8)
        input_box.set_margin_bottom(8)
        
        # Text input
        self.input_scroll = Gtk.ScrolledWindow()
        self.input_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.input_scroll.set_size_request(-1, 80)
        
        self.input_view = Gtk.TextView()
        self.input_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.input_view.get_style_context().add_class("input-text")
        
        # Connect Enter key
        self.input_view.connect("key-press-event", self._on_key_press)
        
        self.input_scroll.add(self.input_view)
        input_box.pack_start(self.input_scroll, True, True, 0)
        
        # Send button
        send_button = Gtk.Button(label="Send")
        send_button.get_style_context().add_class("send-button")
        send_button.connect("clicked", self._on_send_clicked)
        input_box.pack_end(send_button, False, False, 0)
        
        input_frame.add(input_box)
        self.container.pack_end(input_frame, False, False, 0)
    
    def _on_key_press(self, widget, event):
        """Handle key press in input area"""
        if event.keyval == Gdk.KEY_Return:
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                # Ctrl+Enter = new line
                return False
            else:
                # Enter = send message
                self._send_message()
                return True
        return False
    
    def _on_send_clicked(self, button):
        """Handle send button click"""
        self._send_message()
    
    def _send_message(self):
        """Send the current message"""
        buffer = self.input_view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False).strip()
        
        if text:
            # Clear input
            buffer.set_text("")
            
            # Add user message
            self.add_message("You", text, "user")
            
            # Get LLM response (would integrate with parent window)
            # For now, we'll add a placeholder
            # self._get_llm_response(text)
    
    def add_message(self, sender: str, content: str, role: str):
        """Add a message to the chat"""
        try:
            # Create message bubble
            message = MessageBubble(sender, content, role, config=self.config)
            
            # Add to messages container
            self.messages_box.pack_start(message, False, False, 0)
            message.show_all()
            
            # Scroll to bottom
            vadj = self.chat_scroll.get_vadjustment()
            GLib.idle_add(lambda: vadj.set_value(vadj.get_upper() - vadj.get_page_size()))
            
            # Add to conversation manager
            if role == "user":
                self.conversation_manager.add_user_message(content)
            elif role == "assistant":
                self.conversation_manager.add_assistant_message(content)
            
        except Exception as e:
            log_exception(e, "Failed to add message")
    
    def clear_chat(self):
        """Clear all messages"""
        for child in self.messages_box.get_children():
            self.messages_box.remove(child)

class GTKChatWindow(Gtk.Window):
    """
    Main GTK chat window.
    Replaces the Tkinter PersistentChatWindow class.
    """
    
    def __init__(self, app, config: Dict):
        super().__init__(title="Screenshot LLM Assistant")
        # app parameter kept for compatibility but not used in simple Window approach
        
        self.config = config
        self.tabs: Dict[str, GTKChatTab] = {}
        self.tab_counter = 0
        
        # Initialize components
        try:
            self.image_processor = get_image_processor()
        except Exception as e:
            logger.warning(f"Image processor initialization failed: {e}")
            self.image_processor = None
            
        try:
            self.llm_client = LLMClient(self.config.get('llm', {}))
        except Exception as e:
            logger.warning(f"LLM client initialization failed: {e}")
            self.llm_client = None
            
        try:
            self.ipc_manager = IPCManager()
            logger.info("IPC manager initialized successfully")
        except Exception as e:
            logger.error(f"IPC manager initialization failed: {e}")
            self.ipc_manager = None
        
        # Setup window
        logger.info("Setting up GTK window...")
        self._setup_window()
        
        logger.info("Loading GTK styles...")
        self._load_styles()
        
        logger.info("Creating GTK UI...")
        self._create_ui()
        
        logger.info("Starting IPC server...")
        self._start_ipc_server()
        
        logger.info("GTK Chat window initialized successfully")
    
    def _setup_window(self):
        """Configure the main window"""
        self.set_title("Screenshot LLM Assistant")
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Handle window close
        self.connect("delete-event", self._on_window_close)
    
    def _load_styles(self):
        """Load CSS styles for the chat window"""
        css = """
        /* GTK Chat Window Styles */
        .code-block {
            background-color: #1e1e1e;
            border: 1px solid #48b9c7;
            border-radius: 4px;
        }
        
        .code-header {
            background-color: #333333;
            border-bottom: 1px solid #555555;
        }
        
        .code-content {
            background-color: #1e1e1e;
            color: #f8f8f2;
            font-family: "SF Mono", "Consolas", monospace;
            font-size: 10px;
        }
        
        .copy-button {
            background: linear-gradient(135deg, #48b9c7, #5cc7d5);
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 9px;
        }
        
        .copy-button:hover {
            background: linear-gradient(135deg, #5cc7d5, #6dd0de);
        }
        
        .message-text {
            background-color: transparent;
            color: #ffffff;
            font-family: "SF Pro Display", sans-serif;
            font-size: 11px;
        }
        
        .input-area {
            background-color: #3c3c3c;
            border-top: 1px solid #48b9c7;
        }
        
        .input-text {
            background-color: #2d2d2d;
            color: #ffffff;
            font-family: "SF Pro Display", sans-serif;
            font-size: 11px;
        }
        
        .send-button {
            background: linear-gradient(135deg, #48b9c7, #5cc7d5);
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }
        
        .send-button:hover {
            background: linear-gradient(135deg, #5cc7d5, #6dd0de);
        }
        
        .timestamp {
            color: #b0b0b0;
            font-size: 9px;
        }
        """
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _create_ui(self):
        """Create the user interface"""
        # Header Bar
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = "Screenshot LLM Assistant"
        self.set_titlebar(header_bar)

        # Settings Button
        settings_button = Gtk.Button(label="Settings")
        settings_button.connect("clicked", self._on_settings_clicked)
        header_bar.pack_end(settings_button)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        main_box.pack_start(self.notebook, True, True, 0)
        
        # Create first tab
        logger.info("Creating first chat tab...")
        first_tab_id = self.new_tab()
        logger.info(f"Created first tab with ID: {first_tab_id}")
        
        # Add welcome message to first tab for testing
        if first_tab_id and first_tab_id in self.tabs:
            logger.info("Adding welcome message to first tab...")
            first_tab = self.tabs[first_tab_id]
            first_tab.add_message("System", "Welcome to Screenshot LLM Assistant GTK GUI!\n\nThis is the new modern interface. Use mouse button 9 to capture screenshots.", "system")
            logger.info("Welcome message added successfully")
        else:
            logger.error(f"Failed to get first tab - ID: {first_tab_id}, tabs: {list(self.tabs.keys())}")
        
        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("main")
        self.status_bar.push(self.status_context, "Ready - Waiting for screenshots...")
        main_box.pack_end(self.status_bar, False, False, 0)
    
    def _start_ipc_server(self):
        """Start the IPC server for receiving messages from daemon"""
        try:
            if self.ipc_manager is None:
                logger.warning("IPC manager not available, skipping IPC server")
                return
                
            logger.info("Creating IPC server...")
            self.ipc_server = self.ipc_manager.create_server()
            logger.info(f"IPC server created: {self.ipc_server}")
            
            # Register message handlers
            self.ipc_server.register_handler("screenshot", self._handle_screenshot_message)
            self.ipc_server.register_handler("show_window", self._handle_show_window)
            self.ipc_server.register_handler("hide_window", self._handle_hide_window)
            self.ipc_server.register_handler("add_message", self._handle_add_message)
            
            # Start server in background thread
            def start_server():
                try:
                    asyncio.run(self.ipc_server.start())
                except Exception as e:
                    log_exception(e, "IPC server failed")
            
            self.ipc_thread = threading.Thread(target=start_server, daemon=True)
            self.ipc_thread.start()
            
            logger.info("GTK IPC server started")
            
        except Exception as e:
            log_exception(e, "Failed to start IPC server")
    
    def new_tab(self) -> str:
        """Create a new chat tab"""
        try:
            self.tab_counter += 1
            tab_id = str(self.tab_counter)
            logger.info(f"Creating tab with ID: {tab_id}")
            
            # Create new tab
            logger.info("Creating GTKChatTab instance...")
            tab = GTKChatTab(self.notebook, tab_id, self.config)
            self.tabs[tab_id] = tab
            logger.info(f"Tab {tab_id} created and added to tabs dict")
            
            # Select the new tab
            page_num = self.notebook.page_num(tab.container)
            logger.info(f"Tab page number: {page_num}")
            self.notebook.set_current_page(page_num)
            
            # Ensure widgets are shown
            tab.container.show_all()
            
            logger.info(f"Created new GTK tab: {tab_id}")
            return tab_id
            
        except Exception as e:
            log_exception(e, "Failed to create new tab")
            return ""
    
    def get_current_tab(self) -> Optional[GTKChatTab]:
        """Get the currently selected tab"""
        try:
            current_page = self.notebook.get_current_page()
            current_widget = self.notebook.get_nth_page(current_page)
            
            # Find the tab that owns this widget
            for tab in self.tabs.values():
                if tab.container == current_widget:
                    return tab
            
            return None
            
        except Exception as e:
            log_exception(e, "Failed to get current tab")
            return None
    
    def _handle_screenshot_message(self, data: Dict):
        """Handle incoming screenshot from daemon"""
        try:
            image_path = data.get("image_path")
            context = data.get("context", {})
            
            if not image_path or not os.path.exists(image_path):
                logger.error(f"Screenshot file not found: {image_path}")
                return
            
            # Show window if hidden
            self.present()
            
            # Process screenshot in current tab
            self._process_screenshot(image_path, context)
            
            # Update status
            self.status_bar.push(self.status_context, "Processing screenshot...")
            
        except Exception as e:
            log_exception(e, "Failed to handle screenshot message")
    
    def _process_screenshot(self, image_path: str, context: Dict):
        """Process and display a new screenshot"""
        try:
            current_tab = self.get_current_tab()
            if not current_tab:
                return
            
            # Add screenshot message
            context_str = f"Screenshot from {context.get('app_name', 'unknown app')}"
            if context.get('window_title'):
                context_str += f" - {context['window_title']}"
            
            # For now, add as a simple message
            # TODO: Add proper image display support
            current_tab.add_message("System", f"📷 {context_str}", "system")
            
            # Get LLM response
            self._get_llm_response_for_screenshot(current_tab, image_path, context)
            
        except Exception as e:
            log_exception(e, "Failed to process screenshot")
    
    def _get_llm_response_for_screenshot(self, tab: GTKChatTab, image_path: str, context: Dict):
        """Get LLM response for a screenshot"""
        def get_response():
            try:
                # Build context prompt
                context_prompt = self._build_context_prompt(context)
                
                # Use asyncio to call the async LLM client
                async def async_get_response():
                    try:
                        # Get conversation messages for API
                        api_messages = tab.conversation_manager.get_messages_for_api()
                        
                        response = await self.llm_client.send_screenshot(image_path, context_prompt)
                        return response
                    except Exception as e:
                        log_exception(e, "LLM API call failed")
                        return "I apologize, but I encountered an error while analyzing the screenshot."
                
                # Run the async function
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(async_get_response())
                    loop.close()
                except Exception as e:
                    log_exception(e, "Asyncio execution failed")
                    response = "Failed to process the screenshot analysis request."
                
                # Display response in UI thread
                GLib.idle_add(lambda: tab.add_message("Assistant", response, "assistant"))
                GLib.idle_add(lambda: self.status_bar.push(self.status_context, "Analysis complete"))
                
            except Exception as e:
                log_exception(e, "Failed to get LLM response")
                GLib.idle_add(lambda: self.status_bar.push(self.status_context, "Failed to get LLM analysis"))
        
        # Run in background thread
        threading.Thread(target=get_response, daemon=True).start()
    
    def _build_context_prompt(self, context: Dict) -> str:
        """Build context prompt from application context"""
        parts = ["I'm currently working with:"]
        
        if context.get('app_name'):
            parts.append(f"- Application: {context['app_name']}")
        
        if context.get('window_title'):
            parts.append(f"- Window: {context['window_title']}")
        
        if context.get('working_directory'):
            parts.append(f"- Directory: {context['working_directory']}")
        
        return "\n".join(parts)
    
    def _handle_show_window(self, data: Dict):
        """Handle show window request"""
        self.present()
    
    def _handle_hide_window(self, data: Dict):
        """Handle hide window request"""
        self.hide()
    
    def _handle_add_message(self, data: Dict):
        """Handle adding a message from external source (like pop-up)"""
        try:
            sender = data.get("sender", "Assistant")
            content = data.get("content", "")
            role = data.get("role", "assistant")
            
            # Show window and bring to front
            self.present()
            self.show_all()
            
            # Add message to current tab
            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.add_message(sender, content, role)
                logger.info("Message added to chat from external source")
            else:
                logger.warning("No current tab to add message to")
                
        except Exception as e:
            log_exception(e, "Failed to handle add_message")
    
    def _on_window_close(self, widget, event):
        """Handle window close event"""
        # Properly shut down the application
        logger.info("Window close requested, shutting down application")
        
        # Stop IPC server if running
        if hasattr(self, 'ipc_server') and self.ipc_server:
            try:
                self.ipc_server.stop()
                logger.info("IPC server stopped")
            except Exception as e:
                logger.warning(f"Error stopping IPC server: {e}")
        
        # Quit GTK main loop
        Gtk.main_quit()
        return False  # Allow window to be destroyed

    def _on_settings_clicked(self, button):
        """Show the settings dialog."""
        dialog = SettingsWindow(self, self.config)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.config = dialog.save_settings()
            self._save_config()
            logger.info("Settings saved.")
        
        dialog.destroy()

    def _save_config(self):
        """Save the current configuration to file."""
        try:
            config_dir = os.path.expanduser("~/.local/share/screenshot-llm/config")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "config.json")
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            log_exception(e, "Failed to save configuration")

class GTKChatApplication(Gtk.Application):
    """GTK Application wrapper for the chat window"""
    
    def __init__(self, config: Dict):
        super().__init__(application_id="com.screenshot-llm.chat")
        self.config = config
        self.window = None
        
        self.connect("activate", self._on_activate)
    
    def _on_activate(self, app):
        """Application activation handler"""
        print("GTK Application activating...")
        if not self.window:
            print("Creating GTK Chat Window...")
            self.window = GTKChatWindow(app, self.config)
            print("GTK Chat Window created successfully")
        
        print("Presenting window...")
        self.window.present()
        self.window.show_all()

def main():
    """Main entry point for GTK chat window"""
    # Load configuration
    config_dir = os.path.expanduser("~/.local/share/screenshot-llm")
    config_path = os.path.join(config_dir, "config", "config.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        config = {}
    
    # Create and run GTK application
    app = GTKChatApplication(config)
    app.run(sys.argv)

if __name__ == "__main__":
    main()