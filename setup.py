#!/usr/bin/env python3
"""
Setup script for Screenshot LLM Assistant
"""

import os
import json
import getpass
import subprocess
import sys

def setup_config():
    """Setup configuration with API key"""
    config_file = os.path.expanduser("~/.local/share/screenshot-llm/config/config.json")
    
    print("🚀 Screenshot LLM Assistant Setup")
    print("=" * 40)
    
    # Load existing config
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except:
        config = {
            "provider": "anthropic",
            "api_key": "",
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 4096
        }
    
    print(f"\nCurrent provider: {config.get('provider', 'anthropic')}")
    
    # Get API provider
    provider = input("Choose provider (anthropic/openai) [anthropic]: ").strip() or "anthropic"
    config['provider'] = provider
    
    # Get API key
    if provider == "anthropic":
        print("\n📝 Anthropic API Key Setup:")
        print("Get your API key from: https://console.anthropic.com/")
        api_key = getpass.getpass("Enter your Anthropic API key: ").strip()
        config['model'] = config.get('model', 'claude-3-5-haiku-20241022')
    else:
        print("\n📝 OpenAI API Key Setup:")
        print("Get your API key from: https://platform.openai.com/api-keys")
        api_key = getpass.getpass("Enter your OpenAI API key: ").strip()
        config['model'] = config.get('model', 'gpt-4o-mini')
    
    if not api_key:
        print("❌ No API key provided. Setup cancelled.")
        return False
    
    config['api_key'] = api_key
    
    # Save config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved!")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def check_permissions():
    """Check if user has necessary permissions"""
    print("\n🔒 Checking Permissions...")
    
    # Check if user is in input group
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        if 'input' not in result.stdout:
            print("⚠️  User not in 'input' group. Mouse button detection may not work.")
            print("   Run: sudo usermod -a -G input $USER")
            print("   Then logout and login again.")
            return False
        else:
            print("✅ User is in input group")
            return True
    except:
        print("⚠️  Could not check group membership")
        return False

def test_dependencies():
    """Test if all dependencies are available"""
    print("\n🧪 Testing Dependencies...")
    
    # Test grim/screenshot tools
    try:
        subprocess.run(['grim', '--version'], capture_output=True, timeout=3)
        print("✅ grim (screenshot tool) is available")
    except:
        try:
            subprocess.run(['gnome-screenshot', '--version'], capture_output=True, timeout=3)
            print("✅ gnome-screenshot is available")
        except:
            print("⚠️  No screenshot tool found. Install grim or gnome-screenshot")
    
    # Test clipboard tool
    try:
        subprocess.run(['wl-copy', '--version'], capture_output=True, timeout=3)
        print("✅ wl-copy (clipboard) is available")
    except:
        try:
            subprocess.run(['xclip', '-version'], capture_output=True, timeout=3)
            print("✅ xclip (clipboard) is available")
        except:
            print("⚠️  No clipboard tool found. Install wl-clipboard or xclip")

def install_service():
    """Install systemd service"""
    print("\n⚙️  Installing Systemd Service...")
    
    script_path = os.path.expanduser("~/.local/share/screenshot-llm/screenshot-llm.py")
    venv_python = os.path.expanduser("~/.local/share/screenshot-llm/venv/bin/python")
    
    service_content = f"""[Unit]
Description=Screenshot to LLM Assistant
After=graphical-session.target

[Service]
Type=simple
ExecStart={venv_python} {script_path}
Restart=always
Environment="DISPLAY=:0"
Environment="WAYLAND_DISPLAY=wayland-0"

[Install]
WantedBy=default.target
"""
    
    service_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(service_dir, exist_ok=True)
    
    service_file = os.path.join(service_dir, "screenshot-llm.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Service installed to: {service_file}")
        print("\nTo enable and start the service:")
        print("  systemctl --user enable screenshot-llm.service")
        print("  systemctl --user start screenshot-llm.service")
        print("\nTo check status:")
        print("  systemctl --user status screenshot-llm.service")
        
        # Ask if user wants to enable service now
        enable = input("\nEnable service now? (y/N): ").strip().lower()
        if enable == 'y':
            try:
                subprocess.run(['systemctl', '--user', 'enable', 'screenshot-llm.service'], check=True)
                subprocess.run(['systemctl', '--user', 'start', 'screenshot-llm.service'], check=True)
                print("✅ Service enabled and started!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to enable service: {e}")
        
    except Exception as e:
        print(f"❌ Failed to install service: {e}")

def main():
    """Main setup function"""
    print("Screenshot LLM Assistant - Setup")
    print("This tool captures screenshots with mouse button 9 and sends them to an LLM for assistance.")
    print()
    
    # Step 1: Configure API
    if not setup_config():
        return
    
    # Step 2: Check permissions
    perms_ok = check_permissions()
    
    # Step 3: Test dependencies
    test_dependencies()
    
    # Step 4: Install service (optional)
    install_service_opt = input("\nInstall as systemd service for autostart? (y/N): ").strip().lower()
    if install_service_opt == 'y':
        install_service()
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    if not perms_ok:
        print("1. Logout and login again (for input group permissions)")
    print("2. Test with: python ~/.local/share/screenshot-llm/screenshot-llm.py --test-screenshot")
    print("3. Start daemon: python ~/.local/share/screenshot-llm/screenshot-llm.py")
    print("4. Press mouse button 9 to capture and analyze screenshots!")
    
    print("\nTroubleshooting:")
    print("- Check logs: ~/.local/share/screenshot-llm/logs/screenshot-llm.log")
    print("- Edit config: ~/.local/share/screenshot-llm/config/config.json")

if __name__ == "__main__":
    main()