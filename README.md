# Screenshot LLM Assistant

A powerful desktop application that captures screenshots and analyzes them using AI models (OpenAI GPT-4 Vision or Anthropic Claude) to provide intelligent assistance and suggestions.

## Features

- **Smart Screenshot Capture**: Automatically detects context and captures screenshots
- **AI Analysis**: Uses GPT-4 Vision or Claude to analyze screenshots and provide helpful suggestions
- **Context Awareness**: Detects active applications, window titles, and working directories
- **Persistent Chat Interface**: Tabbed conversation interface with markdown support
- **System Tray Integration**: Minimizes to system tray for background operation
- **Mouse Button Trigger**: Configurable mouse button for quick screenshot capture
- **Cross-Platform Support**: Works on Linux (X11 and Wayland), with planned Windows/macOS support

## Installation

### Prerequisites

- Python 3.8 or higher
- Linux desktop environment (GNOME, KDE, XFCE, etc.)
- One of the following screenshot tools:
  - `grim` (Wayland)
  - `maim` (X11, recommended)
  - `scrot` (X11)
  - `gnome-screenshot`
  - `spectacle` (KDE)

### Install Screenshot Tools

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install maim xdotool python3-tk python3-pip
```

#### Fedora/RHEL:
```bash
sudo dnf install maim xdotool tkinter python3-pip
```

#### Arch Linux:
```bash
sudo pacman -S maim xorg-xdotool tk python-pip
```

### Install Python Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd screenshot-llm-assistant

# Install Python dependencies
pip install -r requirements.txt
```

## Configuration

### 1. Set up API Keys

**Quick Setup (Recommended)**:
```bash
# Run the interactive setup script
python setup-api-key.py
```

**Manual Setup**:

#### Option A: Environment Variables (Recommended)
```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Make permanent by adding to ~/.bashrc or ~/.zshrc
echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.bashrc
```

#### Option B: Edit config/config.json
```json
{
  "llm": {
    "provider": "openai",
    "api_key": "your-openai-api-key",
    "model": "gpt-4o",
    "max_tokens": 4096,
    "temperature": 0.7
  }
}
```

**Valid Models:**
- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` (with vision)
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`

### 2. Configure Mouse Button (Optional)

The default configuration uses mouse button 9 (usually thumb button). To change this, edit the `mouse_button` setting in the daemon configuration.

### 3. Test the Installation

```bash
# Test the GUI components
python test-gui.py

# Test screenshot capture
python -m lib.screenshot
```

## Usage

### Starting the Application

1. **Start the GUI (persistent mode)**:
   ```bash
   python screenshot-llm-gui.py
   ```
   The GUI will start and wait for screenshots from the daemon.

2. **Start the daemon (screenshot capture)**:
   ```bash
   python screenshot-llm.py
   ```
   The daemon will listen for mouse button presses and capture screenshots.

### Alternative: Run in background
```bash
# Start GUI minimized to tray
python screenshot-llm-gui.py --minimized

# Start daemon in background
nohup python screenshot-llm.py &
```

### Taking Screenshots

1. **Mouse Button**: Press the configured mouse button (default: button 9) to capture a screenshot
2. **Manual**: Run the daemon manually: `python screenshot-llm.py`
3. **GUI**: Use the chat interface to ask questions about previously captured screenshots

### Using the Chat Interface

- **Multiple Tabs**: Create new conversation tabs with Ctrl+T
- **Send Messages**: Type in the input area and press Enter (Shift+Enter for new lines)
- **View Screenshots**: Click on thumbnail images to view full size
- **Copy Text**: Ctrl+C for selected text, Ctrl+Shift+C for entire conversation
- **Save/Load**: Ctrl+S to save, Ctrl+L to load previous conversations

## Keyboard Shortcuts

- `Ctrl+T`: New conversation tab
- `Ctrl+W`: Close current tab
- `Ctrl+N`: New conversation
- `Ctrl+S`: Save conversation
- `Ctrl+L`: Load conversation
- `Ctrl+C`: Copy selected text
- `Ctrl+Shift+C`: Copy entire conversation
- `Escape`: Minimize to system tray
- `Ctrl+Q`: Quit application

## File Structure

```
screenshot-llm-assistant/
├── config/
│   ├── config.json          # Main configuration
│   └── contexts.json        # Context detection rules
├── lib/
│   ├── chat_window.py       # Main GUI window
│   ├── conversation_manager.py  # Conversation handling
│   ├── context_detector.py  # Application context detection
│   ├── image_processor.py   # Image optimization and thumbnails
│   ├── ipc_handler.py       # Inter-process communication
│   ├── llm_client.py        # AI model API client
│   ├── logger.py            # Logging utilities
│   ├── mouse_listener.py    # Mouse input handling
│   ├── screenshot.py        # Screenshot capture
│   ├── tab_manager.py       # Chat tab management
│   └── tray_manager.py      # System tray integration
├── conversations/           # Saved conversations
├── logs/                   # Application logs
├── screenshot-llm.py       # Main daemon script
├── screenshot-llm-gui.py   # GUI launcher
├── test-gui.py            # Test script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

### Common Issues

1. **"No screenshot tool found"**
   - Install a screenshot tool: `sudo apt install maim` (Ubuntu/Debian)
   - Check if tools are in PATH: `which maim`

2. **"Permission denied" for mouse events**
   - Add user to input group: `sudo usermod -a -G input $USER`
   - Log out and back in
   - Or run with sudo (not recommended)

3. **"API key not configured"**
   - Set your API key in `config/config.json`
   - Or set environment variable: `export OPENAI_API_KEY="your-key"`

4. **GUI doesn't show screenshots**
   - Check if daemon is running: `ps aux | grep screenshot-llm`
   - Check logs in `logs/` directory
   - Ensure IPC socket permissions are correct

5. **Screenshots are black/empty**
   - Some applications block screenshots for security
   - Try different screenshot tools
   - Check if running under Wayland (may need additional setup)

### Debug Mode

Run with debug logging:
```bash
# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from lib.chat_window import PersistentChatWindow
window = PersistentChatWindow()
window.mainloop()
"
```

### Log Files

Check the following log files for debugging:
- `logs/screenshot-llm-gui.log` - GUI application logs
- `logs/screenshot-llm-daemon.log` - Screenshot daemon logs

## Development

### Running Tests
```bash
# Test GUI components
python test-gui.py

# Test individual modules
python -m lib.screenshot
python -m lib.context_detector
python -m lib.llm_client
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Security Notes

- API keys are stored in plain text in `config/config.json`
- Consider using environment variables for production deployment
- Screenshots may contain sensitive information - they are stored temporarily
- IPC socket uses user-only permissions (0o600)

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Basic screenshot capture and AI analysis
- Tabbed chat interface
- System tray integration
- Context-aware prompts
- Support for OpenAI and Anthropic APIs