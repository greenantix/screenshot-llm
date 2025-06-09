# Screenshot LLM Assistant

A lightweight Linux tool that captures screenshots on mouse button 9 press, sends them to an LLM with context-aware prompts, and provides an efficient interface for executing returned commands.

## 🚀 Quick Start

1. **Run setup:**
   ```bash
   source ~/.local/share/screenshot-llm/venv/bin/activate
   python ~/.local/share/screenshot-llm/setup.py
   ```

2. **Test screenshot capture:**
   ```bash
   python ~/.local/share/screenshot-llm/screenshot-llm.py --test-screenshot
   ```

3. **Start the daemon:**
   ```bash
   python ~/.local/share/screenshot-llm/screenshot-llm.py
   ```

4. **Press mouse button 9** anywhere to capture and analyze!

## 🎯 Features

- **Context-Aware**: Detects your current application and builds smart prompts
- **Multi-Monitor Support**: Captures the screen containing your cursor
- **Command Extraction**: Automatically finds and formats commands from LLM responses
- **Safe Execution**: Validates commands before offering execution
- **Clipboard Integration**: One-click copying of commands
- **Multiple LLM Providers**: Supports Anthropic Claude and OpenAI

## 🖱️ Usage

1. **Capture Screenshot**: Press mouse button 9 (forward button)
2. **Wait for Analysis**: LLM analyzes the screenshot with context
3. **Review Results**: Commands are extracted and displayed
4. **Copy/Execute**: Click to copy commands or open terminal

## ⚙️ Configuration

Edit `~/.local/share/screenshot-llm/config/config.json`:

```json
{
  "provider": "anthropic",
  "api_key": "your-api-key-here",
  "model": "claude-3-5-haiku-20241022",
  "max_tokens": 4096,
  "auto_delete_screenshots": true
}
```

### API Keys

- **Anthropic**: Get from [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI**: Get from [platform.openai.com](https://platform.openai.com/api-keys)

You can also set environment variables:
```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

## 🔧 Context Detection

The tool automatically detects your current application and adapts prompts:

- **Terminal**: Includes current directory and git status
- **VS Code**: Includes project and file context
- **Browser**: Includes page title and URL context
- **Default**: Basic window information

Customize contexts in `~/.local/share/screenshot-llm/config/contexts.json`.

## 🖥️ System Requirements

- **OS**: Pop!_OS 22.04+ (or Ubuntu/Debian with Wayland)
- **Python**: 3.10+
- **Hardware**: Multi-monitor setup supported
- **Permissions**: User must be in `input` group

## 📦 Dependencies

### System Dependencies
```bash
sudo apt install python3-pip python3-venv grim slurp wl-clipboard python3-evdev
```

### Python Dependencies
- `evdev` - Mouse event detection
- `anthropic` / `openai` - LLM API clients
- `Pillow` - Image processing
- `pygments` - Syntax highlighting

## 🔒 Permissions

The tool needs access to input devices for mouse button detection:

```bash
sudo usermod -a -G input $USER
# Logout and login again
```

## 🔄 Autostart (Optional)

Install as systemd service:

```bash
python ~/.local/share/screenshot-llm/setup.py
# Choose 'y' when prompted about systemd service

# Manual installation:
systemctl --user enable screenshot-llm.service
systemctl --user start screenshot-llm.service
```

## 🧪 Testing

Test individual components:

```bash
# Test screenshot capture
python ~/.local/share/screenshot-llm/screenshot-llm.py --test-screenshot

# Test context detection
python ~/.local/share/screenshot-llm/screenshot-llm.py --test-context

# Test simple interface
python ~/.local/share/screenshot-llm/lib/simple_interface.py
```

## 📝 Logs

Check logs for troubleshooting:
```bash
tail -f ~/.local/share/screenshot-llm/logs/screenshot-llm.log
```

## 🔧 Troubleshooting

### Mouse Button Not Working
- Ensure you're in the `input` group: `groups | grep input`
- Logout and login after adding to group
- Check mouse device access: `ls -la /dev/input/event*`

### Screenshot Issues
- **Wayland**: Ensure `grim` is installed
- **X11**: Install `maim` or `scrot`
- Test manually: `grim test.png`

### No GUI
- Install GTK4 development packages for full GUI
- Simple text interface will be used as fallback

### API Errors
- Verify API key in config file
- Check network connectivity
- Review API quota and billing

## 📁 File Structure

```
~/.local/share/screenshot-llm/
├── screenshot-llm.py          # Main daemon
├── setup.py                   # Setup script
├── venv/                      # Python virtual environment
├── config/
│   ├── config.json           # API keys and settings
│   └── contexts.json         # Application context profiles
├── lib/
│   ├── mouse_listener.py     # Mouse event handling
│   ├── screenshot.py         # Screenshot capture
│   ├── context_detector.py   # Application context detection
│   ├── llm_client.py        # LLM API interface
│   ├── command_interface.py  # GUI for commands
│   └── simple_interface.py   # Fallback text interface
├── cache/                    # Temporary screenshots
├── history/                  # Interaction history
└── logs/                     # Application logs
```

## 🚧 Roadmap

- **Phase 2**: Advanced context detection and smart prompts
- **Phase 3**: Enhanced GUI with syntax highlighting
- **Phase 4**: Voice input and multi-modal support

## 🤝 Contributing

This is a personal productivity tool. Feel free to fork and adapt for your needs!

## 📄 License

MIT License - Use and modify as needed for your productivity workflow.