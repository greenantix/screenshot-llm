#!/usr/bin/env python3
import os
import re
import subprocess
import threading
import logging
from typing import List, Optional
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Pango
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import TerminalFormatter

logger = logging.getLogger(__name__)

class CommandInterface:
    def __init__(self):
        self.app = None
        self.window = None
        self.text_view = None
        self.commands = []
        
    def extract_commands(self, llm_response: str) -> List[dict]:
        """Extract commands from LLM response"""
        commands = []
        
        # Find code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(code_block_pattern, llm_response, re.DOTALL)
        
        for lang, code in matches:
            if not lang:
                lang = self._guess_language(code)
            
            commands.append({
                'language': lang,
                'code': code.strip(),
                'type': 'code_block'
            })
        
        # Find inline code
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.findall(inline_pattern, llm_response)
        
        for code in inline_matches:
            if len(code.split()) <= 5 and any(cmd in code for cmd in ['cd', 'ls', 'git', 'npm', 'python']):
                commands.append({
                    'language': 'bash',
                    'code': code.strip(),
                    'type': 'inline'
                })
        
        return commands
    
    def _guess_language(self, code: str) -> str:
        """Guess programming language from code"""
        try:
            lexer = guess_lexer(code)
            return lexer.name.lower()
        except:
            # Fallback heuristics
            if any(word in code for word in ['sudo', 'apt', 'cd', 'ls', 'grep']):
                return 'bash'
            elif any(word in code for word in ['def ', 'import ', 'print(']):
                return 'python'
            elif any(word in code for word in ['npm', 'node', 'yarn']):
                return 'javascript'
            return 'bash'
    
    def show_response(self, llm_response: str):
        """Show LLM response in GUI"""
        self.commands = self.extract_commands(llm_response)
        
        # Run in main thread
        GLib.idle_add(self._create_window, llm_response)
    
    def _create_window(self, llm_response: str):
        """Create and show the main window"""
        self.app = Gtk.Application()
        self.app.connect('activate', lambda app: self._on_activate(app, llm_response))
        self.app.run([])
    
    def _on_activate(self, app, llm_response: str):
        """Application activate callback"""
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("Screenshot LLM Assistant")
        self.window.set_default_size(800, 600)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        
        # Create scrolled window for response
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Create text view for response
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_monospace(True)
        
        # Set response text
        buffer = self.text_view.get_buffer()
        buffer.set_text(llm_response)
        
        scrolled.set_child(self.text_view)
        main_box.append(scrolled)
        
        # Create commands section if commands found
        if self.commands:
            commands_label = Gtk.Label(label="Extracted Commands:")
            commands_label.set_markup("<b>Extracted Commands:</b>")
            commands_label.set_halign(Gtk.Align.START)
            main_box.append(commands_label)
            
            # Create command buttons
            for i, cmd in enumerate(self.commands):
                self._create_command_widget(main_box, cmd, i)
        
        # Create close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda b: self.window.destroy())
        main_box.append(close_button)
        
        self.window.set_child(main_box)
        self.window.present()
    
    def _create_command_widget(self, parent_box: Gtk.Box, command: dict, index: int):
        """Create widget for a single command"""
        # Command container
        cmd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cmd_frame = Gtk.Frame()
        cmd_frame.set_child(cmd_box)
        cmd_frame.set_margin_top(5)
        cmd_frame.set_margin_bottom(5)
        
        # Command label
        lang = command['language']
        cmd_label = Gtk.Label(label=f"{lang.title()} Command:")
        cmd_label.set_halign(Gtk.Align.START)
        cmd_box.append(cmd_label)
        
        # Command text with syntax highlighting
        cmd_text = Gtk.TextView()
        cmd_text.set_editable(False)
        cmd_text.set_monospace(True)
        cmd_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        buffer = cmd_text.get_buffer()
        buffer.set_text(command['code'])
        
        # Add some styling
        cmd_text.set_css_classes(["monospace"])
        
        cmd_scroll = Gtk.ScrolledWindow()
        cmd_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        cmd_scroll.set_max_content_height(150)
        cmd_scroll.set_child(cmd_text)
        cmd_box.append(cmd_scroll)
        
        # Button container
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Copy button
        copy_button = Gtk.Button(label="Copy")
        copy_button.connect("clicked", lambda b: self._copy_command(command['code']))
        button_box.append(copy_button)
        
        # Execute button (only for safe commands)
        if self._is_safe_command(command['code']):
            exec_button = Gtk.Button(label="Execute")
            exec_button.connect("clicked", lambda b: self._execute_command(command['code']))
            exec_button.add_css_class("suggested-action")
            button_box.append(exec_button)
        
        # Open terminal button
        terminal_button = Gtk.Button(label="Open Terminal")
        terminal_button.connect("clicked", lambda b: self._open_terminal_with_command(command['code']))
        button_box.append(terminal_button)
        
        cmd_box.append(button_box)
        parent_box.append(cmd_frame)
    
    def _copy_command(self, command: str):
        """Copy command to clipboard"""
        try:
            # Use wl-copy for Wayland or xclip for X11
            if os.environ.get('WAYLAND_DISPLAY'):
                subprocess.run(['wl-copy'], input=command.encode(), timeout=5)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=command.encode(), timeout=5)
            logger.info("Command copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy command: {e}")
    
    def _execute_command(self, command: str):
        """Execute command safely"""
        try:
            # Run in background thread to avoid blocking UI
            threading.Thread(
                target=self._run_command_in_thread,
                args=(command,),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
    
    def _run_command_in_thread(self, command: str):
        """Run command in background thread"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.expanduser('~')
            )
            
            output = f"Exit code: {result.returncode}\n"
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                output += f"Error:\n{result.stderr}\n"
                
            logger.info(f"Command executed: {command}")
            logger.info(f"Result: {output}")
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
    
    def _open_terminal_with_command(self, command: str):
        """Open terminal with command ready to run"""
        try:
            # Try different terminal emulators
            terminals = [
                ['gnome-terminal', '--', 'bash', '-c', f'echo "{command}"; exec bash'],
                ['cosmic-term', '-e', 'bash', '-c', f'echo "{command}"; exec bash'],
                ['kitty', 'bash', '-c', f'echo "{command}"; exec bash'],
                ['alacritty', '-e', 'bash', '-c', f'echo "{command}"; exec bash'],
                ['xterm', '-e', 'bash', '-c', f'echo "{command}"; exec bash']
            ]
            
            for terminal_cmd in terminals:
                try:
                    subprocess.Popen(terminal_cmd)
                    logger.info(f"Opened terminal with command: {command}")
                    break
                except FileNotFoundError:
                    continue
            else:
                logger.warning("No suitable terminal emulator found")
                
        except Exception as e:
            logger.error(f"Failed to open terminal: {e}")
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute automatically"""
        dangerous_patterns = [
            r'\brm\s+', r'\bmv\s+.*\s+/', r'\bcp\s+.*\s+/',
            r'\bsudo\b', r'\bsu\b', r'\bchmod\b', r'\bchown\b',
            r'\bdd\b', r'\bmkfs\b', r'\bformat\b',
            r'>\s*/', r'\|.*>', r'curl.*\|\s*sh', r'wget.*\|\s*sh'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        
        return True

def show_response_gui(llm_response: str):
    """Convenience function to show LLM response"""
    interface = CommandInterface()
    interface.show_response(llm_response)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample response
    test_response = """Here's how to list files and check git status:

```bash
ls -la
```

You can also check your git status:

```bash
git status
```

For Python, try:

```python
print("Hello, World!")
```

Use `cd ..` to go up one directory."""

    show_response_gui(test_response)