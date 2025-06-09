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
        
        # Create new conversation on startup
        self.conversation_manager.create_new_conversation()
        
    def create_window(self):
        """Create the main chat window"""
        self.root = tk.Tk()
        self.root.title("Screenshot LLM Assistant - Interactive Chat")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)
        
        # Configure style
        self._setup_styles()
        
        # Create menu bar
        self._create_menu()
        
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
        """Setup GUI styling"""
        style = ttk.Style()
        
        # Configure colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#0078d4"
        self.user_color = "#dcf8c6"
        self.assistant_color = "#f1f1f1"
        self.screenshot_color = "#e3f2fd"
        
        # Configure ttk styles
        style.theme_use('clam')
        style.configure('Chat.TFrame', background=self.bg_color)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Conversation", command=self._new_conversation)
        file_menu.add_command(label="Load Conversation", command=self._load_conversation)
        file_menu.add_command(label="Save Conversation", command=self._save_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Export as Text", command=self._export_conversation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._quit_application)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy All", command=self._copy_all_text)
        edit_menu.add_command(label="Clear Conversation", command=self._clear_conversation)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Minimize to Tray", command=self._minimize_to_tray)
        view_menu.add_command(label="Always on Top", command=self._toggle_always_on_top)
    
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
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='#ffffff'
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
            font=('Consolas', 10),
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self._send_message
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready - Waiting for screenshots or user input",
            font=('Consolas', 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Conversation info label
        self.conv_info_label = ttk.Label(
            status_frame,
            text="",
            font=('Consolas', 9)
        )
        self.conv_info_label.pack(side=tk.RIGHT)
        
        self._update_conversation_info()
    
    def _configure_text_tags(self):
        """Configure text tags for message formatting"""
        self.chat_display.tag_configure('timestamp', foreground='#888888', font=('Consolas', 8))
        self.chat_display.tag_configure('user_label', foreground='#4CAF50', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('assistant_label', foreground='#2196F3', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('screenshot_label', foreground='#FF9800', font=('Consolas', 10, 'bold'))
        self.chat_display.tag_configure('user_message', foreground='#ffffff', background='#2E7D32')
        self.chat_display.tag_configure('assistant_message', foreground='#000000', background='#E3F2FD')
        self.chat_display.tag_configure('screenshot_message', foreground='#000000', background='#FFF3E0')
        self.chat_display.tag_configure('code', foreground='#ffffff', background='#424242', font=('Consolas', 9))
        self.chat_display.tag_configure('error', foreground='#f44336')
    
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
        image_path = data.get('image_path')
        context = data.get('context', {})
        
        if image_path:
            # Add screenshot to conversation
            message = self.conversation_manager.add_screenshot_message(image_path, context)
            
            # Update GUI in main thread
            self.root.after(0, lambda: self._display_screenshot_message(message))
            
            # Send to LLM and get response
            asyncio.create_task(self._process_screenshot_with_llm(image_path, context))
    
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
        """Process screenshot with LLM and display response"""
        try:
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Processing screenshot with LLM..."))
            
            # Get conversation messages for API
            api_messages = self.conversation_manager.get_messages_for_api()
            
            # Send to LLM (modify last message to include actual image)
            if api_messages:
                last_message = api_messages[-1]
                if 'content' in last_message and isinstance(last_message['content'], list):
                    for content_item in last_message['content']:
                        if content_item.get('type') == 'image_path':
                            # Replace with actual image for API
                            content_item['type'] = 'image'
                            content_item['source'] = {
                                'type': 'base64',
                                'media_type': self.llm_client._get_image_mime_type(image_path),
                                'data': self.llm_client._encode_image(image_path)
                            }
                            del content_item['image_path']
            
            # Get response from LLM
            response_text = await self._get_llm_response_from_conversation()
            
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
    
    def _display_assistant_message(self, message: Dict[str, Any]):
        """Display assistant message in chat"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Timestamp
        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Assistant label
        self.chat_display.insert(tk.END, "🤖 Assistant: ", 'assistant_label')
        self.chat_display.insert(tk.END, f"{message['content']}\n\n", 'assistant_message')
        
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
        
        # Get LLM response
        asyncio.create_task(self._get_user_message_response())
    
    async def _get_user_message_response(self):
        """Get LLM response to user message"""
        try:
            self.status_label.config(text="Getting response...")
            
            # For now, just echo back (TODO: implement proper conversation)
            response_text = "I received your message. Full conversation context will be implemented in the next phase."
            
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