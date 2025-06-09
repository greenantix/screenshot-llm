#!/usr/bin/env python3
"""
GTK Conversation Browser - Phase 2 Implementation
Modern conversation browser using GTK TreeView

Replaces the Tkinter conversation browser as part of Phase 2 migration
as outlined in claude.md.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Callable

class GTKConversationBrowser(Gtk.Dialog):
    """
    Modern GTK conversation browser using TreeView.
    Much more powerful and native-looking than the Tkinter version.
    """
    
    def __init__(self, parent: Gtk.Window, conversations: List[Dict], callback: Callable[[str], None]):
        super().__init__(
            title="Browse Conversations",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )
        
        self.conversations = conversations
        self.callback = callback
        self.selected_conversation = None
        
        self.set_default_size(600, 400)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        self._create_ui()
        self._populate_conversations()
        
        # Connect response signal
        self.connect("response", self._on_response)
    
    def _create_ui(self):
        """Create the conversation browser UI"""
        content_area = self.get_content_area()
        content_area.set_spacing(8)
        content_area.set_margin_left(8)
        content_area.set_margin_right(8)
        content_area.set_margin_top(8)
        content_area.set_margin_bottom(8)
        
        # Header label
        header_label = Gtk.Label()
        header_label.set_markup("<b>Select a conversation to open:</b>")
        header_label.set_halign(Gtk.Align.START)
        content_area.pack_start(header_label, False, False, 0)
        
        # Create scrollable area for the tree view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)
        
        # Create tree view and model
        self._create_tree_view()
        scrolled_window.add(self.tree_view)
        
        content_area.pack_start(scrolled_window, True, True, 0)
        
        # Info panel for selected conversation
        self._create_info_panel(content_area)
        
        # Show all widgets
        self.show_all()
    
    def _create_tree_view(self):
        """Create the conversations tree view"""
        # Create list store with columns: ID, Title, Date, Messages, Preview
        self.list_store = Gtk.ListStore(str, str, str, int, str)
        
        # Create tree view
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_rules_hint(True)
        
        # Create columns
        columns = [
            ("Conversation", 0, 150),
            ("Date", 2, 120),
            ("Messages", 3, 80),
            ("Preview", 4, 200)
        ]
        
        for title, column_id, width in columns:
            renderer = Gtk.CellRendererText()
            
            # Make preview column use ellipsis for long text
            if title == "Preview":
                renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            
            # Make messages column centered
            if title == "Messages":
                renderer.set_property("xalign", 0.5)
            
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
            column.set_min_width(width)
            column.set_resizable(True)
            
            # Make date and messages columns sortable
            if title in ["Date", "Messages"]:
                column.set_sort_column_id(column_id)
            
            self.tree_view.append_column(column)
        
        # Connect selection changed signal
        selection = self.tree_view.get_selection()
        selection.connect("changed", self._on_selection_changed)
        
        # Connect double-click signal
        self.tree_view.connect("row-activated", self._on_row_activated)
    
    def _create_info_panel(self, parent):
        """Create info panel for selected conversation details"""
        info_frame = Gtk.Frame(label="Conversation Details")
        info_frame.set_margin_top(8)
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_margin_left(8)
        info_box.set_margin_right(8)
        info_box.set_margin_top(8)
        info_box.set_margin_bottom(8)
        
        # Conversation details labels
        self.id_label = Gtk.Label()
        self.id_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.id_label, False, False, 0)
        
        self.created_label = Gtk.Label()
        self.created_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.created_label, False, False, 0)
        
        self.messages_label = Gtk.Label()
        self.messages_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.messages_label, False, False, 0)
        
        # First message preview
        preview_label = Gtk.Label()
        preview_label.set_markup("<b>First Message:</b>")
        preview_label.set_halign(Gtk.Align.START)
        preview_label.set_margin_top(4)
        info_box.pack_start(preview_label, False, False, 0)
        
        # Scrollable text view for preview
        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scroll.set_size_request(-1, 80)
        
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        self.preview_text.set_cursor_visible(False)
        self.preview_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        preview_scroll.add(self.preview_text)
        info_box.pack_start(preview_scroll, True, True, 0)
        
        info_frame.add(info_box)
        parent.pack_start(info_frame, False, False, 0)
    
    def _populate_conversations(self):
        """Populate the tree view with conversations"""
        self.list_store.clear()
        
        for conv in self.conversations:
            conv_id = conv.get("id", "Unknown")
            
            # Format date
            created = conv.get("created", "")
            if created:
                try:
                    date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = created[:16] if len(created) > 16 else created
            else:
                formatted_date = "Unknown"
            
            # Get message count
            message_count = conv.get("message_count", 0)
            
            # Create preview from first message
            preview = "No messages"
            if conv.get("messages") and len(conv["messages"]) > 0:
                first_msg = conv["messages"][0]
                content = first_msg.get("content", "")
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")  # Single line
            
            # Create a readable title
            title = f"Chat {conv_id.split('_')[-1] if '_' in conv_id else conv_id}"
            
            self.list_store.append([conv_id, title, formatted_date, message_count, preview])
        
        # Sort by date (newest first)
        self.list_store.set_sort_column_id(2, Gtk.SortType.DESCENDING)
    
    def _on_selection_changed(self, selection):
        """Handle selection change in tree view"""
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            conv_id = model[tree_iter][0]
            self.selected_conversation = conv_id
            self._update_info_panel(conv_id)
            
            # Enable OK button
            self.set_response_sensitive(Gtk.ResponseType.OK, True)
        else:
            self.selected_conversation = None
            self._clear_info_panel()
            
            # Disable OK button
            self.set_response_sensitive(Gtk.ResponseType.OK, False)
    
    def _on_row_activated(self, tree_view, path, column):
        """Handle double-click on row"""
        # Double-click acts as OK
        self.response(Gtk.ResponseType.OK)
    
    def _update_info_panel(self, conv_id: str):
        """Update the info panel with conversation details"""
        # Find the conversation data
        conv_data = None
        for conv in self.conversations:
            if conv.get("id") == conv_id:
                conv_data = conv
                break
        
        if not conv_data:
            self._clear_info_panel()
            return
        
        # Update labels
        self.id_label.set_markup(f"<b>ID:</b> {conv_id}")
        
        created = conv_data.get("created", "Unknown")
        if created:
            try:
                date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%B %d, %Y at %H:%M")
            except:
                formatted_date = created
        else:
            formatted_date = "Unknown"
        
        self.created_label.set_markup(f"<b>Created:</b> {formatted_date}")
        
        message_count = conv_data.get("message_count", 0)
        self.messages_label.set_markup(f"<b>Messages:</b> {message_count}")
        
        # Update preview
        preview_text = "No messages available"
        if conv_data.get("messages") and len(conv_data["messages"]) > 0:
            first_msg = conv_data["messages"][0]
            preview_text = first_msg.get("content", "No content")
        
        buffer = self.preview_text.get_buffer()
        buffer.set_text(preview_text)
    
    def _clear_info_panel(self):
        """Clear the info panel"""
        self.id_label.set_text("")
        self.created_label.set_text("")
        self.messages_label.set_text("")
        
        buffer = self.preview_text.get_buffer()
        buffer.set_text("")
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response"""
        if response_id == Gtk.ResponseType.OK and self.selected_conversation:
            # Call the callback with selected conversation ID
            self.callback(self.selected_conversation)
        
        self.destroy()

