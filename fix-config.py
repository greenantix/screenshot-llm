#!/usr/bin/env python3
"""
Fix config file issues for Screenshot LLM Assistant
"""

import os
import json
from pathlib import Path

def main():
    print("🔧 Screenshot LLM Assistant - Config Fix Tool")
    print("=" * 50)
    
    # Check for config files in different locations
    config_locations = [
        "config/config.json",  # Current directory
        "~/.local/share/screenshot-llm/config/config.json",  # User directory
        os.path.expanduser("~/.local/share/screenshot-llm/config/config.json")
    ]
    
    print("\n📁 Checking config file locations...")
    
    for location in config_locations:
        expanded_path = os.path.expanduser(location)
        if os.path.exists(expanded_path):
            print(f"✅ Found: {expanded_path}")
            
            # Check if it has the old API key
            try:
                with open(expanded_path, 'r') as f:
                    config = json.load(f)
                    
                api_key = config.get('llm', {}).get('api_key', '')
                if api_key and api_key.endswith('S_8A'):
                    print(f"⚠️  Contains old API key ending in 'S_8A'")
                    
                    # Ask if user wants to clear it
                    response = input(f"Clear old API key from {expanded_path}? (y/n): ")
                    if response.lower() == 'y':
                        config['llm']['api_key'] = ''
                        with open(expanded_path, 'w') as f:
                            json.dump(config, f, indent=2)
                        print(f"✅ Cleared API key from {expanded_path}")
                elif api_key:
                    print(f"🔑 Has API key: {api_key[:8]}...{api_key[-4:]}")
                else:
                    print(f"📝 API key is empty (will read from environment)")
                    
            except Exception as e:
                print(f"❌ Error reading {expanded_path}: {e}")
        else:
            print(f"❌ Not found: {expanded_path}")
    
    # Check environment variables
    print("\n🌍 Checking environment variables...")
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:8]}...{openai_key[-4:]}")
    else:
        print("❌ OPENAI_API_KEY not set")
        
    if anthropic_key:
        print(f"✅ ANTHROPIC_API_KEY: {anthropic_key[:8]}...{anthropic_key[-4:]}")
    else:
        print("❌ ANTHROPIC_API_KEY not set")
    
    print("\n💡 Recommendations:")
    if not openai_key and not anthropic_key:
        print("1. Set environment variable: export OPENAI_API_KEY='your-key'")
        print("2. Or run: python setup-api-key.py")
    
    print("3. Restart the daemon after making changes")
    print("4. Check logs in logs/ directory for detailed errors")

if __name__ == "__main__":
    main()