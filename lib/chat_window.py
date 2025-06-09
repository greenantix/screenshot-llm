#!/usr/bin/env python3
"""
Persistent Chat Window for Screenshot LLM Assistant

Tkinter-based chat interface that maintains conversation history
and allows continuous interaction with the LLM.
"""

import asyncio
import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image, ImageTk
import subprocess
import re
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import TerminalFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

# Add lib directory to path
lib_path = os.path.dirname(__file__)
sys.path.insert(0, lib_path)

from conversation import ConversationManager
from ipc_handler import IPCManager, IPCMessage
from llm_client import LLMClient

logger = logging.getLogger(__name__)

class PersistentChatWindow:
    def __init__(self, config_dir: str = "~/.local/share/screenshot-llm"):
        self.config_dir = os.path.expanduser(config_dir)
        self.root = None
        self.conversation_manager = ConversationManager(config_dir)
        self.llm_client = LLMClient()
        self.ipc_manager = IPCManager(config_dir)
        self.ipc_server = None
        
        # GUI components
        self.chat_display = None
        self.input_entry = None
        self.status_label = None
        self.send_button = None
        
        # State
        self.is_visible = True
        self.conversation_active = False
        self.last_screenshot_time = 0  # Debounce mechanism
        
        # Create new conversation on startup
        self.conversation_manager.create_new_conversation()
        
    def create_window(self):
        """Create the main chat window"""
        self.root = tk.Tk()
        self.root.title("Screenshot LLM Assistant v2.0")
        self.root.geometry("1000x750")
        self.root.minsize(700, 500)
        
        # Configure style
        self._setup_styles()
        
        # Set window properties for modern appearance
        self.root.configure(bg=self.bg_color)
        
        # Try to set window icon (optional)
        try:
            # You could add an icon file here
            pass
        except:
            pass
        
        # Create menu bar
        self._create_menu()
        
        # Create header
        self._create_header()
        
        # Create main layout
        self._create_layout()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Start IPC server
        self._start_ipc_server()
        
        logger.info("Chat window created")
    
    def _setup_styles(self):
        """Setup GUI styling with Pop!_OS theme"""
        style = ttk.Style()
        
        # Pop!_OS inspired color scheme
        self.bg_color = "#2d2d2d"           # Pop!_OS dark background
        self.surface_color = "#3c3c3c"      # Card/surface color
        self.fg_color = "#f7f7f7"           # Main text
        self.fg_secondary = "#cccccc"       # Secondary text
        self.accent_color = "#48b9c7"       # Pop!_OS teal accent
        self.accent_hover = "#5ebdcc"       # Lighter teal
        self.user_color = "#48b9c7"         # User message teal
        self.assistant_color = "#4a4a4a"    # Assistant message gray
        self.screenshot_color = "#574c7a"   # Purple for screenshots
        self.error_color = "#f85149"        # Red for errors
        self.success_color = "#3fb950"      # Green for success
        
        # Configure ttk styles with Pop!_OS theme
        style.theme_use('clam')
        
        # Main window styling
        style.configure('Chat.TFrame', 
                       background=self.bg_color,
                       relief='flat')
        
        # Button styling
        style.configure('Accent.TButton',
                       background=self.accent_color,
                       foreground='white',
                       borderwidth=0,
                       relief='flat',
                       padding=(16, 8))
        
        style.map('Accent.TButton',
                 background=[('active', self.accent_hover),
                           ('pressed', '#3a9aa5')])
        
        # Entry styling
        style.configure('Modern.TEntry',
                       fieldbackground=self.surface_color,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.accent_color)
        
        # Label styling
        style.configure('Header.TLabel',
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=('SF Pro Display', 11))
        
        style.configure('Status.TLabel',
                       background=self.bg_color,
                       foreground=self.fg_secondary,
                       font=('SF Pro Display', 9))
        
        # Scrollbar styling
        style.configure('Modern.Vertical.TScrollbar',
                       background=self.surface_color,
                       troughcolor=self.bg_color,
                       borderwidth=0,
                       arrowcolor=self.fg_secondary,
                       darkcolor=self.surface_color,
                       lightcolor=self.surface_color)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root,
                         bg=self.surface_color,
                         fg=self.fg_color,
                         activebackground=self.accent_color,
                         activeforeground='white',
                         borderwidth=0)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0,
                           bg=self.surface_color,
                           fg=self.fg_color,
                           activebackground=self.accent_color,
                           activeforeground='white',
                           borderwidth=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Conversation", command=self._new_conversation)
        file_menu.add_command(label="Load Conversation", command=self._load_conversation)
        file_menu.add_command(label="Save Conversation", command=self._save_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Export as Text", command=self._export_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._quit_application)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0,
                           bg=self.surface_color,
                           fg=self.fg_color,
                           activebackground=self.accent_color,
                           activeforeground='white',
                           borderwidth=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy All", command=self._copy_all_text)
        edit_menu.add_command(label="Clear Conversation", command=self._clear_conversation)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0,
                           bg=self.surface_color,
                           fg=self.fg_color,
                           activebackground=self.accent_color,
                           activeforeground='white',
                           borderwidth=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Minimize to Tray", command=self._minimize_to_tray)
        view_menu.add_command(label="Always on Top", command=self._toggle_always_on_top)
    
    def _create_header(self):
        """Create modern header with branding"""
        header_frame = tk.Frame(self.root, bg=self.surface_color, height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Left side - app info
        left_frame = tk.Frame(header_frame, bg=self.surface_color)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=12)
        
        # App title
        title_label = tk.Label(left_frame, 
                              text="Screenshot LLM Assistant", 
                              font=('SF Pro Display', 14, 'bold'),
                              fg=self.fg_color, 
                              bg=self.surface_color)
        title_label.pack(side=tk.LEFT)
        
        # Version badge
        version_label = tk.Label(left_frame, 
                               text="v2.0", 
                               font=('SF Pro Display', 10),
                               fg=self.accent_color, 
                               bg=self.surface_color)
        version_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # Right side - status indicators
        right_frame = tk.Frame(header_frame, bg=self.surface_color)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=12)
        
        # Connection status
        self.connection_status = tk.Label(right_frame, 
                                        text="🟢 Connected", 
                                        font=('SF Pro Display', 10),
                                        fg=self.success_color, 
                                        bg=self.surface_color)
        self.connection_status.pack(side=tk.RIGHT)
        
        # Separator line
        separator = tk.Frame(self.root, height=1, bg=self.accent_color)
        separator.pack(fill=tk.X)
    
    def _create_layout(self):
        """Create the main window layout"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Chat.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat display area (scrollable)
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('SF Pro Display', 11),  # Pop!_OS system font
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.accent_color,
            selectbackground=self.accent_color,
            selectforeground='white',
            borderwidth=0,
            highlightthickness=0,
            relief='flat',
            padx=16,
            pady=12
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different message types
        self._configure_text_tags()
        
        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Input field
        self.input_entry = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            font=('SF Pro Display', 11),
            bg=self.surface_color,
            fg=self.fg_color,
            insertbackground=self.accent_color,
            selectbackground=self.accent_color,
            selectforeground='white',
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.accent_color,
            relief='solid',
            padx=12,
            pady=8
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self._send_message,
            style='Accent.TButton'
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready - Waiting for screenshots or user input",
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Conversation info label
        self.conv_info_label = ttk.Label(
            status_frame,
            text="",
            style='Status.TLabel'
        )
        self.conv_info_label.pack(side=tk.RIGHT)
        
        self._update_conversation_info()
    
    def _configure_text_tags(self):
        """Configure text tags for message formatting with Pop!_OS styling"""
        # Timestamp styling
        self.chat_display.tag_configure('timestamp', 
                                      foreground=self.fg_secondary, 
                                      font=('SF Pro Display', 9))
        
        # Message labels with emojis
        self.chat_display.tag_configure('user_label', 
                                      foreground=self.accent_color, 
                                      font=('SF Pro Display', 11, 'bold'))
        self.chat_display.tag_configure('assistant_label', 
                                      foreground=self.success_color, 
                                      font=('SF Pro Display', 11, 'bold'))
        self.chat_display.tag_configure('screenshot_label', 
                                      foreground=self.screenshot_color, 
                                      font=('SF Pro Display', 11, 'bold'))
        
        # Message content styling - modern card-like appearance
        self.chat_display.tag_configure('user_message', 
                                      foreground=self.fg_color,
                                      background=self.user_color,
                                      lmargin1=20, lmargin2=20, rmargin=20,
                                      spacing1=8, spacing3=8,
                                      borderwidth=1, relief='solid')
        
        self.chat_display.tag_configure('assistant_message', 
                                      foreground=self.fg_color,
                                      background=self.assistant_color,
                                      lmargin1=20, lmargin2=20, rmargin=20,
                                      spacing1=8, spacing3=8,
                                      borderwidth=1, relief='solid')
        
        self.chat_display.tag_configure('screenshot_message', 
                                      foreground=self.fg_color,
                                      background=self.screenshot_color,
                                      lmargin1=20, lmargin2=20, rmargin=20,
                                      spacing1=8, spacing3=8,
                                      borderwidth=1, relief='solid')
        
        # Code block styling - enhanced for markdown
        self.chat_display.tag_configure('code_block', 
                                      foreground='#e6edf3',
                                      background='#161b22',
                                      font=('JetBrains Mono', 10),
                                      lmargin1=30, lmargin2=30, rmargin=30,
                                      spacing1=4, spacing3=4,
                                      borderwidth=1, relief='solid')
        
        # Inline code styling
        self.chat_display.tag_configure('code_inline', 
                                      foreground='#f85149',
                                      background='#2d2d2d',
                                      font=('JetBrains Mono', 10))
        
        # Headers for markdown
        self.chat_display.tag_configure('header1', 
                                      foreground=self.accent_color,
                                      font=('SF Pro Display', 16, 'bold'),
                                      spacing1=12, spacing3=6)
        
        self.chat_display.tag_configure('header2', 
                                      foreground=self.accent_color,
                                      font=('SF Pro Display', 14, 'bold'),
                                      spacing1=10, spacing3=4)
        
        # Bold and italic
        self.chat_display.tag_configure('bold', font=('SF Pro Display', 11, 'bold'))
        self.chat_display.tag_configure('italic', font=('SF Pro Display', 11, 'italic'))
        
        # Links
        self.chat_display.tag_configure('link', 
                                      foreground=self.accent_color,
                                      underline=True)
        
        # Error styling
        self.chat_display.tag_configure('error', 
                                      foreground=self.error_color,
                                      background='#2d1b1b')
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-Return>', lambda e: self._send_message())
        self.root.bind('<Control-n>', lambda e: self._new_conversation())
        self.root.bind('<Control-s>', lambda e: self._save_conversation())
        self.root.bind('<Control-q>', lambda e: self._quit_application())
        self.root.bind('<Escape>', lambda e: self._minimize_to_tray())
        
        # Focus input entry by default
        self.input_entry.focus_set()
    
    def _start_ipc_server(self):
        """Start IPC server in background thread"""
        def run_server():
            self.ipc_server = self.ipc_manager.create_server()
            
            # Register message handlers
            self.ipc_server.register_handler('screenshot', self._handle_screenshot)
            self.ipc_server.register_handler('llm_response', self._handle_llm_response)
            self.ipc_server.register_handler('show_window', self._handle_show_window)
            self.ipc_server.register_handler('hide_window', self._handle_hide_window)
            
            # Run server event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.ipc_server.start())
            except Exception as e:
                logger.error(f"IPC server error: {e}")
            finally:
                loop.close()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        logger.info("IPC server started in background")
    
    def _handle_screenshot(self, data: Dict[str, Any]):
        """Handle screenshot received from daemon"""
        import time
        
        # Debounce mechanism to prevent double screenshots
        current_time = time.time()
        if current_time - self.last_screenshot_time < 2.0:  # 2 second debounce
            logger.debug("Screenshot ignored due to debounce")
            return
        
        self.last_screenshot_time = current_time
        
        image_path = data.get('image_path')
        context = data.get('context', {})
        
        if image_path:
            logger.info(f"Processing screenshot: {image_path}")
            
            # Add screenshot to conversation
            message = self.conversation_manager.add_screenshot_message(image_path, context)
            
            # Update GUI in main thread
            self.root.after(0, lambda: self._display_screenshot_message(message))
            
            # Send to LLM and get response in a new thread to avoid blocking GUI
            import threading
            threading.Thread(
                target=lambda: asyncio.run(self._process_screenshot_with_llm(image_path, context)),
                daemon=True
            ).start()
    
    def _handle_llm_response(self, data: Dict[str, Any]):
        """Handle LLM response from daemon"""
        response_text = data.get('response', '')
        
        if response_text:
            # Add to conversation
            message = self.conversation_manager.add_assistant_message(response_text)
            
            # Update GUI in main thread
            self.root.after(0, lambda: self._display_assistant_message(message))
    
    def _handle_show_window(self, data: Dict[str, Any]):
        """Handle show window request"""
        self.root.after(0, self.show_window)
    
    def _handle_hide_window(self, data: Dict[str, Any]):
        """Handle hide window request"""
        self.root.after(0, self._minimize_to_tray)
    
    async def _process_screenshot_with_llm(self, image_path: str, context: Dict[str, Any]):
        """Process screenshot with LLM using full conversation context"""
        try:
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Processing screenshot with LLM..."))
            
            # Get full conversation context for LLM
            response_text = await self._get_llm_response_with_full_context(image_path, context)
            
            if response_text:
                # Add response to conversation
                message = self.conversation_manager.add_assistant_message(response_text)
                
                # Display in GUI
                self.root.after(0, lambda: self._display_assistant_message(message))
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
            error_msg = f"Error processing screenshot: {str(e)}"
            self.root.after(0, lambda: self._display_error(error_msg))
    
    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context data for LLM prompt"""
        if not context:
            return "Help me with this screenshot."
        
        parts = []
        
        if context.get('app_name'):
            parts.append(f"I'm using {context['app_name']}")
        
        if context.get('window_title'):
            parts.append(f"Window: {context['window_title']}")
        
        if context.get('working_dir'):
            parts.append(f"Working directory: {context['working_dir']}")
        
        context_text = ". ".join(parts) if parts else "I need help"
        return f"{context_text}. Help me with:"
    
    async def _get_llm_response_with_full_context(self, image_path: str, context: Dict[str, Any]) -> str:
        """Get LLM response using full conversation context"""
        try:
            # Get all conversation messages formatted for API
            api_messages = self.conversation_manager.get_messages_for_api()
            
            # Build context prompt for the new screenshot
            context_prompt = self._format_context_for_llm(context)
            
            if not api_messages:
                # First message - just send the screenshot
                return await self.llm_client.send_screenshot(image_path, context_prompt)
            
            # We have conversation history - need to format it properly for the LLM API
            if self.llm_client.config['provider'] == 'anthropic':
                return await self._send_to_anthropic_with_context(api_messages, image_path, context_prompt)
            elif self.llm_client.config['provider'] == 'openai':
                return await self._send_to_openai_with_context(api_messages, image_path, context_prompt)
            else:
                # Fallback to simple screenshot processing
                return await self.llm_client.send_screenshot(image_path, context_prompt)
                
        except Exception as e:
            logger.error(f"Error getting LLM response with context: {e}")
            # Fallback to simple processing
            context_prompt = self._format_context_for_llm(context)
            return await self.llm_client.send_screenshot(image_path, context_prompt)
    
    async def _send_to_anthropic_with_context(self, api_messages: list, image_path: str, context_prompt: str) -> str:
        """Send conversation with new screenshot to Anthropic Claude"""
        try:
            # Convert conversation messages to Anthropic format
            claude_messages = []
            
            for msg in api_messages:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # Handle mixed content (text + images)
                        claude_content = []
                        for item in content:
                            if item.get('type') == 'text':
                                claude_content.append({
                                    "type": "text",
                                    "text": item.get('text', '')
                                })
                            elif item.get('type') == 'image_path':
                                # Skip old images - we'll only include the new one
                                pass
                        
                        if claude_content:
                            claude_messages.append({
                                "role": "user",
                                "content": claude_content
                            })
                    else:
                        # Simple text message
                        claude_messages.append({
                            "role": "user", 
                            "content": content
                        })
                        
                elif msg.get('role') == 'assistant':
                    claude_messages.append({
                        "role": "assistant",
                        "content": msg.get('content', '')
                    })
            
            # Add the new screenshot message
            image_data = self.llm_client._encode_image(image_path)
            mime_type = self.llm_client._get_image_mime_type(image_path)
            
            new_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{context_prompt}\n\nThis is a new screenshot. Please analyze it in the context of our conversation."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }
            
            claude_messages.append(new_message)
            
            # Send to Claude
            response = await self.llm_client.client.messages.create(
                model=self.llm_client.config['model'],
                max_tokens=self.llm_client.config['max_tokens'],
                messages=claude_messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error sending to Anthropic with context: {e}")
            raise
    
    async def _send_to_openai_with_context(self, api_messages: list, image_path: str, context_prompt: str) -> str:
        """Send conversation with new screenshot to OpenAI"""
        try:
            # Convert conversation messages to OpenAI format
            openai_messages = []
            
            for msg in api_messages:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # Handle mixed content (text + images)
                        openai_content = []
                        for item in content:
                            if item.get('type') == 'text':
                                openai_content.append({
                                    "type": "text",
                                    "text": item.get('text', '')
                                })
                            elif item.get('type') == 'image_path':
                                # Skip old images - we'll only include the new one
                                pass
                        
                        if openai_content:
                            openai_messages.append({
                                "role": "user",
                                "content": openai_content
                            })
                    else:
                        # Simple text message
                        openai_messages.append({
                            "role": "user",
                            "content": content
                        })
                        
                elif msg.get('role') == 'assistant':
                    openai_messages.append({
                        "role": "assistant",
                        "content": msg.get('content', '')
                    })
            
            # Add the new screenshot message
            image_data = self.llm_client._encode_image(image_path)
            mime_type = self.llm_client._get_image_mime_type(image_path)
            
            new_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{context_prompt}\n\nThis is a new screenshot. Please analyze it in the context of our conversation."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }
            
            openai_messages.append(new_message)
            
            # Send to OpenAI
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.config['model'],
                max_tokens=self.llm_client.config['max_tokens'],
                messages=openai_messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error sending to OpenAI with context: {e}")
            raise
    
    def _parse_markdown(self, text: str) -> list:
        """Parse markdown text into formatted segments"""
        segments = []
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Code blocks
            if line.strip().startswith('```'):
                # Start of code block
                language = line.strip()[3:].strip()
                code_lines = []
                i += 1
                
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    segments.append(('code_block', code_text))
                
                i += 1
                continue
            
            # Headers
            elif line.startswith('# '):
                segments.append(('header1', line[2:]))
            elif line.startswith('## '):
                segments.append(('header2', line[3:]))
            
            # Regular text with inline formatting
            else:
                if line.strip():  # Non-empty line
                    formatted_line = self._parse_inline_formatting(line)
                    segments.extend(formatted_line)
                else:
                    segments.append(('normal', '\n'))
            
            i += 1
        
        return segments
    
    def _parse_inline_formatting(self, line: str) -> list:
        """Parse inline markdown formatting"""
        segments = []
        
        # Simple regex patterns for inline formatting
        import re
        
        # Split by code blocks first
        parts = re.split(r'(`[^`]+`)', line)
        
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                # Inline code
                segments.append(('code_inline', part[1:-1]))
            else:
                # Check for bold/italic
                bold_parts = re.split(r'(\*\*[^*]+\*\*)', part)
                for bold_part in bold_parts:
                    if bold_part.startswith('**') and bold_part.endswith('**'):
                        segments.append(('bold', bold_part[2:-2]))
                    else:
                        # Check for italic
                        italic_parts = re.split(r'(\*[^*]+\*)', bold_part)
                        for italic_part in italic_parts:
                            if italic_part.startswith('*') and italic_part.endswith('*'):
                                segments.append(('italic', italic_part[1:-1]))
                            else:
                                if italic_part:
                                    segments.append(('normal', italic_part))
        
        segments.append(('normal', '\n'))
        return segments
    
    async def _get_llm_response_from_conversation(self) -> str:
        """Get LLM response using full conversation context"""
        try:
            api_messages = self.conversation_manager.get_messages_for_api()
            
            if not api_messages:
                return ""
            
            # For now, just use the last message (screenshot)
            # TODO: Implement full conversation context
            last_message = api_messages[-1]
            
            if last_message.get('role') == 'user' and 'content' in last_message:
                content = last_message['content']
                
                # Find image and text content
                text_content = ""
                image_data = None
                mime_type = None
                
                for item in content:
                    if item.get('type') == 'text':
                        text_content = item.get('text', '')
                    elif item.get('type') == 'image' and 'source' in item:
                        source = item['source']
                        if source.get('type') == 'base64':
                            image_data = source.get('data')
                            mime_type = source.get('media_type')
                
                if image_data and mime_type:
                    # Use LLM client with direct data
                    if self.llm_client.config['provider'] == 'anthropic':
                        message = {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": text_content},
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": image_data
                                    }
                                }
                            ]
                        }
                        
                        response = await self.llm_client.client.messages.create(
                            model=self.llm_client.config['model'],
                            max_tokens=self.llm_client.config['max_tokens'],
                            messages=[message]
                        )
                        
                        return response.content[0].text
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"Error getting response: {str(e)}"
    
    def _display_screenshot_message(self, message: Dict[str, Any]):
        """Display screenshot message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Timestamp
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Screenshot label
        self.chat_display.insert(tk.END, "📸 Screenshot: ", 'screenshot_label')
        self.chat_display.insert(tk.END, f"{message['content']}\n", 'screenshot_message')
        
        # Try to display thumbnail
        image_path = message.get('image_path')
        if image_path and os.path.exists(image_path):
            try:
                # Create thumbnail
                thumbnail = self._create_thumbnail(image_path)
                if thumbnail:
                    # Insert image in text widget
                    self.chat_display.image_create(tk.END, image=thumbnail)
                    self.chat_display.insert(tk.END, " ")  # Space after image
                    
                    # Store reference to prevent garbage collection
                    if not hasattr(self, '_image_refs'):
                        self._image_refs = []
                    self._image_refs.append(thumbnail)
                    
                    # Make image clickable to view full size
                    self._make_image_clickable(image_path)
                
            except Exception as e:
                logger.warning(f"Could not display thumbnail for {image_path}: {e}")
                # Fallback: just show filename
                self.chat_display.insert(tk.END, f"   [Image: {os.path.basename(image_path)}]", 'screenshot_message')
        
        self.chat_display.insert(tk.END, "\n")
        
        # Context info
        context = message.get('context', {})
        if context:
            context_text = self._format_context_for_display(context)
            self.chat_display.insert(tk.END, f"   {context_text}\n", 'screenshot_message')
        
        self.chat_display.insert(tk.END, "\n")
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self._update_conversation_info()
    
    def _create_thumbnail(self, image_path: str, max_size: tuple = (200, 150)) -> Optional[ImageTk.PhotoImage]:
        """Create thumbnail image for display in chat"""
        try:
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage for Tkinter
                return ImageTk.PhotoImage(img)
                
        except Exception as e:
            logger.warning(f"Could not create thumbnail: {e}")
            return None
    
    def _make_image_clickable(self, image_path: str):
        """Make the last inserted image clickable to view full size"""
        try:
            # Get current text widget state and indices
            current_index = self.chat_display.index("end-2c")  # Get position before the last newline
            
            # Create a unique tag for this image
            tag_name = f"clickable_image_{len(self._image_refs) if hasattr(self, '_image_refs') else 0}"
            
            # Apply tag to the image that was just inserted
            # We need to find the image position - it should be just before current position
            try:
                # Search backwards for the image
                search_start = self.chat_display.index("end-10c")
                img_start = self.chat_display.search("image", search_start, current_index)
                
                if img_start:
                    # Create a tag around the image area
                    img_end = f"{img_start}+1c"
                    self.chat_display.tag_add(tag_name, img_start, img_end)
                    
                    # Configure the tag for visual feedback
                    self.chat_display.tag_configure(tag_name, 
                                                  borderwidth=1,
                                                  relief='solid',
                                                  background=self.accent_color)
                    
                    # Bind click event to the tag
                    self.chat_display.tag_bind(tag_name, '<Button-1>', 
                                             lambda e: self._show_full_image(image_path))
                    
                    # Change cursor on hover
                    self.chat_display.tag_bind(tag_name, '<Enter>', 
                                             lambda e: self.chat_display.config(cursor='hand2'))
                    self.chat_display.tag_bind(tag_name, '<Leave>', 
                                             lambda e: self.chat_display.config(cursor=''))
                    
                    # Add a small text hint
                    self.chat_display.insert(tk.END, " 🔍", 'image_hint')
                    self.chat_display.tag_configure('image_hint', 
                                                  foreground=self.accent_color,
                                                  font=('SF Pro Display', 8))
                    self.chat_display.tag_bind('image_hint', '<Button-1>', 
                                             lambda e: self._show_full_image(image_path))
                    
                else:
                    # Fallback: add a text link
                    self.chat_display.insert(tk.END, " [Click to view full size]", 'image_link')
                    self.chat_display.tag_configure('image_link', 
                                                  foreground=self.accent_color, 
                                                  underline=True,
                                                  font=('SF Pro Display', 10))
                    self.chat_display.tag_bind('image_link', '<Button-1>', 
                                             lambda e: self._show_full_image(image_path))
                    
            except Exception as search_error:
                logger.debug(f"Could not find image for tagging: {search_error}")
                # Simple fallback
                self.chat_display.insert(tk.END, " [View Full Size]", 'image_link')
                self.chat_display.tag_configure('image_link', 
                                              foreground=self.accent_color, 
                                              underline=True)
                self.chat_display.tag_bind('image_link', '<Button-1>', 
                                         lambda e: self._show_full_image(image_path))
            
        except Exception as e:
            logger.warning(f"Could not make image clickable: {e}")
    
    def _show_full_image(self, image_path: str):
        """Show full-size image in a new window"""
        try:
            if not os.path.exists(image_path):
                messagebox.showerror("Image Error", "Image file not found")
                return
            
            # Create new window for full-size image
            image_window = tk.Toplevel(self.root)
            image_window.title(f"Screenshot - {os.path.basename(image_path)}")
            image_window.transient(self.root)
            
            # Load full-size image
            with Image.open(image_path) as img:
                # Get screen dimensions to limit window size
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Scale image if too large for screen (leave some margin)
                max_width = screen_width - 100
                max_height = screen_height - 200
                
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Create label to display image
                label = tk.Label(image_window, image=photo)
                label.pack(padx=10, pady=10)
                
                # Keep reference to prevent garbage collection
                label.image = photo
                
                # Set window size and center it
                image_window.geometry(f"{img.width + 20}x{img.height + 20}")
                
                # Center window on screen
                x = (screen_width - img.width) // 2
                y = (screen_height - img.height) // 2
                image_window.geometry(f"+{x}+{y}")
                
                # Add close button
                close_btn = tk.Button(image_window, text="Close", 
                                    command=image_window.destroy)
                close_btn.pack(pady=5)
                
        except Exception as e:
            logger.error(f"Could not show full image: {e}")
            messagebox.showerror("Image Error", f"Could not display image: {e}")
    
    def _display_assistant_message(self, message: Dict[str, Any]):
        """Display assistant message with markdown formatting"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Timestamp
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Assistant label
        self.chat_display.insert(tk.END, "🤖 Assistant:\n", 'assistant_label')
        
        # Parse and render markdown content
        content = message['content']
        markdown_segments = self._parse_markdown(content)
        
        # Render each segment with appropriate formatting
        for segment_type, segment_text in markdown_segments:
            if segment_type == 'normal':
                self.chat_display.insert(tk.END, segment_text, 'assistant_message')
            elif segment_type == 'code_block':
                self.chat_display.insert(tk.END, f"\n{segment_text}\n", 'code_block')
            elif segment_type == 'code_inline':
                self.chat_display.insert(tk.END, segment_text, 'code_inline')
            elif segment_type == 'bold':
                self.chat_display.insert(tk.END, segment_text, 'bold')
            elif segment_type == 'italic':
                self.chat_display.insert(tk.END, segment_text, 'italic')
            elif segment_type == 'header1':
                self.chat_display.insert(tk.END, f"\n{segment_text}\n", 'header1')
            elif segment_type == 'header2':
                self.chat_display.insert(tk.END, f"\n{segment_text}\n", 'header2')
            else:
                self.chat_display.insert(tk.END, segment_text, 'assistant_message')
        
        self.chat_display.insert(tk.END, "\n\n")
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self._update_conversation_info()
    
    def _display_user_message(self, message: Dict[str, Any]):
        """Display user message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Timestamp
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # User label
        self.chat_display.insert(tk.END, "👤 You: ", 'user_label')
        self.chat_display.insert(tk.END, f"{message['content']}\n\n", 'user_message')
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self._update_conversation_info()
    
    def _display_error(self, error_text: str):
        """Display error message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.chat_display.insert(tk.END, "❌ Error: ", 'error')
        self.chat_display.insert(tk.END, f"{error_text}\n\n", 'error')
        
        # Auto-scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Update status
        self.status_label.config(text="Error occurred - Check logs")
    
    def _format_context_for_display(self, context: Dict[str, Any]) -> str:
        """Format context for display in chat"""
        parts = []
        
        if context.get('app'):
            parts.append(f"App: {context['app']}")
        
        if context.get('window_title'):
            parts.append(f"Window: {context['window_title']}")
        
        if context.get('working_directory'):
            parts.append(f"Dir: {context['working_directory']}")
        
        return " | ".join(parts) if parts else "No context"
    
    def _update_conversation_info(self):
        """Update conversation info display"""
        summary = self.conversation_manager.get_conversation_summary()
        self.conv_info_label.config(text=summary)
    
    def _send_message(self):
        """Send user message"""
        text = self.input_entry.get("1.0", tk.END).strip()
        
        if not text:
            return
        
        # Clear input
        self.input_entry.delete("1.0", tk.END)
        
        # Add to conversation
        message = self.conversation_manager.add_user_message(text)
        
        # Display in chat
        self._display_user_message(message)
        
        # Get LLM response in a separate thread
        import threading
        threading.Thread(
            target=lambda: asyncio.run(self._get_user_message_response()),
            daemon=True
        ).start()
    
    async def _get_user_message_response(self):
        """Get LLM response to user message using conversation context"""
        try:
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Getting response..."))
            
            # Get LLM response using full conversation context
            response_text = await self._get_llm_response_for_text_only()
            
            if response_text:
                # Add response to conversation
                message = self.conversation_manager.add_assistant_message(response_text)
                
                # Display in GUI
                self.root.after(0, lambda: self._display_assistant_message(message))
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            
        except Exception as e:
            logger.error(f"Error getting user message response: {e}")
            error_msg = f"Error getting response: {str(e)}"
            self.root.after(0, lambda: self._display_error(error_msg))
    
    async def _get_llm_response_for_text_only(self) -> str:
        """Get LLM response for text-only conversation (no new images)"""
        try:
            # Get all conversation messages
            api_messages = self.conversation_manager.get_messages_for_api()
            
            if not api_messages:
                return "I don't see any conversation history. Please share a screenshot or ask a specific question."
            
            # Convert messages to the appropriate format for the LLM provider
            if self.llm_client.config['provider'] == 'anthropic':
                return await self._send_text_to_anthropic(api_messages)
            elif self.llm_client.config['provider'] == 'openai':
                return await self._send_text_to_openai(api_messages)
            else:
                return "I can only respond when a specific LLM provider is configured."
                
        except Exception as e:
            logger.error(f"Error getting text-only LLM response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def _send_text_to_anthropic(self, api_messages: list) -> str:
        """Send text conversation to Anthropic Claude"""
        try:
            claude_messages = []
            
            for msg in api_messages:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # Extract only text content, skip images
                        text_parts = []
                        for item in content:
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                        
                        if text_parts:
                            claude_messages.append({
                                "role": "user",
                                "content": " ".join(text_parts)
                            })
                    else:
                        claude_messages.append({
                            "role": "user",
                            "content": content
                        })
                        
                elif msg.get('role') == 'assistant':
                    claude_messages.append({
                        "role": "assistant",
                        "content": msg.get('content', '')
                    })
            
            response = await self.llm_client.client.messages.create(
                model=self.llm_client.config['model'],
                max_tokens=self.llm_client.config['max_tokens'],
                messages=claude_messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error sending text to Anthropic: {e}")
            raise
    
    async def _send_text_to_openai(self, api_messages: list) -> str:
        """Send text conversation to OpenAI"""
        try:
            openai_messages = []
            
            for msg in api_messages:
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # Extract only text content, skip images
                        text_parts = []
                        for item in content:
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                        
                        if text_parts:
                            openai_messages.append({
                                "role": "user",
                                "content": " ".join(text_parts)
                            })
                    else:
                        openai_messages.append({
                            "role": "user",
                            "content": content
                        })
                        
                elif msg.get('role') == 'assistant':
                    openai_messages.append({
                        "role": "assistant",
                        "content": msg.get('content', '')
                    })
            
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.config['model'],
                max_tokens=self.llm_client.config['max_tokens'],
                messages=openai_messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error sending text to OpenAI: {e}")
            raise
    
    def _new_conversation(self):
        """Start new conversation"""
        if messagebox.askyesno("New Conversation", "Start a new conversation? Current conversation will be saved."):
            self.conversation_manager.save_conversation()
            self.conversation_manager.create_new_conversation()
            
            # Clear chat display
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            self._update_conversation_info()
            self.status_label.config(text="New conversation started")
    
    def _load_conversation(self):
        """Load conversation from file"""
        try:
            # Get list of available conversations
            conversations = self.conversation_manager.list_conversations()
            
            if not conversations:
                messagebox.showinfo("Load Conversation", "No saved conversations found.")
                return
            
            # Create conversation selection dialog
            self._show_conversation_browser(conversations)
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load conversations: {e}")
    
    def _show_conversation_browser(self, conversations):
        """Show conversation browser dialog"""
        # Create new window for conversation browser
        browser_window = tk.Toplevel(self.root)
        browser_window.title("Load Conversation")
        browser_window.geometry("600x400")
        browser_window.transient(self.root)
        browser_window.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(browser_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Instructions
        ttk.Label(main_frame, text="Select a conversation to load:").pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for conversations
        columns = ('ID', 'Created', 'Messages', 'Last Activity')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        tree.heading('ID', text='Conversation ID')
        tree.heading('Created', text='Created')
        tree.heading('Messages', text='Messages')
        tree.heading('Last Activity', text='Last Activity')
        
        tree.column('ID', width=200)
        tree.column('Created', width=120)
        tree.column('Messages', width=80)
        tree.column('Last Activity', width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate conversations
        for conv in conversations:
            created = conv.get('created', 'Unknown')
            if created != 'Unknown':
                try:
                    created = datetime.fromisoformat(created).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            last_activity = conv.get('last_activity', 'Unknown')
            if last_activity != 'Unknown':
                try:
                    last_activity = datetime.fromisoformat(last_activity).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            tree.insert('', tk.END, values=(
                conv.get('id', 'Unknown'),
                created,
                conv.get('message_count', 0),
                last_activity
            ))
        
        # Button frame
        button_frame = ttk.Frame(browser_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        # Selected conversation variable
        selected_conv = {'id': None}
        
        def on_select():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                conv_id = item['values'][0]
                selected_conv['id'] = conv_id
        
        def on_load():
            if selected_conv['id']:
                try:
                    # Load the conversation
                    success = self.conversation_manager.load_conversation(selected_conv['id'])
                    if success:
                        # Refresh the chat display
                        self._refresh_chat_display()
                        self.status_label.config(text=f"Loaded conversation: {selected_conv['id']}")
                        browser_window.destroy()
                    else:
                        messagebox.showerror("Load Error", "Failed to load conversation")
                except Exception as e:
                    messagebox.showerror("Load Error", f"Error loading conversation: {e}")
            else:
                messagebox.showwarning("No Selection", "Please select a conversation to load")
        
        def on_delete():
            if selected_conv['id']:
                if messagebox.askyesno("Delete Conversation", 
                                     f"Delete conversation '{selected_conv['id']}'?\nThis cannot be undone."):
                    try:
                        # Find and delete the conversation file
                        conv_file = os.path.join(self.conversation_manager.conversations_dir, 
                                               f"{selected_conv['id']}.json")
                        if os.path.exists(conv_file):
                            os.remove(conv_file)
                            messagebox.showinfo("Deleted", "Conversation deleted successfully")
                            browser_window.destroy()
                            # Reopen browser with updated list
                            self._load_conversation()
                        else:
                            messagebox.showerror("Delete Error", "Conversation file not found")
                    except Exception as e:
                        messagebox.showerror("Delete Error", f"Failed to delete conversation: {e}")
            else:
                messagebox.showwarning("No Selection", "Please select a conversation to delete")
        
        # Bind selection event
        tree.bind('<<TreeviewSelect>>', lambda e: on_select())
        tree.bind('<Double-1>', lambda e: on_load())
        
        # Buttons
        ttk.Button(button_frame, text="Load", command=on_load).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=on_delete).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=browser_window.destroy).pack(side=tk.RIGHT)
    
    def _refresh_chat_display(self):
        """Refresh chat display with loaded conversation"""
        # Clear current display
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        
        # Display all messages from loaded conversation
        for message in self.conversation_manager.messages:
            if message['type'] == 'screenshot':
                self._display_screenshot_message(message)
            elif message['type'] == 'user':
                self._display_user_message(message)
            elif message['type'] == 'assistant':
                self._display_assistant_message(message)
        
        self.chat_display.config(state=tk.DISABLED)
        self._update_conversation_info()
    
    def _save_conversation(self):
        """Save current conversation"""
        try:
            filepath = self.conversation_manager.save_conversation()
            self.status_label.config(text=f"Conversation saved: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save conversation: {e}")
    
    def _export_conversation(self):
        """Export conversation as text"""
        if not self.conversation_manager.messages:
            messagebox.showwarning("Export", "No conversation to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(f"Screenshot LLM Assistant - Conversation Export\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for msg in self.conversation_manager.messages:
                        timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M:%S')
                        msg_type = msg['type'].capitalize()
                        f.write(f"[{timestamp}] {msg_type}: {msg['content']}\n\n")
                
                self.status_label.config(text=f"Exported to: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def _copy_all_text(self):
        """Copy all conversation text to clipboard"""
        text = self.chat_display.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_label.config(text="All text copied to clipboard")
    
    def _clear_conversation(self):
        """Clear current conversation"""
        if messagebox.askyesno("Clear Conversation", "Clear the current conversation? This cannot be undone."):
            self.conversation_manager.clear_conversation()
            
            # Clear chat display
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            self._update_conversation_info()
            self.status_label.config(text="Conversation cleared")
    
    def _minimize_to_tray(self):
        """Minimize window (hide from taskbar)"""
        self.root.withdraw()
        self.is_visible = False
        logger.info("Window minimized to tray")
    
    def _toggle_always_on_top(self):
        """Toggle always on top mode"""
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)
        status = "enabled" if not current else "disabled"
        self.status_label.config(text=f"Always on top {status}")
    
    def _on_window_close(self):
        """Handle window close button"""
        # Minimize instead of closing
        self._minimize_to_tray()
    
    def _quit_application(self):
        """Quit the application completely"""
        if messagebox.askyesno("Quit", "Quit Screenshot LLM Assistant?"):
            # Save conversation
            try:
                self.conversation_manager.save_conversation()
            except:
                pass
            
            # Stop IPC server
            if self.ipc_server:
                self.ipc_server.stop()
            
            self.root.quit()
            self.root.destroy()
    
    def show_window(self):
        """Show/focus the window"""
        if not self.is_visible:
            self.root.deiconify()
        
        self.root.lift()
        self.root.focus_force()
        self.is_visible = True
        logger.info("Window shown and focused")
    
    def run(self):
        """Start the chat window"""
        if not self.root:
            self.create_window()
        
        logger.info("Starting chat window main loop")
        self.root.mainloop()

def main():
    """Main entry point for the chat window"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        chat_window = PersistentChatWindow()
        chat_window.run()
    except KeyboardInterrupt:
        logger.info("Chat window stopped by user")
    except Exception as e:
        logger.error(f"Chat window error: {e}")

if __name__ == "__main__":
    main()