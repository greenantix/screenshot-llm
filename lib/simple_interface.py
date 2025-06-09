#!/usr/bin/env python3
import re
import subprocess
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class SimpleCommandInterface:
    """Simple text-based interface for testing without GTK"""
    
    def __init__(self):
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
        if any(word in code for word in ['sudo', 'apt', 'cd', 'ls', 'grep']):
            return 'bash'
        elif any(word in code for word in ['def ', 'import ', 'print(']):
            return 'python'
        elif any(word in code for word in ['npm', 'node', 'yarn']):
            return 'javascript'
        return 'bash'
    
    def show_response(self, llm_response: str):
        """Show LLM response in terminal"""
        print("\n" + "="*60)
        print("📱 Screenshot LLM Assistant Response")
        print("="*60)
        print("\n" + llm_response)
        
        # Extract and show commands
        self.commands = self.extract_commands(llm_response)
        
        if self.commands:
            print("\n" + "-"*40)
            print("🔧 Extracted Commands:")
            print("-"*40)
            
            for i, cmd in enumerate(self.commands, 1):
                print(f"\n{i}. {cmd['language'].title()} Command:")
                print(f"   {cmd['code']}")
                
                # Offer to copy to clipboard
                try:
                    response = input(f"   Copy to clipboard? (y/N): ").strip().lower()
                    if response == 'y':
                        self._copy_command(cmd['code'])
                        print("   ✅ Copied to clipboard!")
                except KeyboardInterrupt:
                    print("\n   Skipped.")
        
        print("\n" + "="*60)
        input("Press Enter to close...")
    
    def _copy_command(self, command: str):
        """Copy command to clipboard"""
        try:
            if os.environ.get('WAYLAND_DISPLAY'):
                subprocess.run(['wl-copy'], input=command.encode(), timeout=5)
            else:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=command.encode(), timeout=5)
        except Exception as e:
            logger.warning(f"Could not copy to clipboard: {e}")

def show_response_simple(llm_response: str):
    """Convenience function to show LLM response"""
    interface = SimpleCommandInterface()
    interface.show_response(llm_response)

if __name__ == "__main__":
    # Test with sample response
    test_response = """Here's how to list files and check git status:

```bash
ls -la
```

You can also check your git status:

```bash
git status
```

Use `cd ..` to go up one directory."""

    show_response_simple(test_response)