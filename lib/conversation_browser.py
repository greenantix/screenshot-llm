#!/usr/bin/env python3
"""
Conversation browser dialog for Screenshot LLM Assistant
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable
from .logger import get_logger

logger = get_logger(__name__)

class ConversationBrowser:
    """Dialog for browsing and selecting saved conversations"""
    
    def __init__(self, parent: tk.Tk, conversations: List[Dict], callback: Callable[[str], None]):
        self.parent = parent
        self.conversations = conversations
        self.callback = callback
        self.dialog = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create the conversation browser dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Load Conversation")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Create main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="Select a conversation to load:",
                               font=("SF Pro Display", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for conversations
        columns = ("Date", "Messages", "Preview")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.tree.heading("Date", text="Date")
        self.tree.heading("Messages", text="Messages")
        self.tree.heading("Preview", text="Preview")
        
        self.tree.column("Date", width=150)
        self.tree.column("Messages", width=80)
        self.tree.column("Preview", width=350)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate conversations
        self._populate_conversations()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, 
                  text="Cancel", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(button_frame, 
                  text="Load", 
                  command=self._load_selected).pack(side=tk.RIGHT)
        
        # Bind double-click
        self.tree.bind("<Double-1>", lambda e: self._load_selected())
        
        # Focus on dialog
        self.dialog.focus_set()
    
    def _populate_conversations(self):
        """Populate the conversation list"""
        for conv in self.conversations:
            # Format timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(conv["timestamp"])
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = conv["timestamp"][:16]  # Fallback
            
            # Insert into tree
            self.tree.insert("", tk.END, 
                           values=(
                               date_str,
                               conv["message_count"],
                               conv["first_message"]
                           ),
                           tags=(conv["id"],))
    
    def _load_selected(self):
        """Load the selected conversation"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get conversation ID from tags
        item = selection[0]
        tags = self.tree.item(item, "tags")
        if tags:
            conversation_id = tags[0]
            self.callback(conversation_id)
            self._cancel()
    
    def _cancel(self):
        """Cancel and close dialog"""
        self.dialog.destroy()

if __name__ == "__main__":
    # Test the conversation browser
    root = tk.Tk()
    root.withdraw()
    
    test_conversations = [
        {
            "id": "20240101_120000",
            "timestamp": "2024-01-01T12:00:00",
            "message_count": 5,
            "first_message": "Screenshot analysis request for terminal window"
        },
        {
            "id": "20240102_130000", 
            "timestamp": "2024-01-02T13:00:00",
            "message_count": 3,
            "first_message": "Help with Python error in VS Code"
        }
    ]
    
    def test_callback(conv_id: str):
        print(f"Selected conversation: {conv_id}")
        root.quit()
    
    browser = ConversationBrowser(root, test_conversations, test_callback)
    root.mainloop()