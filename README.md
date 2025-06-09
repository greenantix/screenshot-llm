# Screenshot LLM Assistant v2.0 - Interactive Persistent Chat

A powerful desktop assistant that captures screenshots and provides intelligent analysis through a persistent, interactive chat interface. Now features continuous conversations, context preservation, and a modern GUI.

## ✨ New Features in v2.0

- **🗨️ Persistent Chat Interface**: Modern Tkinter-based window that stays open for continuous interaction
- **💬 Conversation History**: Full context preservation across screenshots and user messages  
- **🔄 Inter-Process Communication**: Robust IPC between screenshot daemon and chat GUI
- **💾 Conversation Persistence**: Save, load, and manage conversation sessions
- **🖼️ Screenshot Thumbnails**: Visual preview of screenshots with full-size viewing
- **⌨️ Keyboard Shortcuts**: Efficient navigation and control
- **🎛️ System Tray Integration**: Minimizes to tray instead of closing

## Features

### Core Functionality
- **Automatic Screenshot Capture**: Triggers on mouse button 9 press
- **Multi-Monitor Support**: Captures the screen containing the cursor
- **Context-Aware Prompts**: Detects active applications and working directories
- **Multiple LLM Providers**: Supports both Anthropic Claude and OpenAI GPT
- **Optimized Image Processing**: Automatically resizes images for efficient API transmission

### Chat Interface
- **Interactive Conversations**: Ask follow-up questions about screenshots
- **Message History**: Scrollable conversation with timestamps
- **Visual Screenshots**: Embedded thumbnails with click-to-expand
- **Export Options**: Save conversations as text files
- **Multiple Sessions**: Create, load, and manage different conversation threads

## Installation

1. Clone or download this repository to `~/.local/share/screenshot-llm`

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API key:
```bash
# Edit the config file
nano ~/.local/share/screenshot-llm/config/config.json

# Or set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
# or
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Option 1: Start Complete System
```bash
# Start both daemon and GUI with monitoring
python start-screenshot-llm.py

# Start GUI minimized to tray
python start-screenshot-llm.py --minimized

# Start daemon first (fallback mode)
python start-screenshot-llm.py --daemon-first
```

### Option 2: Start Components Separately
```bash
# Start GUI only
python screenshot-llm-gui.py

# Start daemon only (uses zenity fallback)
python screenshot-llm.py

# Start GUI minimized
python screenshot-llm-gui.py --minimized
```

### Option 3: Install as System Service
```bash
python screenshot-llm.py --install-service
systemctl --user enable screenshot-llm.service
systemctl --user start screenshot-llm.service
```

## Usage Workflow

1. **Take Screenshot**: Press mouse button 9 (side button)
2. **Automatic Processing**: Screenshot appears in chat window with LLM analysis
3. **Interactive Follow-up**: Type questions about the screenshot or ask for help
4. **Continuous Context**: Each new screenshot adds to the ongoing conversation
5. **Session Management**: Save conversations, start new ones, or load previous sessions

### Keyboard Shortcuts

- `Ctrl+Enter`: Send message
- `Ctrl+N`: New conversation
- `Ctrl+S`: Save conversation
- `Ctrl+Q`: Quit application
- `Esc`: Minimize to tray
- `Ctrl+C`: Copy selected text
- `Ctrl+Shift+C`: Copy entire conversation

## Configuration

Edit `config/config.json`:

```json
{
  "provider": "anthropic",
  "api_key": "your-api-key",
  "model": "claude-3-5-haiku-20241022",
  "max_tokens": 4096,
  "screenshot_dir": "~/.local/share/screenshot-llm/cache",
  "history_dir": "~/.local/share/screenshot-llm/history", 
  "mouse_button": 9,
  "auto_delete_screenshots": true,
  "persistent_chat": true,
  "auto_save_conversations": true,
  "max_conversation_length": 50,
  "window_always_on_top": false,
  "start_minimized": false
}
```

## Architecture

### System Components

1. **Screenshot Daemon** (`screenshot-llm.py`): Captures screenshots and handles mouse events
2. **Chat GUI** (`screenshot-llm-gui.py`): Persistent Tkinter window for conversations  
3. **IPC Handler** (`lib/ipc_handler.py`): Unix socket communication between processes
4. **Conversation Manager** (`lib/conversation.py`): Message history and persistence
5. **Startup Manager** (`start-screenshot-llm.py`): Coordinates launching and monitoring

### Process Flow

```
[Mouse Button 9] → [Screenshot Daemon] → [IPC] → [Chat GUI] → [LLM API] → [Response Display]
                                                     ↓
                                              [User Input] → [LLM API] → [Response Display]
