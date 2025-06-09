import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List, Dict
import json
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
import re
from PIL import Image, ImageTk
import io
from .conversation_manager import ConversationManager
from .conversation_browser import ConversationBrowser
from .tray_manager import TrayManager
from .image_processor import get_image_processor
from .logger import get_logger, log_exception
from .tab_manager import TabManager

logger = get_logger()

class ChatWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Screenshot LLM Assistant")
        self.geometry("800x600")
        
        try:
            # Initialize components
            self.image_processor = get_image_processor()
            
            # Create main container
            self.main_container = ttk.Frame(self)
            self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create notebook first
            self.tab_manager = TabManager(self.main_container, {})
            
            # Set up styles
            self._setup_styles()
            
            # Pack tab manager
            self.tab_manager.pack(fill=tk.BOTH, expand=True)
            
            # Initialize UI
            self._setup_status_bar()
            self._setup_keyboard_shortcuts()
            
            get_logger().info("Chat window initialized successfully")
            
        except Exception as e:
            log_exception(e, "Failed to initialize chat window")
            raise
        

    def _setup_styles(self):
        """Configure ttk styles for the GUI"""
        style = ttk.Style()
        
        # Pop!_OS inspired colors
        bg_color = "#2d2d2d"
        fg_color = "#ffffff"
        accent_color = "#48b9c7"
        
        # Configure styles for all widgets
        style.configure("Custom.TFrame",
                      background=bg_color)
        
        style.configure("Custom.TButton",
                      background=accent_color,
                      foreground=fg_color,
                      padding=5)
        
        style.configure("Custom.TEntry",
                      fieldbackground=bg_color,
                      foreground=fg_color,
                      padding=5)
        
        style.configure("Custom.TNotebook",
                      background=bg_color,
                      tabmargins=[0, 5, 0, 0])
                      
        style.configure("Custom.TNotebook.Tab",
                      background=bg_color,
                      foreground=fg_color,
                      padding=[10, 2],
                      font=("SF Pro Display", 10))
        
        style.map("Custom.TNotebook.Tab",
                background=[("selected", accent_color)],
                foreground=[("selected", fg_color)])
        
        style.configure("Custom.TLabel",
                      background=bg_color,
                      foreground=fg_color,
                      padding=2)
        
        # Apply styles to tab manager if it exists
        if hasattr(self, 'tab_manager'):
            self.tab_manager.configure(style="Custom.TNotebook")



    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for various actions"""
        # Tab management
        self.bind("<Control-t>", lambda e: self.tab_manager.new_tab())
        self.bind("<Control-w>", lambda e: self._close_current_tab())
        self.bind("<Control-Tab>", lambda e: self._next_tab())
        self.bind("<Control-Shift-Tab>", lambda e: self._prev_tab())
        
        # Conversation management
        self.bind("<Control-n>", lambda e: self._new_conversation())
        self.bind("<Control-s>", lambda e: self._save_conversation())
        self.bind("<Control-l>", lambda e: self._load_conversation())
        
        # Copy operations
        self.bind("<Control-c>", lambda e: self._copy_selected_text())
        self.bind("<Control-Shift-C>", lambda e: self._copy_all_text())
        
        # Window management
        self.bind("<Escape>", lambda e: self._minimize_to_tray())

    def _close_current_tab(self):
        """Close the current tab"""
        current = self.tab_manager.get_current_tab()
        if current:
            self.tab_manager.close_tab(
                next(k for k, v in self.tab_manager.tabs.items()
                     if v == current)
            )

    def _next_tab(self):
        """Switch to next tab"""
        current = self.tab_manager.index(self.tab_manager.select())
        total = self.tab_manager.index("end")
        self.tab_manager.select((current + 1) % total)

    def _prev_tab(self):
        """Switch to previous tab"""
        current = self.tab_manager.index(self.tab_manager.select())
        total = self.tab_manager.index("end")
        self.tab_manager.select((current - 1) % total)

    def _setup_status_bar(self):
        """Set up the status bar at the bottom of the window"""
        self.status_bar = ttk.Label(self,
                                  text="Ready",
                                  style="Custom.TLabel")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

    def _setup_markdown_tags(self, chat_display: tk.Text):
        """Configure markdown formatting tags for a text widget"""
        tag_configs = {
            "bold": {"font": ("SF Pro Display", 11, "bold")},
            "italic": {"font": ("SF Pro Display", 11, "italic")},
            "code": {"font": ("SF Mono", 11)},
            "code_block": {
                "font": ("SF Mono", 11),
                "background": "#363636",
                "spacing1": 10,
                "spacing3": 10
            },
            "link": {
                "foreground": "#48b9c7",
                "underline": True
            },
            "blockquote": {
                "lmargin1": 20,
                "lmargin2": 20,
                "background": "#363636",
                "font": ("SF Pro Display", 11, "italic")
            },
            "hr": {
                "foreground": "#48b9c7",
                "spacing1": 10,
                "spacing3": 10,
                "justify": "center"
            }
        }
        
        for tag, config in tag_configs.items():
            chat_display.tag_configure(tag, **config)

    def _send_message(self):
        """Handle sending a message"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        message = current_tab.get_input_text()
        if message:
            # Clear input field
            current_tab.clear_input()
            
            # Add message to conversation
            current_tab.conversation_manager.add_message("user", message)
            
            # Display message
            self._display_message("You", message)
            
            # Get LLM response
            threading.Thread(target=self._get_llm_response_from_conversation,
                          args=(current_tab,)).start()

    def _display_message(self, sender: str, message: str):
        """Display a message in the current tab with markdown formatting"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        # Enable editing
        current_tab.chat_display.configure(state=tk.NORMAL)
        
        # Add sender with timestamp
        current_tab.chat_display.insert(tk.END, f"{sender}: ", "bold")
        
        # Parse and display message with markdown formatting
        self._parse_markdown(message, current_tab.chat_display)
        
        # Add newline
        current_tab.chat_display.insert(tk.END, "\n\n")
        
        # Disable editing and scroll to bottom
        current_tab.chat_display.configure(state=tk.DISABLED)
        current_tab.chat_display.see(tk.END)

    def _parse_markdown(self, text: str, chat_display: tk.Text):
        """Parse and display markdown formatted text"""
        lines = text.split("\n")
        in_code_block = False
        code_block_lang = None
        code_block_content = []
        in_list = False
        list_indent = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code block
            if line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                    i += 1
                    continue
                else:
                    in_code_block = False
                    if code_block_content:
                        self._insert_code_block("\n".join(code_block_content), code_block_lang)
                    code_block_content = []
                    i += 1
                    continue
            
            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue
            
            # Check for horizontal rule
            if re.match(r'^([-*_])\1{2,}$', line):
                chat_display.insert(tk.END, "\n")
                chat_display.insert(tk.END, "─" * 40, "hr")
                chat_display.insert(tk.END, "\n")
                i += 1
                continue
            
            # Check for blockquote
            if line.startswith(">"):
                quote_text = line[1:].strip()
                chat_display.insert(tk.END, quote_text, "blockquote")
                chat_display.insert(tk.END, "\n")
                i += 1
                continue
            
            # Check for list items
            list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', line)
            if list_match:
                indent = len(list_match.group(1))
                marker = list_match.group(2)
                content = list_match.group(3)
                
                if not in_list or indent != list_indent:
                    in_list = True
                    list_indent = indent
                
                # Add bullet point and content
                chat_display.insert(tk.END, "  " * (indent // 2))
                chat_display.insert(tk.END, "• " if marker in "-*+" else f"{marker} ")
                self._parse_inline_formatting(content, chat_display)
                chat_display.insert(tk.END, "\n")
                i += 1
                continue
            else:
                in_list = False
            
            # Regular paragraph
            if line.strip():
                self._parse_inline_formatting(line)
            self.chat_display.insert(tk.END, "\n")
            i += 1

    def _parse_inline_formatting(self, text: str):
        """Parse and apply inline markdown formatting"""
        # Handle inline code
        while "`" in text:
            start = text.find("`")
            end = text.find("`", start + 1)
            if end == -1:
                break
                
            # Insert text before code
            chat_display.insert(tk.END, text[:start])
            # Insert code with formatting
            chat_display.insert(tk.END, text[start+1:end], "code")
            # Update remaining text
            text = text[end+1:]
        
        # Insert any remaining text
        if text:
            chat_display.insert(tk.END, text)

    def _insert_code_block(self, code: str, language: str, chat_display: tk.Text):
        """Insert a syntax-highlighted code block with action buttons"""
        try:
            # Create frame for code block and buttons
            frame = ttk.Frame(chat_display, style="Custom.TFrame")
            
            # Create text widget for code
            code_text = tk.Text(frame,
                              width=80,
                              height=min(len(code.split('\n')) + 1, 20),
                              font=("SF Mono", 11),
                              bg="#363636",
                              fg="#ffffff",
                              wrap=tk.NONE)
            
            # Add syntax highlighting
            if language:
                try:
                    lexer = get_lexer_by_name(language)
                    formatter = get_formatter_by_name("html")
                    highlighted = pygments.highlight(code, lexer, formatter)
                    code_text.insert("1.0", highlighted)
                except:
                    code_text.insert("1.0", code)
            else:
                code_text.insert("1.0", code)
                
            code_text.configure(state=tk.DISABLED)
            
            # Create button frame
            button_frame = ttk.Frame(frame, style="Custom.TFrame")
            
            # Add copy button
            copy_btn = ttk.Button(button_frame,
                                text="Copy",
                                style="Custom.TButton",
                                command=lambda: self._copy_code(code))
            copy_btn.pack(side=tk.LEFT, padx=2)
            
            # Add run button if code appears to be a command
            if language in ["bash", "shell", "sh"] or code.strip().startswith("$"):
                run_btn = ttk.Button(button_frame,
                                   text="Run",
                                   style="Custom.TButton",
                                   command=lambda: self._run_code(code))
                run_btn.pack(side=tk.LEFT, padx=2)
            
            # Pack everything
            button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
            code_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Insert the frame into the chat display
            self.chat_display.window_create(tk.END, window=frame)
            
        except Exception as e:
            logger.log_exception(e, "Failed to insert code block")
            # Fallback to plain code block
            chat_display.insert(tk.END, code, "code_block")

    def _copy_code(self, code: str):
        """Copy code to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(code)
        self._reset_status()
        self.status_bar.configure(text="Code copied to clipboard")

    def _run_code(self, code: str):
        """Run code in terminal (with confirmation)"""
        if messagebox.askyesno(
            "Run Command",
            "Are you sure you want to run this command?\n\n" + code[:200] +
            ("..." if len(code) > 200 else ""),
            icon="warning"
        ):
            try:
                # Strip command prompt symbol if present
                if code.startswith("$ "):
                    code = code[2:]
                    
                # Run in new terminal
                import subprocess
                subprocess.Popen(['x-terminal-emulator', '-e',
                               f'bash -c "{code}; read -p \'Press Enter to close\'"'])
                
                self._reset_status()
                self.status_bar.configure(text="Command launched in terminal")
                
            except Exception as e:
                logger.log_exception(e, "Failed to run command")
                self._display_error("Failed to run command")

    def _new_conversation(self):
        """Start a new conversation"""
        if messagebox.askyesno("New Conversation", 
                             "Start a new conversation? Current conversation will be saved."):
            # Get current tab
            current_tab = self.tab_manager.get_current_tab()
            if not current_tab:
                return
                
            # Save current conversation
            current_tab.conversation_manager.save_conversation()
            
            # Create new tab
            self.tab_manager.new_tab()

    def _save_conversation(self):
        """Save the current tab's conversation"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            current_tab.conversation_manager.save_conversation()
            self.status_bar.configure(text="Conversation saved")

    def _load_conversation(self):
        """Load a previous conversation in new tab"""
        current_tab = self.tab_manager.get_current_tab()
        if current_tab:
            conversations = current_tab.conversation_manager.list_conversations()
            browser = ConversationBrowser(self, conversations, self._on_conversation_selected)

    def _on_conversation_selected(self, conversation_id: str):
        """Handle conversation selection from browser by creating new tab"""
        # Create new tab
        tab_id = self.tab_manager.new_tab()
        if not tab_id:
            messagebox.showerror("Error", "Failed to create new tab")
            return
            
        tab = self.tab_manager.tabs[tab_id]
        
        # Load conversation in new tab
        if tab.conversation_manager.load_conversation(conversation_id):
            # Display loaded messages
            for msg in tab.conversation_manager.messages:
                self._display_message(
                    "You" if msg["role"] == "user" else "Assistant",
                    msg["content"]
                )
            
            self.status_bar.configure(text=f"Loaded conversation {conversation_id}")
        else:
            # Close tab if load failed
            self.tab_manager.close_tab(tab_id)
            messagebox.showerror(
                "Error",
                f"Failed to load conversation {conversation_id}"
            )

    def _copy_selected_text(self):
        """Copy selected text from current tab to clipboard"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        try:
            selected = current_tab.chat_display.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected)
            self.status_bar.configure(text="Selected text copied to clipboard")
        except tk.TclError:
            # No selection
            pass

    def _copy_all_text(self):
        """Copy entire conversation from current tab to clipboard"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        all_text = current_tab.chat_display.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(all_text)
        self.status_bar.configure(text="Conversation copied to clipboard")

    def _minimize_to_tray(self):
        """Minimize window to system tray"""
        if not hasattr(self, 'tray_manager'):
            self.tray_manager = TrayManager(
                show_window=self._restore_from_tray,
                quit_app=self.quit
            )
        self.withdraw()

    def _restore_from_tray(self):
        """Restore window from system tray"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit(self):
        """Clean up and quit the application"""
        if hasattr(self, 'tray_manager'):
            self.tray_manager.cleanup()
        self.conversation_manager.save_conversation()
        self.destroy()

    def process_screenshot(self, screenshot_data: bytes, description: str = ""):
        """Process and display a new screenshot in current tab"""
        current_tab = self.tab_manager.get_current_tab()
        if not current_tab:
            return
            
        try:
            logger.info("Processing new screenshot")
            
            def on_thumbnail_ready(thumbnail_data: bytes):
                """Callback when thumbnail is created"""
                try:
                    # Create thumbnail image
                    image = Image.open(io.BytesIO(thumbnail_data))
                    photo = ImageTk.PhotoImage(image)
                    
                    # Store reference to prevent garbage collection
                    if not hasattr(current_tab, '_photo_references'):
                        current_tab._photo_references = []
                    current_tab._photo_references.append(photo)
                    
                    # Add thumbnail to chat
                    current_tab.chat_display.configure(state=tk.NORMAL)
                    current_tab.chat_display.image_create(tk.END, image=photo)
                    
                    # Make image clickable
                    tag_name = f"img_{len(current_tab._photo_references)}"
                    current_tab.chat_display.tag_add(tag_name, "end-2c", "end-1c")
                    current_tab.chat_display.tag_bind(
                        tag_name,
                        "<Button-1>",
                        lambda e, img=screenshot_data: self._show_full_image(img)
                    )
                    
                    current_tab.chat_display.insert(tk.END, "\n\n")
                    current_tab.chat_display.configure(state=tk.DISABLED)
                    current_tab.chat_display.see(tk.END)
                    
                except Exception as e:
                    logger.log_exception(e, "Failed to display thumbnail")
                    self._display_error("Failed to display screenshot thumbnail")
            
            # Process screenshot asynchronously
            self.image_processor.process_image_async(
                screenshot_data,
                callback=on_thumbnail_ready,
                optimize=True,
                thumbnail=True
            )
            
            # Add screenshot to conversation
            self.conversation_manager.add_message(
                "system",
                f"[Screenshot received{': ' + description if description else ''}]",
                {"screenshot": {"data": screenshot_data, "description": description}}
            )
            
        except Exception as e:
            logger.log_exception(e, "Failed to process screenshot")
            self._display_error("Failed to process screenshot")

    def _show_full_image(self, image_data: bytes):
        """Display full-size image in a new window"""
        try:
            # Create new window
            window = tk.Toplevel(self)
            window.title("Screenshot Viewer")
            
            def on_image_ready(optimized_data: bytes):
                try:
                    # Display optimized image
                    image = Image.open(io.BytesIO(optimized_data))
                    photo = ImageTk.PhotoImage(image)
                    
                    # Create label with image
                    label = ttk.Label(window, image=photo)
                    label.image = photo  # Keep reference
                    label.pack(padx=10, pady=10)
                    
                    # Add close button
                    ttk.Button(
                        window,
                        text="Close",
                        command=window.destroy
                    ).pack(pady=(0, 10))
                    
                except Exception as e:
                    logger.log_exception(e, "Failed to display full image")
                    self._display_error("Failed to display full-size image")
                    window.destroy()
            
            # Process image asynchronously
            self.image_processor.process_image_async(
                image_data,
                callback=on_image_ready,
                optimize=True,
                thumbnail=False
            )
            
        except Exception as e:
            logger.log_exception(e, "Failed to create image viewer window")
            self._display_error("Failed to open image viewer")

    def _display_error(self, message: str):
        """Display an error message to the user"""
        self.status_bar.configure(
            text=message,
            foreground="#ff0000"
        )
        messagebox.showerror("Error", message)

    def _reset_status(self):
        """Reset the status bar"""
        self.status_bar.configure(
            text="Ready",
            foreground="#ffffff"
        )