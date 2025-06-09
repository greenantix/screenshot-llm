#!/usr/bin/env python3
"""
Test the markdown parsing with copy code buttons
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path

# Add lib directory to path
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

from chat_window import PersistentChatWindow

def test_markdown_rendering():
    """Test the new markdown rendering with copy buttons"""
    
    # Sample markdown with code blocks
    sample_response = """
# Here's how to set up a Python virtual environment

First, navigate to your project directory:

```bash
cd /path/to/your/project
python -m venv venv
source venv/bin/activate  # On Linux/Mac
```

Then install your dependencies:

```python
# requirements.txt
import os
import sys

def setup_environment():
    print("Setting up virtual environment...")
    return True
```

You can also use inline code like `pip install -r requirements.txt` for quick commands.

**Important**: Make sure to activate your virtual environment before installing packages.
"""
    
    # Create a test window
    root = tk.Tk()
    root.title("Markdown Test")
    root.geometry("800x600")
    root.configure(bg="#2d2d2d")
    
    # Create text widget
    text_widget = tk.Text(
        root,
        wrap=tk.WORD,
        bg="#2d2d2d",
        fg="#ffffff",
        font=("SF Pro Display", 11),
        padx=10,
        pady=10
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create a minimal chat window instance just for the markdown parser
    config = {
        "ui": {
            "theme": {
                "background": "#2d2d2d",
                "foreground": "#ffffff", 
                "accent": "#48b9c7",
                "surface": "#3c3c3c"
            }
        }
    }
    
    # We'll simulate the parser without creating the full window
    class MarkdownTester:
        def __init__(self):
            self.bg_color = "#2d2d2d"
            self.fg_color = "#ffffff"
            self.accent_color = "#48b9c7"
            self.surface_color = "#3c3c3c"
            
        def _copy_to_clipboard(self, text):
            print(f"Copying to clipboard: {text[:50]}...")
            # Use wl-copy for actual copying
            try:
                import subprocess
                subprocess.run(['wl-copy'], input=text.encode(), timeout=5, check=True)
                print("✅ Copied to clipboard!")
            except Exception as e:
                print(f"❌ Copy failed: {e}")
                
        def _parse_markdown(self, text, text_widget):
            """Copy the method from chat_window.py"""
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
        
        def _insert_code_block(self, text_widget, code_block):
            """Insert a code block with copy button"""
            lines = code_block.strip().split('\n')
            if len(lines) < 2:
                return
            
            # Extract language and code
            first_line = lines[0]
            language = first_line[3:].strip() if len(first_line) > 3 else "text"
            code_content = '\n'.join(lines[1:-1])  # Remove ``` lines
            
            if not code_content.strip():
                return
            
            # Insert code block header
            text_widget.insert(tk.END, f"\n{language.title()} Code:\n", "bold")
            
            # Insert the code with styling
            text_widget.insert(tk.END, code_content, "code_block")
            
            # Create copy button frame
            button_frame = tk.Frame(text_widget, bg=self.bg_color)
            copy_button = ttk.Button(
                button_frame,
                text="📋 Copy",
                command=lambda: self._copy_to_clipboard(code_content)
            )
            copy_button.pack(pady=2)
            
            # Insert button as window in text widget
            text_widget.insert(tk.END, "\n")
            text_widget.window_create(tk.END, window=button_frame)
            text_widget.insert(tk.END, "\n\n")
        
        def _parse_regular_markdown(self, text_widget, text):
            """Parse regular markdown text"""
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
        
        def _parse_inline_code(self, text_widget, line):
            """Parse line with inline code"""
            import re
            parts = re.split(r'(`[^`]+`)', line)
            
            for part in parts:
                if part.startswith('`') and part.endswith('`'):
                    code_text = part[1:-1]
                    text_widget.insert(tk.END, code_text, "code")
                else:
                    self._parse_text_formatting(text_widget, part)
        
        def _parse_text_formatting(self, text_widget, text):
            """Parse bold and italic formatting"""
            import re
            parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', text)
            
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    text_widget.insert(tk.END, part[2:-2], "bold")
                elif part.startswith('*') and part.endswith('*'):
                    text_widget.insert(tk.END, part[1:-1], "italic")
                else:
                    text_widget.insert(tk.END, part)
    
    # Create markdown tester and render the sample
    tester = MarkdownTester()
    tester._parse_markdown(sample_response, text_widget)
    
    # Add instructions
    instruction_frame = tk.Frame(root, bg="#2d2d2d")
    instruction_frame.pack(fill=tk.X, padx=10, pady=5)
    
    instructions = tk.Label(
        instruction_frame,
        text="📋 Click the 'Copy' buttons to test the copy functionality!",
        bg="#2d2d2d",
        fg="#48b9c7",
        font=("SF Pro Display", 12, "bold")
    )
    instructions.pack()
    
    root.mainloop()

if __name__ == "__main__":
    test_markdown_rendering()