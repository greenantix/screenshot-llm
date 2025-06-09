import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from datetime import datetime
import json

class ConversationBrowser(tk.Toplevel):
    def __init__(self, parent, conversation_data: list, on_select: Callable[[str], None]):
        super().__init__(parent)
        
        self.title("Load Conversation")
        self.geometry("600x400")
        self.minsize(400, 300)
        
        # Make the window modal
        self.transient(parent)
        self.grab_set()
        
        # Store callback
        self.on_select = on_select
        
        # Setup styles
        self._setup_styles()
        
        # Create main container
        self.main_container = ttk.Frame(self, style="Custom.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create search bar
        self._setup_search_bar()
        
        # Create conversation list
        self._setup_conversation_list()
        
        # Create preview area
        self._setup_preview_area()
        
        # Create button bar
        self._setup_button_bar()
        
        # Populate conversations
        self._populate_conversations(conversation_data)
        
        # Center window on parent
        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")

    def _setup_styles(self):
        """Configure ttk styles for the browser"""
        style = ttk.Style()
        
        # Use same theme as main window
        style.configure("Browser.Treeview",
                      background="#2d2d2d",
                      foreground="#ffffff",
                      fieldbackground="#2d2d2d")
        
        style.configure("Browser.Treeview.Heading",
                      background="#363636",
                      foreground="#ffffff")

    def _setup_search_bar(self):
        """Create the search bar"""
        search_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_conversations)
        
        search_entry = ttk.Entry(search_frame,
                               textvariable=self.search_var,
                               style="Custom.TEntry")
        search_entry.pack(fill=tk.X)
        search_entry.insert(0, "Search conversations...")
        search_entry.bind("<FocusIn>", 
                         lambda e: search_entry.delete(0, tk.END) 
                         if search_entry.get() == "Search conversations..." 
                         else None)

    def _setup_conversation_list(self):
        """Create the conversation list view"""
        list_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        self.tree = ttk.Treeview(list_frame, 
                                style="Browser.Treeview",
                                columns=("Date", "Messages"),
                                show="headings")
        
        # Configure columns
        self.tree.heading("Date", text="Date")
        self.tree.heading("Messages", text="Messages")
        
        self.tree.column("Date", width=150)
        self.tree.column("Messages", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, 
                                orient=tk.VERTICAL,
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_select_conversation)

    def _setup_preview_area(self):
        """Create the conversation preview area"""
        preview_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create preview text widget
        self.preview = tk.Text(preview_frame,
                             height=5,
                             wrap=tk.WORD,
                             bg="#2d2d2d",
                             fg="#ffffff",
                             font=("SF Pro Display", 11))
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.configure(state=tk.DISABLED)

    def _setup_button_bar(self):
        """Create the button bar"""
        button_frame = ttk.Frame(self.main_container, style="Custom.TFrame")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        load_button = ttk.Button(button_frame,
                               text="Load",
                               style="Custom.TButton",
                               command=self._load_selected)
        cancel_button = ttk.Button(button_frame,
                                 text="Cancel",
                                 style="Custom.TButton",
                                 command=self.destroy)
        
        load_button.pack(side=tk.RIGHT, padx=(5, 0))
        cancel_button.pack(side=tk.RIGHT)

    def _populate_conversations(self, conversations: list):
        """Populate the conversation list"""
        for conv in conversations:
            date = datetime.fromisoformat(conv["timestamp"]).strftime("%Y-%m-%d %H:%M")
            
            self.tree.insert("", "end",
                           iid=conv["id"],
                           values=(date, conv["message_count"]),
                           tags=(conv["id"],))
            
    def _filter_conversations(self, *args):
        """Filter conversations based on search text"""
        search_text = self.search_var.get().lower()
        if search_text == "search conversations...":
            return
            
        for item in self.tree.get_children():
            conversation = self.tree.item(item)
            show = True
            
            if search_text:
                # Check if search text in date or preview
                date = conversation["values"][0].lower()
                if search_text not in date:
                    show = False
                    
            self.tree.detach(item) if not show else self.tree.reattach(item, "", "end")

    def _on_select_conversation(self, event):
        """Handle conversation selection"""
        selection = self.tree.selection()
        if not selection:
            return
            
        conversation_id = selection[0]
        # Update preview
        self.preview.configure(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        
        # TODO: Load and show conversation preview
        self.preview.insert(tk.END, f"Loading preview for conversation {conversation_id}...")
        
        self.preview.configure(state=tk.DISABLED)

    def _load_selected(self):
        """Load the selected conversation"""
        selection = self.tree.selection()
        if selection:
            conversation_id = selection[0]
            self.destroy()
            self.on_select(conversation_id)