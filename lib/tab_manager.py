#!/usr/bin/env python3
"""
Tab manager for Screenshot LLM Assistant
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
from .conversation import ConversationManager
from .logger import get_logger, log_exception

logger = get_logger(__name__)

class ChatTab:
    """Represents a single chat tab"""
    
    def __init__(self, parent: ttk.Notebook, tab_id: str, config: Dict = None):
        self.tab_id = tab_id
        self.parent = parent
        self.config = config
        
        # Create main frame
        self.frame = ttk.Frame(parent, style="Custom.TFrame")
        
        # Initialize conversation manager with config
        self.conversation_manager = ConversationManager(config=config)
        
        # Create UI components
        self._create_ui()
        
        # Add to notebook
        parent.add(self.frame, text=f"Chat {tab_id}")
    
    def _create_ui(self):
        """Create the tab's UI components"""
        # Chat display area
        chat_frame = ttk.Frame(self.frame, style="Custom.TFrame")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget with scrollbar
        self.chat_display = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("SF Pro Display", 11),
            insertbackground="#48b9c7",
            selectbackground="#48b9c7",
            selectforeground="#ffffff"
        )
        
        scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=scrollbar.set)
        
        # Pack chat display and scrollbar
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input area
        input_frame = ttk.Frame(self.frame, style="Custom.TFrame")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Input text widget
        self.input_text = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            bg="#3c3c3c",
            fg="#ffffff",
            font=("SF Pro Display", 11),
            insertbackground="#48b9c7"
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            style="Custom.TButton",
            command=self._on_send
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Bind Enter key to send (Ctrl+Enter for new line)
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Control-Return>", self._on_ctrl_enter)
        
        # Initialize markdown tags
        self._setup_markdown_tags()
    
    def _setup_markdown_tags(self):
        """Configure markdown formatting tags for the chat display"""
        tag_configs = {
            "bold": {"font": ("SF Pro Display", 11, "bold")},
            "italic": {"font": ("SF Pro Display", 11, "italic")},
            "code": {
                "font": ("SF Mono", 10),
                "background": "#363636",
                "foreground": "#48b9c7"
            },
            "code_block": {
                "font": ("SF Mono", 10),
                "background": "#363636",
                "spacing1": 10,
                "spacing3": 10,
                "lmargin1": 10,
                "lmargin2": 10
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
            },
            "header1": {
                "font": ("SF Pro Display", 16, "bold"),
                "spacing1": 10,
                "spacing3": 5
            },
            "header2": {
                "font": ("SF Pro Display", 14, "bold"),
                "spacing1": 8,
                "spacing3": 4
            },
            "header3": {
                "font": ("SF Pro Display", 12, "bold"),
                "spacing1": 6,
                "spacing3": 3
            }
        }
        
        for tag, config in tag_configs.items():
            self.chat_display.tag_configure(tag, **config)
    
    def _on_enter_key(self, event):
        """Handle Enter key press"""
        # Check if Shift is held for new line
        if event.state & 0x1:  # Shift key
            return  # Allow default behavior (new line)
        else:
            self._on_send()
            return "break"  # Prevent default behavior
    
    def _on_ctrl_enter(self, event):
        """Handle Ctrl+Enter for new line"""
        self.input_text.insert(tk.INSERT, "\n")
        return "break"
    
    def _on_send(self):
        """Handle send button click"""
        message = self.get_input_text().strip()
        if message:
            self.clear_input()
            # Find the chat window and call its message handler
            widget = self.parent
            while widget:
                if hasattr(widget, '_send_message_from_tab'):
                    widget._send_message_from_tab(self, message)
                    return
                widget = widget.master if hasattr(widget, 'master') else None
            
            # Fallback: just add the message locally
            self.add_message("You", message, "user")
    
    def get_input_text(self) -> str:
        """Get text from input field"""
        return self.input_text.get("1.0", tk.END).strip()
    
    def clear_input(self):
        """Clear the input field"""
        self.input_text.delete("1.0", tk.END)
    
    def add_message(self, sender: str, content: str, role: str = "user"):
        """Add a message to the chat display"""
        try:
            # Enable editing
            self.chat_display.configure(state=tk.NORMAL)
            
            # Add timestamp and sender
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M")
            
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.chat_display.insert(tk.END, f"{sender}: ", "bold")
            
            # Add content - simplified for now
            self.chat_display.insert(tk.END, content)
            self.chat_display.insert(tk.END, "\n\n")
            
            # Add to conversation
            if role == "user":
                self.conversation_manager.add_user_message(content)
            elif role == "assistant":
                self.conversation_manager.add_assistant_message(content)
            
            # Disable editing and scroll to bottom
            self.chat_display.configure(state=tk.DISABLED)
            self.chat_display.see(tk.END)
            
        except Exception as e:
            log_exception(e, "Failed to add message to chat")
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.configure(state=tk.DISABLED)

class TabManager(ttk.Notebook):
    """Manages multiple chat tabs"""
    
    def __init__(self, parent, config: Dict):
        super().__init__(parent, style="Custom.TNotebook")
        
        self.config = config
        self.tabs: Dict[str, ChatTab] = {}
        self.tab_counter = 0
        
        # Create first tab
        self.new_tab()
    
    def new_tab(self) -> str:
        """Create a new chat tab"""
        try:
            self.tab_counter += 1
            tab_id = str(self.tab_counter)
            
            # Create new tab with config
            tab = ChatTab(self, tab_id, self.config)
            self.tabs[tab_id] = tab
            
            # Select the new tab
            self.select(tab.frame)
            
            logger.info(f"Created new tab: {tab_id}")
            return tab_id
            
        except Exception as e:
            log_exception(e, "Failed to create new tab")
            return ""
    
    def close_tab(self, tab_id: str):
        """Close a specific tab"""
        if tab_id not in self.tabs:
            return
        
        try:
            tab = self.tabs[tab_id]
            
            # Save conversation before closing
            tab.conversation_manager.save_conversation()
            
            # Remove from notebook
            self.forget(tab.frame)
            
            # Remove from our tracking
            del self.tabs[tab_id]
            
            # If no tabs left, create a new one
            if not self.tabs:
                self.new_tab()
            
            logger.info(f"Closed tab: {tab_id}")
            
        except Exception as e:
            log_exception(e, f"Failed to close tab {tab_id}")
    
    def get_current_tab(self) -> Optional[ChatTab]:
        """Get the currently selected tab"""
        try:
            current_widget = self.nametowidget(self.select())
            
            # Find the tab that owns this widget
            for tab in self.tabs.values():
                if tab.frame == current_widget:
                    return tab
            
            return None
            
        except Exception as e:
            log_exception(e, "Failed to get current tab")
            return None
    
    def get_tab_count(self) -> int:
        """Get the number of open tabs"""
        return len(self.tabs)

if __name__ == "__main__":
    # Test the tab manager
    root = tk.Tk()
    root.geometry("800x600")
    
    tab_manager = TabManager(root, {})
    tab_manager.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()