```

### Inter-Process Communication

- **Protocol**: Unix domain sockets for fast, secure local communication
- **Message Types**: `screenshot`, `llm_response`, `show_window`, `hide_window`
- **Reliability**: Automatic reconnection and fallback mechanisms
- **Security**: User-only socket permissions

## File Structure

```
~/.local/share/screenshot-llm/
├── screenshot-llm.py              # Main daemon
├── screenshot-llm-gui.py          # GUI process  
├── start-screenshot-llm.py        # Startup coordinator
├── zenity_display.py              # Fallback display
├── test-persistent-chat.py        # Test suite
├── lib/
│   ├── mouse_listener.py          # Mouse event handling
│   ├── screenshot.py              # Screenshot capture logic
│   ├── context_detector.py        # Application context detection
│   ├── llm_client.py             # LLM API integration
│   ├── chat_window.py            # Persistent chat interface
│   ├── conversation.py           # Conversation management
│   ├── ipc_handler.py           # Inter-process communication
│   ├── command_interface.py       # Legacy GUI formatting
│   └── simple_interface.py        # Fallback display method
├── config/
│   ├── config.json               # Main configuration
│   └── contexts.json             # Context detection rules
├── conversations/                # Saved conversation sessions
├── cache/                        # Temporary screenshots
├── history/                      # Legacy response history
└── logs/                        # Application logs
```

## Testing

Run the test suite to verify installation:

```bash
python test-persistent-chat.py
```

### Manual Testing

```bash
# Test screenshot capture
python screenshot-llm.py --test-screenshot

# Test context detection  
python screenshot-llm.py --test-context

# Test GUI standalone
python screenshot-llm-gui.py

# Test IPC communication
python -c "from lib.ipc_handler import *; print('IPC imports OK')"
```

## Troubleshooting

### GUI Issues
```bash
# Check if GUI process is running
ps aux | grep screenshot-llm-gui

# Restart GUI only
pkill -f screenshot-llm-gui
python screenshot-llm-gui.py
```

### IPC Connection Issues
```bash
# Check IPC socket
ls -la ~/.local/share/screenshot-llm/screenshot-llm.sock

# Clear stale socket
rm ~/.local/share/screenshot-llm/screenshot-llm.sock
```

### Permission Issues
```bash
# Add user to input group for mouse access
sudo usermod -a -G input $USER
# Log out and back in
```

### Missing Screenshot Tools
```bash
# Wayland
sudo apt install grim wlr-randr

# X11
sudo apt install maim scrot xdotool
```

### Conversation Loading Issues
```bash
# Check conversation directory
ls ~/.local/share/screenshot-llm/conversations/

# Verify JSON format
python -m json.tool ~/.local/share/screenshot-llm/conversations/conversation_*.json
```

## Dependencies

- **Core**: Python 3.8+, evdev, Pillow, tkinter
- **LLM Clients**: anthropic, openai
- **Screenshot Tools**:
  - Wayland: `grim`, `wlr-randr`
  - X11: `maim` or `scrot`, `xrandr`, `xdotool`
- **GUI**: tkinter (built-in), Pillow for image handling
- **Fallback**: `zenity` or `PyGObject`

## Migration from v1.0

The new persistent chat system is fully backward compatible:

- **Existing configs**: Work unchanged
- **Service files**: Continue to work with new daemon
- **Fallback mode**: If GUI unavailable, falls back to original zenity behavior
- **Manual migration**: Old response history in `history/` can be referenced but won't auto-import

## Performance & Resource Usage

- **Memory**: ~50-100MB for GUI process, ~20-30MB for daemon
- **CPU**: Minimal when idle, brief spikes during screenshot processing
- **Storage**: Conversations stored as compact JSON files
- **Network**: Only during LLM API calls

## Future Enhancements

- Multiple conversation tabs
- Code syntax highlighting in responses  
- Quick action buttons (copy commands, run in terminal)
- Search within conversations
- Conversation templates for different contexts
- Export as Markdown with embedded images
- Voice input/output integration

## License

This project is provided as-is for educational and personal use.