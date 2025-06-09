#!/usr/bin/env python3
"""
Quick Answer Pop-up Window - GTK Implementation
Phase 1 of the Tkinter to GTK migration as outlined in claude.md

This module creates a borderless, always-on-top GTK window that appears
at the cursor location to show immediate LLM responses.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
import sys
import os
import argparse
import json
from typing import Optional
import subprocess
import re

class QuickAnswerWindow(Gtk.Window):
    """
    A modern GTK pop-up window for displaying quick LLM responses.
    
    Features:
    - Borderless, always-on-top design
    - Positioned at cursor location
    - Modern styling with CSS
    - Markdown text rendering
    - Copy code functionality
    - Integration with main chat window
    """
    
    def __init__(self, response_text: str, x: int, y: int, config_dir: str = "~/.local/share/screenshot-llm"):
        super().__init__()
        
        self.response_text = response_text
        self.cursor_x = x
        self.cursor_y = y
        self.config_dir = os.path.expanduser(config_dir)
        
        # Configure window properties
        self._setup_window()
        
        # Load CSS styling
        self._load_styles()
        
        # Create UI
        self._create_ui()
        
        # Position window at cursor
        self._position_window()
        
        # Show window
        self.show_all()
        
        # Auto-focus and grab input
        self.present()
        self.grab_focus()
    
    def _setup_window(self):
        """Configure window properties for a modern pop-up experience"""
        # Remove window decorations (borderless)
        self.set_decorated(False)
        
        # Always stay on top
        self.set_keep_above(True)
        
        # Don't show in taskbar
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        
        # Set window type hint for a popup
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        
        # Set window size constraints
        self.set_default_size(400, 300)
        self.set_size_request(300, 150)  # Minimum size
        
        # Make window resizable but with sensible limits
        self.set_resizable(True)
        
        # Connect escape key and focus loss to close
        self.connect("key-press-event", self._on_key_press)
        self.connect("focus-out-event", self._on_focus_out)
        self.connect("delete-event", Gtk.main_quit)
    
    def _load_styles(self):
        """Load modern CSS styling for the pop-up window"""
        css = """
        /* Pop!_OS Dark Theme Compatible Quick Answer Window */
        .quick-answer-window {
            background-color: #2e2e2e;
            border: 1px solid #484848;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
        }
        
        .quick-answer-header {
            background: #3d3d3d;
            color: #ffffff;
            padding: 12px 16px;
            border-radius: 12px 12px 0 0;
            font-weight: 600;
            font-size: 12px;
            border-bottom: 1px solid #484848;
        }
        
        .quick-answer-content {
            background-color: #2e2e2e;
            color: #ffffff;
            padding: 16px;
            font-family: "Fira Sans", "Ubuntu", sans-serif;
            font-size: 12px;
        }
        
        .quick-answer-button {
            background: #faa41a;
            color: #2e2e2e;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            margin: 4px;
            font-weight: 600;
            font-size: 11px;
            min-height: 32px;
        }
        
        .quick-answer-button:hover {
            background: #ffb347;
            box-shadow: 0 4px 8px rgba(250, 164, 26, 0.3);
        }
        
        .quick-answer-code {
            background-color: #1e1e1e;
            color: #f8f8f2;
            font-family: "Fira Code", "Ubuntu Mono", monospace;
            font-size: 11px;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #484848;
            margin: 8px 0;
        }
        
        .quick-answer-close {
            background-color: #484848;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 11px;
            min-height: 32px;
        }
        
        .quick-answer-close:hover {
            background-color: #5a5a5a;
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
        """Create the modern UI components"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class("quick-answer-window")
        self.add(main_box)
        
        # Header with title and close button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header_box.get_style_context().add_class("quick-answer-header")
        
        title_label = Gtk.Label("Quick Answer")
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, True, True, 0)
        
        close_button = Gtk.Button("✕")
        close_button.get_style_context().add_class("quick-answer-close")
        close_button.connect("clicked", lambda w: Gtk.main_quit())
        header_box.pack_end(close_button, False, False, 0)
        
        main_box.pack_start(header_box, False, False, 0)
        
        # Scrollable content area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # Content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content_box.get_style_context().add_class("quick-answer-content")
        content_box.set_margin_left(12)
        content_box.set_margin_right(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        
        # Parse and display the response
        self._parse_and_display_response(content_box)
        
        scrolled.add(content_box)
        main_box.pack_start(scrolled, True, True, 0)
        
        # Action buttons
        self._create_action_buttons(main_box)
    
    def _parse_and_display_response(self, container: Gtk.Box):
        """Parse response and create TL;DR format with actionable commands"""
        # Extract summary and commands
        summary = self._extract_summary()
        commands = self._extract_commands()
        
        # Add TL;DR summary
        if summary:
            summary_label = Gtk.Label()
            summary_label.set_markup(f"<b>TL;DR:</b> {summary}")
            summary_label.set_line_wrap(True)
            summary_label.set_line_wrap_mode(Pango.WrapMode.WORD)
            summary_label.set_halign(Gtk.Align.START)
            summary_label.set_selectable(True)
            container.pack_start(summary_label, False, False, 8)
        
        # Add commands section if any found
        if commands:
            commands_label = Gtk.Label()
            commands_label.set_markup("<b>Commands to run:</b>")
            commands_label.set_halign(Gtk.Align.START)
            container.pack_start(commands_label, False, False, 4)
            
            for i, cmd in enumerate(commands[:3]):  # Show max 3 commands
                self._add_command_widget(container, cmd, i)
    
    def _extract_summary(self) -> str:
        """Extract a concise summary from the response"""
        lines = self.response_text.split('\n')
        
        # Look for explicit summary patterns
        for line in lines:
            line = line.strip()
            if line.lower().startswith(('summary:', 'tl;dr:', 'in short:', 'quick answer:')):
                return line.split(':', 1)[1].strip()
        
        # Extract first meaningful sentence
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('#', '```', '-', '*')) and len(line) > 20:
                # Take first sentence or first 100 chars
                if '.' in line:
                    return line.split('.')[0] + '.'
                elif len(line) > 100:
                    return line[:97] + '...'
                else:
                    return line
        
        return "Quick response available - see full details in chat window"
    
    def _extract_commands(self) -> list:
        """Extract executable commands from the response"""
        commands = []
        lines = self.response_text.split('\n')
        in_code_block = False
        current_language = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('```'):
                if in_code_block:
                    in_code_block = False
                    current_language = ""
                else:
                    in_code_block = True
                    current_language = line[3:].strip()
                continue
            
            if in_code_block:
                # Skip empty lines and comments
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Check if it looks like a command
                    if (current_language in ['bash', 'sh', 'shell', ''] and 
                        (line.startswith(('sudo', 'apt', 'pip', 'npm', 'git', 'cd', 'mkdir', 'cp', 'mv', 'chmod')) or
                         ' install ' in line or ' run ' in line or ' start ' in line)):
                        commands.append(line)
                    elif current_language == 'python' and ('import' in line or line.startswith('python')):
                        commands.append(line)
        
        return commands[:5]  # Return max 5 commands
    
    def _add_command_widget(self, container: Gtk.Box, command: str, index: int):
        """Add a command widget with copy button"""
        cmd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cmd_box.set_margin_top(4)
        cmd_box.set_margin_bottom(4)
        
        # Command text
        cmd_label = Gtk.Label()
        cmd_label.set_markup(f"<tt>{command}</tt>")
        cmd_label.set_halign(Gtk.Align.START)
        cmd_label.set_selectable(True)
        cmd_label.get_style_context().add_class("quick-answer-code")
        cmd_box.pack_start(cmd_label, True, True, 0)
        
        # Copy button
        copy_btn = Gtk.Button("📋")
        copy_btn.set_tooltip_text("Copy command")
        copy_btn.get_style_context().add_class("quick-answer-button")
        copy_btn.connect("clicked", lambda w: self._copy_to_clipboard(command))
        cmd_box.pack_end(copy_btn, False, False, 0)
        
        container.pack_start(cmd_box, False, False, 0)
    
    def _add_text_widget(self, container: Gtk.Box, text: str):
        """Add a text widget with proper formatting"""
        label = Gtk.Label(text.strip())
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD)
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.START)
        label.set_selectable(True)
        container.pack_start(label, False, False, 0)
    
    def _add_header_widget(self, container: Gtk.Box, text: str, level: int):
        """Add a header widget"""
        label = Gtk.Label(text)
        label.set_line_wrap(True)
        label.set_halign(Gtk.Align.START)
        
        # Style based on header level
        if level == 1:
            label.set_markup(f"<b><big>{text}</big></b>")
        else:
            label.set_markup(f"<b>{text}</b>")
        
        container.pack_start(label, False, False, 4)
    
    def _add_code_widget(self, container: Gtk.Box, code: str, language: str):
        """Add a code block widget with copy functionality"""
        code_frame = Gtk.Frame()
        code_frame.get_style_context().add_class("quick-answer-code")
        
        code_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Code header with language and copy button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        lang_label = Gtk.Label(language.title() if language != "text" else "Code")
        lang_label.set_halign(Gtk.Align.START)
        lang_label.set_markup(f"<small><b>{language.title() if language != 'text' else 'Code'}</b></small>")
        header_box.pack_start(lang_label, True, True, 0)
        
        copy_button = Gtk.Button("📋 Copy")
        copy_button.get_style_context().add_class("quick-answer-button")
        copy_button.connect("clicked", lambda w: self._copy_to_clipboard(code))
        header_box.pack_end(copy_button, False, False, 0)
        
        code_box.pack_start(header_box, False, False, 0)
        
        # Code text
        code_label = Gtk.Label(code)
        code_label.set_line_wrap(True)
        code_label.set_halign(Gtk.Align.START)
        code_label.set_selectable(True)
        code_label.set_markup(f"<tt>{code}</tt>")
        code_box.pack_start(code_label, False, False, 0)
        
        code_frame.add(code_box)
        container.pack_start(code_frame, False, False, 4)
    
    def _create_action_buttons(self, container: Gtk.Box):
        """Create action buttons at the bottom"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_margin_left(12)
        button_box.set_margin_right(12)
        button_box.set_margin_bottom(12)
        
        # "Open in Chat" button
        chat_button = Gtk.Button("💬 Open in Chat")
        chat_button.get_style_context().add_class("quick-answer-button")
        chat_button.connect("clicked", self._on_open_in_chat)
        button_box.pack_start(chat_button, True, True, 0)
        
        # "Close" button
        close_button = Gtk.Button("Close")
        close_button.get_style_context().add_class("quick-answer-close")
        close_button.connect("clicked", lambda w: Gtk.main_quit())
        button_box.pack_end(close_button, False, False, 0)
        
        container.pack_end(button_box, False, False, 0)
    
    def _on_open_in_chat(self, button):
        """Send full response to GTK chat window and close pop-up"""
        try:
            # Import IPC client for communication with GTK window
            import sys
            import os
            
            # Add lib path for imports
            lib_path = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, lib_path)
            
            from ipc_handler import IPCManager
            
            # Create IPC client to send message to GTK window
            ipc_manager = IPCManager(self.config_dir)
            client = ipc_manager.create_client()
            
            # Send full response to chat window
            message = {
                "command": "add_message", 
                "data": {
                    "sender": "Assistant",
                    "content": self.response_text,
                    "role": "assistant"
                }
            }
            
            import asyncio
            
            async def send_message():
                try:
                    await client.send_message(message["command"], message["data"])
                    await client.close()
                except Exception as e:
                    print(f"Failed to send message to chat: {e}")
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_message())
            loop.close()
            
            # Close the pop-up
            Gtk.main_quit()
            
        except Exception as e:
            print(f"Failed to open in chat: {e}")
            # Fallback: just close the pop-up
            Gtk.main_quit()
    
    def _position_window(self):
        """Position the window near the cursor but keep it on screen"""
        # Get screen dimensions
        screen = self.get_screen()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Get window size
        window_width, window_height = self.get_size()
        
        # Calculate position with offset to avoid covering cursor
        offset_x, offset_y = 20, 20
        x = min(self.cursor_x + offset_x, screen_width - window_width - 20)
        y = min(self.cursor_y + offset_y, screen_height - window_height - 20)
        
        # Ensure window stays on screen
        x = max(x, 20)
        y = max(y, 20)
        
        self.move(x, y)
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            
            # Show brief feedback
            # Could add a toast notification here
            print(f"Copied to clipboard: {text[:50]}...")
            
        except Exception as e:
            print(f"Failed to copy to clipboard: {e}")
    
    def _on_open_in_chat(self, button):
        """Open this response in the main chat window"""
        try:
            # Use IPC to send to main chat window
            # This would integrate with the existing IPC system
            print("TODO: Integrate with main chat window via IPC")
            # For now, just print the action
            print("Opening in main chat window...")
            
        except Exception as e:
            print(f"Failed to open in chat: {e}")
        
        # Close this popup
        Gtk.main_quit()
    
    def _on_key_press(self, widget, event):
        """Handle key press events"""
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False
    
    def _on_focus_out(self, widget, event):
        """Handle focus loss - could close window or just ignore"""
        # For now, don't auto-close on focus loss to allow interaction
        # Uncomment the next line if you want it to close on focus loss
        # Gtk.main_quit()
        return False

def main():
    """Main entry point for the quick answer window"""
    parser = argparse.ArgumentParser(description="Quick Answer Pop-up Window")
    parser.add_argument("response", help="LLM response text to display")
    parser.add_argument("--x", type=int, default=100, help="X coordinate for window position")
    parser.add_argument("--y", type=int, default=100, help="Y coordinate for window position")
    parser.add_argument("--config-dir", default="~/.local/share/screenshot-llm", 
                       help="Configuration directory")
    
    args = parser.parse_args()
    
    # Create and show the window
    window = QuickAnswerWindow(args.response, args.x, args.y, args.config_dir)
    
    # Run the GTK main loop
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()