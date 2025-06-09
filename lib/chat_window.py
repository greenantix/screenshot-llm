#!/usr/bin/env python3
"""
Chat window for Screenshot LLM Assistant
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import asyncio
import json
import os
import re
from typing import Optional, List, Dict
from PIL import Image, ImageTk
import io

from .conversation_manager import ConversationManager
from .conversation_browser import ConversationBrowser
from .tray_manager import TrayManager
from .image_processor import get_image_processor
from .logger import get_logger, log_exception
from .tab_manager import TabManager
from .llm_client import LLMClient
from .ipc_handler import IPCManager
import subprocess

logger = get_logger(__name__)

class PersistentChatWindow(tk.Tk):
    """Main persistent chat window for Screenshot LLM Assistant"""
    
    def __init__(self, config: Dict):
        super().__init__()
        
        # Use provided configuration
        self.config = config
        
        # Set up window
        self.title("Screenshot LLM Assistant")
        self._setup_window()
        
        # Initialize components
        self.image_processor = get_image_processor()
        self.llm_client = LLMClient(self.config.get('llm', {}))
        self.ipc_manager = IPCManager()
        self.tray_manager = None
        
        # Set up styles and UI
        self._setup_styles()
        self._create_ui()
        self._setup_keyboard_shortcuts()
        
        # Start IPC server
        self._start_ipc_server()
        
        logger.info("Chat window initialized successfully")
    
    # _load_config is no longer needed here, config is passed in.
    
    def _setup_window(self):
        """Configure the main window"""
        # Get theme colors
        theme = self.config.get("ui", {}).get("theme", {})
        self.bg_color = theme.get("background", "#2d2d2d")
        self.fg_color = theme.get("foreground", "#ffffff")
        self.accent_color = theme.get("accent", "#48b9c7")
        self.surface_color = theme.get("surface", "#3c3c3c")
        
        # Set window properties
        window_config = self.config.get("ui", {}).get("window", {})
        width = window_config.get("default_width", 800)
        height = window_config.get("default_height", 600)
        
        self.geometry(f"{width}x{height}")
        self.minsize(
            window_config.get("min_width", 400),
            window_config.get("min_height", 300)
        )
        
        # Configure window background
        self.configure(bg=self.bg_color)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _setup_styles(self):
        """Configure ttk styles with Pop!_OS inspired theme"""
        style = ttk.Style()
        
        # Define additional theme colors
        self.button_hover = "#5cc7d5"  # Lighter accent for hover
        self.button_pressed = "#3da4b0"  # Darker accent for pressed
        self.border_color = "#4a4a4a"  # Subtle border color
        self.text_secondary = "#b0b0b0"  # Secondary text color
        
        # Configure Frame styles
        style.configure("Custom.TFrame", 
                       background=self.bg_color,
                       relief="flat",
                       borderwidth=0)
        
        style.configure("Surface.TFrame",
                       background=self.surface_color,
                       relief="flat", 
                       borderwidth=1)
        
        # Configure Button styles with modern look
        style.configure("Custom.TButton",
                       background=self.accent_color,
                       foreground=self.fg_color,
                       borderwidth=0,
                       focuscolor="none",
                       relief="flat",
                       padding=(12, 6),
                       font=("SF Pro Display", 10, "normal"))
        
        style.map("Custom.TButton",
                 background=[("active", self.button_hover),
                           ("pressed", self.button_pressed),
                           ("disabled", self.surface_color)],
                 foreground=[("disabled", self.text_secondary)])
        
        # Secondary button style
        style.configure("Secondary.TButton",
                       background=self.surface_color,
                       foreground=self.fg_color,
                       borderwidth=1,
                       relief="solid",
                       focuscolor="none",
                       padding=(12, 6),
                       font=("SF Pro Display", 10, "normal"))
        
        style.map("Secondary.TButton",
                 background=[("active", self.border_color),
                           ("pressed", self.bg_color)],
                 bordercolor=[("active", self.accent_color)])
        
        # Configure Entry styles
        style.configure("Custom.TEntry",
                       fieldbackground=self.surface_color,
                       foreground=self.fg_color,
                       bordercolor=self.border_color,
                       lightcolor=self.surface_color,
                       darkcolor=self.surface_color,
                       borderwidth=1,
                       insertcolor=self.accent_color,
                       relief="solid",
                       padding=(8, 6),
                       font=("SF Pro Display", 10, "normal"))
        
        style.map("Custom.TEntry",
                 bordercolor=[("focus", self.accent_color)],
                 lightcolor=[("focus", self.accent_color)],
                 darkcolor=[("focus", self.accent_color)])
        
        # Configure Notebook styles
        style.configure("Custom.TNotebook",
                       background=self.bg_color,
                       borderwidth=0,
                       tabmargins=[0, 5, 0, 0])
                       
        style.configure("Custom.TNotebook.Tab",
                       background=self.surface_color,
                       foreground=self.fg_color,
                       borderwidth=1,
                       relief="solid",
                       padding=[12, 8],
                       font=("SF Pro Display", 10, "normal"))
        
        style.map("Custom.TNotebook.Tab",
                 background=[("selected", self.accent_color),
                           ("active", self.button_hover)],
                 foreground=[("selected", self.fg_color)],
                 bordercolor=[("selected", self.accent_color)])
        
        # Configure Label styles
        style.configure("Custom.TLabel",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=("SF Pro Display", 10, "normal"),
                       padding=2)
        
        style.configure("Heading.TLabel",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=("SF Pro Display", 12, "bold"),
                       padding=4)
        
        style.configure("Secondary.TLabel",
                       background=self.bg_color,
                       foreground=self.text_secondary,
                       font=("SF Pro Display", 9, "normal"),
                       padding=2)
        
        # Configure Scrollbar styles
        style.configure("Custom.Vertical.TScrollbar",
                       background=self.surface_color,
                       troughcolor=self.bg_color,
                       borderwidth=0,
                       arrowcolor=self.fg_color,
                       darkcolor=self.surface_color,
                       lightcolor=self.surface_color)
        
        style.map("Custom.Vertical.TScrollbar",
                 background=[("active", self.accent_color)])
        
        # Configure Separator styles
        style.configure("Custom.TSeparator",
                       background=self.border_color)
        
        # Configure Progressbar styles
        style.configure("Custom.Horizontal.TProgressbar",
                       background=self.accent_color,
                       troughcolor=self.surface_color,
                       borderwidth=0,
                       lightcolor=self.accent_color,
                       darkcolor=self.accent_color)
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to system clipboard"""
        try:
            # Use wl-copy for Wayland or xclip for X11
            if os.environ.get('WAYLAND_DISPLAY'):
                subprocess.run(['wl-copy'], input=text.encode(), timeout=5, check=True)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), timeout=5, check=True)
            
            self.status_bar.configure(text="Code copied to clipboard")
            logger.info("Code copied to clipboard")
            
            # Reset status after 2 seconds
            self.after(2000, lambda: self.status_bar.configure(text="Ready"))
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            self.status_bar.configure(text="Failed to copy - clipboard tool not available")
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            self.status_bar.configure(text="Error copying to clipboard")
    
    def _create_ui(self):
        """Create the user interface"""
        # Create main container
        self.main_container = ttk.Frame(self, style="Custom.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tab manager
        self.tab_manager = TabManager(self.main_container, self.config)
        self.tab_manager.pack(fill=tk.BOTH, expand=True)
        
        # Set up status bar
        self._setup_status_bar()
    
    def _setup_status_bar(self):
        """Set up the status bar at the bottom of the window"""
        self.status_bar = ttk.Label(
            self,
            text="Ready - Waiting for screenshots...",
            style="Custom.TLabel"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for various actions"""
        # Tab management
        self.bind("<Control-t>", lambda e: self.tab_manager.new_tab())
        self.bind("<Control-w>", lambda e: self._close_current_tab())
        
        # Conversation management
        self.bind("<Control-n>", lambda e: self._new_conversation())
        self.bind("<Control-s>", lambda e: self._save_conversation())
        self.bind("<Control-l>", lambda e: self._load_conversation())
        
        # Copy operations
        self.bind("<Control-c>", lambda e: self._copy_selected_text())
        self.bind("<Control-Shift-C>", lambda e: self._copy_all_text())
        
        # Window management
        self.bind("<Escape>", lambda e: self._minimize_to_tray())
        self.bind("<Control-q>", lambda e: self.quit())
    
    def _start_ipc_server(self):
        """Start the IPC server for receiving messages from daemon"""
        try:
            self.ipc_server = self.ipc_manager.create_server()
            
            # Register message handlers
            self.ipc_server.register_handler("screenshot", self._handle_screenshot_message)
            self.ipc_server.register_handler("show_window", self._handle_show_window)
            self.ipc_server.register_handler("hide_window", self._handle_hide_window)
            
            # Start server in background thread
            def start_server():
                try:
                    asyncio.run(self.ipc_server.start())
                except Exception as e:
                    log_exception(e, "IPC server failed")
            
            self.ipc_thread = threading.Thread(target=start_server, daemon=True)
            self.ipc_thread.start()
            
            logger.info("IPC server started")
            
        except Exception as e:
            log_exception(e, "Failed to start IPC server")
    
    def _handle_screenshot_message(self, data: Dict):
        """Handle incoming screenshot from daemon"""
        try:
            image_path = data.get("image_path")
            context = data.get("context", {})
            
            if not image_path or not os.path.exists(image_path):
                logger.error(f"Screenshot file not found: {image_path}")
                return
            
            # Read screenshot data
            with open(image_path, 'rb') as f:
                screenshot_data = f.read()
            
            # Show window if hidden
            self.deiconify()
            self.lift()
            
            # Process screenshot in current tab
            self._process_screenshot(screenshot_data, context, image_path)
            
            # Update status
            self.status_bar.configure(text="Processing screenshot...")
            
        except Exception as e:
            log_exception(e, "Failed to handle screenshot message")
    
    def _handle_show_window(self, data: Dict):
        """Handle show window request"""
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def _handle_hide_window(self, data: Dict):
        """Handle hide window request"""
        self.withdraw()
    
    def _process_screenshot(self, screenshot_data: bytes, context: Dict, image_path: str = None):
        """Process and display a new screenshot"""
        try:
            current_tab = self.tab_manager.get_current_tab()
            if not current_tab:
                return
            
            # Create thumbnail asynchronously
            def on_thumbnail_ready(thumbnail_data: bytes):
                try:
                    # Create thumbnail image for display
                    image = Image.open(io.BytesIO(thumbnail_data))
                    photo = ImageTk.PhotoImage(image)
                    
                    # Store reference to prevent garbage collection
                    if not hasattr(current_tab, '_photo_references'):
                        current_tab._photo_references = []
                    current_tab._photo_references.append(photo)
                    
                    # Add thumbnail to chat
                    current_tab.chat_display.configure(state=tk.NORMAL)
                    
                    # Add screenshot with context info
                    context_str = f"Screenshot from {context.get('app_name', 'unknown app')}"
                    if context.get('window_title'):
                        context_str += f" - {context['window_title']}"
                    
                    current_tab.chat_display.insert(tk.END, f"\n📷 {context_str}\n", "bold")
                    current_tab.chat_display.image_create(tk.END, image=photo)
                    
                    # Make image clickable
                    tag_name = f"screenshot_{len(current_tab._photo_references)}"
                    current_tab.chat_display.tag_add(tag_name, "end-2c", "end-1c")
                    current_tab.chat_display.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e: self._show_full_image(screenshot_data)
                    )
                    current_tab.chat_display.tag_configure(tag_name, background=self.surface_color)
                    
                    current_tab.chat_display.insert(tk.END, "\n\n")
                    current_tab.chat_display.configure(state=tk.DISABLED)
                    current_tab.chat_display.see(tk.END)
                    
                    # Add to conversation with image path if available
                    if image_path:
                        current_tab.conversation_manager.add_screenshot_message(image_path, context)
                    
                    # Get LLM response
                    self._get_llm_response_for_screenshot(current_tab, context)
                    
                except Exception as e:
                    log_exception(e, "Failed to display screenshot thumbnail")
                    self._display_error("Failed to display screenshot")
            
            # Process image asynchronously
            self.image_processor.process_image_async(
                screenshot_data,
                callback=on_thumbnail_ready,
                optimize=True,
                thumbnail=True
            )
            
        except Exception as e:
            log_exception(e, "Failed to process screenshot")
            self._display_error("Failed to process screenshot")
    
    def _get_llm_response_for_screenshot(self, tab, context: Dict):
        """Get LLM response for a screenshot in a separate thread"""
        def get_response():
            try:
                # Build context prompt
                context_prompt = self._build_context_prompt(context)
                
                # Get conversation messages for API
                api_messages = tab.conversation_manager.get_messages_for_api()
                
                # Use asyncio to call the async LLM client
                async def async_get_response():
                    try:
                        response = await self.llm_client.send_conversation(
                            api_messages,
                            context_prompt
                        )
                        return response
                    except Exception as e:
                        log_exception(e, "LLM API call failed")
                        return "I apologize, but I encountered an error while analyzing the screenshot. Please check your API configuration and try again."
                
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
                self.after(0, lambda: self._display_llm_response(tab, response))
                
            except Exception as e:
                log_exception(e, "Failed to get LLM response")
                self.after(0, lambda: self._display_error("Failed to get LLM analysis"))
        
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
    
    def _display_llm_response(self, tab, response: str):
        """Display LLM response in the chat"""
        try:
            tab.chat_display.configure(state=tk.NORMAL)
            
            # Add timestamp and label
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M")
            
            tab.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            tab.chat_display.insert(tk.END, "Assistant: ", "bold")
            
            # Parse and display markdown response with copy buttons
            self._parse_markdown(response, tab.chat_display)
            
            tab.chat_display.insert(tk.END, "\n\n")
            tab.chat_display.configure(state=tk.DISABLED)
            tab.chat_display.see(tk.END)
            
            # Add to conversation
            tab.conversation_manager.add_assistant_message(response)
            
            # Update status
            self.status_bar.configure(text="Analysis complete")
            
        except Exception as e:
            log_exception(e, "Failed to display LLM response")
    
    def _parse_markdown(self, text: str, text_widget: tk.Text):
        """Parse and display markdown formatted text with copy code buttons"""
        import re
        
        # Configure text tags for styling
        text_widget.tag_configure("header1", font=("SF Pro Display", 14, "bold"), foreground=self.accent_color)
        text_widget.tag_configure("header2", font=("SF Pro Display", 12, "bold"), foreground=self.accent_color)
        text_widget.tag_configure("header3", font=("SF Pro Display", 11, "bold"), foreground=self.accent_color)
        text_widget.tag_configure("code", font=("SF Mono", 10), background=self.surface_color, foreground="#f8f8f2")
        text_widget.tag_configure("code_block", font=("SF Mono", 10), background=self.surface_color, foreground="#f8f8f2")
        text_widget.tag_configure("bold", font=("SF Pro Display", 10, "bold"))
        text_widget.tag_configure("italic", font=("SF Pro Display", 10, "italic"))
        
        # Split text into parts, handling code blocks specially
        parts = re.split(r'(```[\w]*\n.*?\n```)', text, flags=re.DOTALL)
        
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # This is a code block
                self._insert_code_block(text_widget, part)
            else:
                # Regular markdown text
                self._parse_regular_markdown(text_widget, part)
    
    def _insert_code_block(self, text_widget: tk.Text, code_block: str):
        """Insert a code block with syntax highlighting and copy button"""
        lines = code_block.strip().split('\n')
        if len(lines) < 2:
            return
        
        # Extract language and code
        first_line = lines[0]
        language = first_line[3:].strip() if len(first_line) > 3 else "text"
        code_content = '\n'.join(lines[1:-1])  # Remove ``` lines
        
        if not code_content.strip():
            return
        
        # Insert code block header with language and copy button
        text_widget.insert(tk.END, f"\n{language.title()} Code:\n", "bold")
        
        # Apply syntax highlighting
        code_start = text_widget.index(tk.END)
        self._insert_highlighted_code(text_widget, code_content, language)
        code_end = text_widget.index(tk.END)
        
        # Create copy button frame
        button_frame = tk.Frame(text_widget, bg=self.bg_color)
        copy_button = ttk.Button(
            button_frame,
            text="📋 Copy",
            style="Secondary.TButton",
            command=lambda: self._copy_to_clipboard(code_content)
        )
        copy_button.pack(pady=2)
        
        # Insert button as window in text widget
        text_widget.insert(tk.END, "\n")
        text_widget.window_create(tk.END, window=button_frame)
        text_widget.insert(tk.END, "\n\n")
        
        # Add border around code block
        text_widget.tag_add("code_block_border", code_start, code_end)
        text_widget.tag_configure("code_block_border", 
                                 relief="solid", 
                                 borderwidth=1,
                                 bgstipple="gray50")
    
    def _insert_highlighted_code(self, text_widget: tk.Text, code: str, language: str):
        """Insert code with syntax highlighting"""
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name, guess_lexer
            from pygments.formatters import TerminalFormatter
            from pygments.token import Token
            from pygments.util import ClassNotFound
            
            # Map language names to pygments lexer names
            language_map = {
                'js': 'javascript',
                'ts': 'typescript', 
                'py': 'python',
                'sh': 'bash',
                'shell': 'bash',
                'yml': 'yaml',
                'dockerfile': 'docker'
            }
            
            # Get the lexer
            try:
                lexer_name = language_map.get(language.lower(), language.lower())
                lexer = get_lexer_by_name(lexer_name)
            except ClassNotFound:
                try:
                    # Try to guess the lexer
                    lexer = guess_lexer(code)
                except:
                    # Fallback to plain text
                    text_widget.insert(tk.END, code, "code_block")
                    return
            
            # Define color scheme for dark theme
            token_colors = {
                Token.Keyword: "#ff79c6",           # Pink
                Token.String: "#f1fa8c",            # Yellow
                Token.Comment: "#6272a4",           # Blue-gray
                Token.Number: "#bd93f9",            # Purple
                Token.Operator: "#ff79c6",          # Pink
                Token.Name.Function: "#50fa7b",     # Green
                Token.Name.Class: "#8be9fd",        # Cyan
                Token.Name.Variable: "#f8f8f2",     # White
                Token.Name.Builtin: "#8be9fd",      # Cyan
                Token.Literal: "#f1fa8c",           # Yellow
            }
            
            # Tokenize the code
            tokens = list(lexer.get_tokens(code))
            
            for token_type, token_value in tokens:
                # Find the most specific color for this token
                color = None
                for token_class, token_color in token_colors.items():
                    if token_type in token_class:
                        color = token_color
                        break
                
                # Create unique tag for this token type
                tag_name = f"token_{str(token_type).replace('.', '_')}"
                if color:
                    text_widget.tag_configure(tag_name, 
                                             foreground=color,
                                             background=self.surface_color,
                                             font=("SF Mono", 10))
                    text_widget.insert(tk.END, token_value, tag_name)
                else:
                    text_widget.insert(tk.END, token_value, "code_block")
                    
        except Exception as e:
            # Fallback to plain code block if highlighting fails
            logger.warning(f"Syntax highlighting failed: {e}")
            text_widget.insert(tk.END, code, "code_block")
    
    def _parse_regular_markdown(self, text_widget: tk.Text, text: str):
        """Parse regular markdown text (non-code blocks)"""
        lines = text.split("\n")
        
        for line in lines:
            if line.startswith("# "):
                text_widget.insert(tk.END, line[2:] + "\n", "header1")
            elif line.startswith("## "):
                text_widget.insert(tk.END, line[3:] + "\n", "header2")
            elif line.startswith("### "):
                text_widget.insert(tk.END, line[4:] + "\n", "header3")
            elif "`" in line:
                # Handle inline code
                self._parse_inline_code(text_widget, line)
                text_widget.insert(tk.END, "\n")
            else:
                # Handle bold and italic
                self._parse_text_formatting(text_widget, line)
                text_widget.insert(tk.END, "\n")
    
    def _parse_inline_code(self, text_widget: tk.Text, line: str):
        """Parse line with inline code (`code`)"""
        import re
        parts = re.split(r'(`[^`]+`)', line)
        
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                # Inline code
                code_text = part[1:-1]  # Remove backticks
                text_widget.insert(tk.END, code_text, "code")
            else:
                # Regular text
                self._parse_text_formatting(text_widget, part)
    
    def _parse_text_formatting(self, text_widget: tk.Text, text: str):
        """Parse bold and italic formatting"""
        import re
        
        # Handle **bold** and *italic*
        parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', text)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Bold text
                text_widget.insert(tk.END, part[2:-2], "bold")
            elif part.startswith('*') and part.endswith('*'):
                # Italic text
                text_widget.insert(tk.END, part[1:-1], "italic")
            else:
                # Regular text
                text_widget.insert(tk.END, part)
    
    def _show_full_image(self, image_data: bytes):
        """Display full-size image in a new window"""
        try:
            # Create new window
            window = tk.Toplevel(self)
            window.title("Screenshot Viewer")
            window.configure(bg=self.bg_color)
            
            # Process image for display
            def on_image_ready(optimized_data: bytes):
                try:
                    image = Image.open(io.BytesIO(optimized_data))
                    
                    # Scale down if too large for screen
                    screen_width = window.winfo_screenwidth()
                    screen_height = window.winfo_screenheight()
                    max_width = int(screen_width * 0.8)
                    max_height = int(screen_height * 0.8)
                    
                    if image.width > max_width or image.height > max_height:
                        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    # Create label with image
                    label = tk.Label(window, image=photo, bg=self.bg_color)
                    label.image = photo  # Keep reference
                    label.pack(padx=10, pady=10)
                    
                    # Add close button
                    close_btn = ttk.Button(
                        window,
                        text="Close",
                        style="Custom.TButton",
                        command=window.destroy
                    )
                    close_btn.pack(pady=(0, 10))
                    
                    # Center window
                    window.geometry(f"{image.width + 20}x{image.height + 60}")
                    window.transient(self)
                    
                except Exception as e:
                    log_exception(e, "Failed to display full image")
                    window.destroy()
            
            # Process image asynchronously
            self.image_processor.process_image_async(
                image_data,
                callback=on_image_ready,
                optimize=True,
                thumbnail=False
            )
            
        except Exception as e:
            log_exception(e, "Failed to create image viewer")
    
    def _send_message_from_tab(self, tab, message: str):
        """Handle message sent from a tab"""
        try:
            # Add user message to display
            tab.add_message("You", message, "user")
            
            # Get LLM response in background
            self._get_llm_response_for_message(tab, message)
            
        except Exception as e:
            log_exception(e, "Failed to send message")
    
    def _get_llm_response_for_message(self, tab, message: str):
        """Get LLM response for a user message"""
        def get_response():
            try:
                # Get conversation messages for API
                api_messages = tab.conversation_manager.get_messages_for_api()
                
                # Use asyncio to call the async LLM client
                async def async_get_response():
                    try:
                        response = await self.llm_client.send_conversation(api_messages)
                        return response
                    except Exception as e:
                        log_exception(e, "LLM API call failed")
                        return "I apologize, but I encountered an error while processing your message. Please check your API configuration and try again."
                
                # Run the async function
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(async_get_response())
                    loop.close()
                except Exception as e:
                    log_exception(e, "Asyncio execution failed")
                    response = "Failed to process your message."
                
                # Display response in UI thread
                self.after(0, lambda: tab.add_message("Assistant", response, "assistant"))
                
            except Exception as e:
                log_exception(e, "Failed to get LLM response for message")
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def _close_current_tab(self):
        """Close the current tab"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab and len(self.tab_manager.tabs) > 1:
            # Find the tab ID
            tab_id = None
            for tid, tab in self.tab_manager.tabs.items():
                if tab == current_tab:
                    tab_id = tid
                    break
            
            if tab_id:
                self.tab_manager.close_tab(tab_id)
    
    def _new_conversation(self):
        """Start a new conversation"""
        self.tab_manager.new_tab()
    
    def _save_conversation(self):
        """Save the current conversation"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            current_tab.conversation_manager.save_conversation()
            self.status_bar.configure(text="Conversation saved")
    
    def _load_conversation(self):
        """Load a conversation"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            conversations = current_tab.conversation_manager.list_conversations()
            if conversations:
                ConversationBrowser(self, conversations, self._on_conversation_selected)
            else:
                messagebox.showinfo("No Conversations", "No saved conversations found.")
    
    def _on_conversation_selected(self, conversation_id: str):
        """Handle conversation selection"""
        # Create new tab and load conversation
        tab_id = self.tab_manager.new_tab()
        if tab_id:
            tab = self.tab_manager.tabs[tab_id]
            if tab.conversation_manager.load_conversation(conversation_id):
                # Display loaded messages (simplified)
                tab.clear_chat()
                for msg in tab.conversation_manager.messages:
                    role = "You" if msg["role"] == "user" else "Assistant"
                    tab.add_message(role, msg["content"], msg["role"])
                
                self.status_bar.configure(text=f"Loaded conversation {conversation_id}")
            else:
                self.tab_manager.close_tab(tab_id)
                messagebox.showerror("Error", "Failed to load conversation")
    
    def _copy_selected_text(self):
        """Copy selected text to clipboard"""
        try:
            current_tab = self.tab_manager.get_current_tab()
            if current_tab:
                selected = current_tab.chat_display.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.clipboard_clear()
                self.clipboard_append(selected)
                self.status_bar.configure(text="Selected text copied")
        except tk.TclError:
            pass  # No selection
    
    def _copy_all_text(self):
        """Copy all conversation text to clipboard"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            all_text = current_tab.chat_display.get("1.0", tk.END)
            self.clipboard_clear()
            self.clipboard_append(all_text)
            self.status_bar.configure(text="Conversation copied to clipboard")
    
    def _minimize_to_tray(self):
        """Minimize window to system tray"""
        try:
            if not self.tray_manager:
                self.tray_manager = TrayManager(
                    show_window=self._restore_from_tray,
                    quit_app=self.quit
                )
                self.tray_manager.start()
            
            self.withdraw()
            
        except Exception as e:
            log_exception(e, "Failed to minimize to tray")
    
    def _restore_from_tray(self):
        """Restore window from system tray"""
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def _on_window_close(self):
        """Handle window close event"""
        # Minimize to tray instead of closing
        self._minimize_to_tray()
    
    def _display_error(self, message: str):
        """Display an error message"""
        self.status_bar.configure(text=f"Error: {message}")
        logger.error(message)
    
    def quit(self):
        """Clean up and quit the application"""
        try:
            # Save current conversation
            current_tab = self.tab_manager.get_current_tab()
            if current_tab:
                current_tab.conversation_manager.save_conversation()
            
            # Stop IPC server
            if hasattr(self, 'ipc_server'):
                self.ipc_server.stop()
            
            # Clean up tray manager
            if self.tray_manager:
                self.tray_manager.cleanup()
            
            # Clean up image processor
            self.image_processor.cleanup()
            
        except Exception as e:
            log_exception(e, "Error during cleanup")
        finally:
            self.destroy()

# Backward compatibility
ChatWindow = PersistentChatWindow

if __name__ == "__main__":
    # Test the chat window
    window = PersistentChatWindow()
    window.mainloop()