def show_conversation_browser(parent: Gtk.Window, conversations: List[Dict], callback: Callable[[str], None]):
    """
    Show the conversation browser dialog.
    
    Args:
        parent: Parent window
        conversations: List of conversation data
        callback: Function to call with selected conversation ID
    """
    if not conversations:
        # Show no conversations dialog
        dialog = Gtk.MessageDialog(
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="No saved conversations found."
        )
        dialog.run()
        dialog.destroy()
        return
    
    # Show conversation browser
    browser = GTKConversationBrowser(parent, conversations, callback)

# Example usage for testing
if __name__ == "__main__":
    # Mock conversation data for testing
    mock_conversations = [
        {
            "id": "conversation_2025-01-01_10-00-00",
            "created": "2025-01-01T10:00:00",
            "message_count": 5,
            "messages": [
                {"content": "This is the first message in the conversation. It contains some sample text to test the preview functionality."}
            ]
        },
        {
            "id": "conversation_2025-01-02_14-30-00", 
            "created": "2025-01-02T14:30:00",
            "message_count": 3,
            "messages": [
                {"content": "Another conversation with different content for testing purposes."}
            ]
        }
    ]
    
    def test_callback(conv_id):
        print(f"Selected conversation: {conv_id}")
        Gtk.main_quit()
    
    # Create test window
    window = Gtk.Window()
    window.set_title("Test")
    window.set_default_size(400, 200)
    window.connect("destroy", Gtk.main_quit)
    
    button = Gtk.Button(label="Open Conversation Browser")
    button.connect("clicked", lambda w: show_conversation_browser(window, mock_conversations, test_callback))
    window.add(button)
    
    window.show_all()
    Gtk.main()