import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Callable
from .conversation_manager import ConversationManager
from .logger import get_logger

from .logger import get_logger, log_exception

logger = get_logger()

class ConversationTab(ttk.Frame):
    """Represents a single conversation tab"""
    
    def __init__(self, parent, conversation_manager: ConversationManager, window):
        super().__init__(parent)
        
        self.conversation_manager = conversation_manager
        self.window = window  # Reference to main window for shared functionality
        
        # Create text widget with scrollbar
        self.create_text_widget()
        
        # Create input area
        self.create_input_area()
        
        # Store photo references
        self._photo_references = []
        
        # Setup markdown tags
        self.window._setup_markdown_tags(self.chat_display)

    def create_text_widget(self):
        """Create the main text display area"""
        try:
            # Create chat display frame
            self.chat_frame = ttk.Frame(self, style="Custom.TFrame")
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create text widget with scrollbar
            self.chat_display = tk.Text(
                self.chat_frame,
                wrap=tk.WORD,
                bg="#2d2d2d",
                fg="#ffffff",
                font=("SF Pro Display", 11),
                padx=10,
                pady=10,
                insertbackground="#ffffff",  # Cursor color
                state=tk.DISABLED  # Start in disabled state
            )
            
            # Add scrollbar
            self.scrollbar = ttk.Scrollbar(
                self.chat_frame,
                orient=tk.VERTICAL,
                command=self.chat_display.yview
            )
            self.chat_display.configure(yscrollcommand=self.scrollbar.set)
            
            # Pack widgets
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.log_exception(e, "Failed to create text widget")
            raise

    def create_input_area(self):
        """Create the input area for messages"""
        try:
            # Create input frame
            self.input_frame = ttk.Frame(self, style="Custom.TFrame")
            self.input_frame.pack(fill=tk.X, pady=(10, 0))
            
            # Create input field
            self.input_field = tk.Text(
                self.input_frame,
                height=3,
                bg="#2d2d2d",
                fg="#ffffff",
                font=("SF Pro Display", 11),
                padx=5,
                pady=5,
                insertbackground="#ffffff",  # Cursor color
                undo=True  # Enable undo/redo
            )
            self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Create send button
            self.send_button = ttk.Button(
                self.input_frame,
                text="Send",
                style="Custom.TButton",
                command=lambda: self.window._send_message()
            )
            self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
            
            # Bind Enter key to send (Shift+Enter for newline)
            self.input_field.bind("<Return>", lambda e: self.window._send_message() if not e.state & 0x1 else None)
            
        except Exception as e:
            logger.log_exception(e, "Failed to create input area")
            raise

    def get_input_text(self) -> str:
        """Get text from input field"""
        try:
            return self.input_field.get("1.0", tk.END).strip()
        except Exception as e:
            logger.log_exception(e, "Failed to get input text")
            return ""

    def clear_input(self):
        """Clear the input field"""
        try:
            self.input_field.delete("1.0", tk.END)
        except Exception as e:
            logger.log_exception(e, "Failed to clear input")

    def display_message(self, message: str, tags: tuple = ()):
        """Display a message in the chat display"""
        try:
            self.chat_display.configure(state=tk.NORMAL)
            self.chat_display.insert(tk.END, message, tags)
            self.chat_display.configure(state=tk.DISABLED)
            self.chat_display.see(tk.END)
        except Exception as e:
            logger.log_exception(e, "Failed to display message")

class TabManager(ttk.Notebook):
    """Manages multiple conversation tabs"""
    
    def __init__(self, parent, config: dict):
        super().__init__(parent, style="Custom.TNotebook")
        
        self.config = config
        self.tabs: Dict[str, ConversationTab] = {}
        self._tab_counter = 0
        self.window = self.winfo_toplevel()  # Get reference to main window
        
        # Bind tab events
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # Create initial tab
        self.new_tab()

    def new_tab(self) -> str:
        """Create a new conversation tab"""
        try:
            # Create unique tab ID
            tab_id = f"tab_{self._tab_counter}"
            self._tab_counter += 1
            
            # Create conversation manager for this tab
            conversation_manager = ConversationManager()
            
            # Create and set up tab
            tab = ConversationTab(self, conversation_manager, self.window)
            self.tabs[tab_id] = tab
            
            # Add to notebook with default name and close button
            self.add(tab, text=f"Chat {len(self.tabs)}")
            
            # Set up tab styles and markdown tags
            if hasattr(self.window, '_setup_markdown_tags'):
                self.window._setup_markdown_tags(tab.chat_display)
            
            # Switch to new tab
            self.select(tab)
            
            logger.info(f"Created new tab: {tab_id}")
            return tab_id
            
        except Exception as e:
            log_exception(e, "Failed to create new tab")
            raise

    def close_tab(self, tab_id: str):
        """Close a conversation tab"""
        try:
            if tab_id in self.tabs:
                # Save conversation
                self.tabs[tab_id].conversation_manager.save_conversation()
                
                # Remove tab
                tab_index = self.index(self.tabs[tab_id])
                self.forget(tab_index)
                
                # Remove from dictionary
                del self.tabs[tab_id]
                
                logger.info(f"Closed tab: {tab_id}")
                
                # Create new tab if last one closed
                if not self.tabs:
                    self.new_tab()
                    
        except Exception as e:
            log_exception(e, "Failed to close tab")
            raise

    def get_current_tab(self) -> Optional[ConversationTab]:
        """Get the currently selected tab"""
        try:
            current = self.select()
            for tab_id, tab in self.tabs.items():
                if str(tab) == str(current):
                    return tab
            return None
        except Exception as e:
            log_exception(e, "Failed to get current tab")
            return None

    def _on_tab_changed(self, event):
        """Handle tab change events"""
        try:
            current_tab = self.get_current_tab()
            if current_tab:
                # Give focus to input field
                current_tab.input_field.focus_set()
        except Exception as e:
            log_exception(e, "Error handling tab change")

    def cleanup(self):
        """Clean up all tabs"""
        for tab_id in list(self.tabs.keys()):
            try:
                self.close_tab(tab_id)
            except:
                pass