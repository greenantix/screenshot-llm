# Screenshot LLM Assistant

A powerful, GTK-based desktop application that captures screenshots and analyzes them using AI models (OpenAI GPT-4 Vision or Anthropic Claude) to provide intelligent assistance and suggestions.

## Features

- **Quick Answer Pop-up**: Get immediate, at-cursor answers in a sleek, borderless GTK window.
- **Modern GTK Interface**: A fully-featured, tabbed chat window built with GTK for a native look and feel.
- **Smart Screenshot Capture**: Automatically detects context and captures screenshots.
- **AI Analysis**: Uses GPT-4 Vision or Claude to analyze screenshots and provide helpful suggestions.
- **Context Awareness**: Detects active applications, window titles, and working directories.
- **Mouse Button Trigger**: Configurable mouse button for quick screenshot capture.
- **Cross-Platform Support**: Works on Linux (X11 and Wayland).

## Installation

### Prerequisites

- Python 3.8 or higher
- GTK3 libraries
- Linux desktop environment (GNOME, KDE, XFCE, etc.)
- One of the following screenshot tools:
  - `grim` (Wayland)
  - `maim` (X11, recommended)
  - `scrot` (X11)

### Install Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install maim xdotool python3-gi python3-pip
```

#### Fedora/RHEL:
```bash
sudo dnf install maim xdotool python3-gobject python3-pip
```

#### Arch Linux:
```bash
sudo pacman -S maim xorg-xdotool python-gobject python-pip
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
Open the settings window from the main chat interface to configure your API keys, or edit `config/config.json` manually.

### 2. Configure Mouse Button (Optional)
The default configuration uses mouse button 9 (usually a thumb button). To change this, edit the `mouse_device_path` in the settings window or in `config/config.json`.

## Usage

### Starting the Application
Use the provided shell script to launch the application:
```bash
./run.sh
```
This will start both the main GTK chat window and the background daemon.

### Workflow

1. **Quick Answer**: Press the configured mouse button (default: button 9) to capture a screenshot. A pop-up window will appear at your cursor's location with a concise answer from the LLM.
2. **Detailed View**: From the pop-up, click "Open in Chat" to see the full conversation in the main GTK chat window.
3. **Persistent Chat**: The main window keeps a history of your conversations in a tabbed interface.

## File Structure

```
screenshot-llm-assistant/
├── config/
│   └── config.json          # Main configuration
├── lib/
│   ├── gtk_chat_window.py   # Main GTK chat window
│   ├── quick_answer_window.py # GTK pop-up window
│   ├── settings_window.py   # GTK settings dialog
│   ├── conversation_manager.py # Conversation handling
│   ├── context_detector.py  # Application context detection
│   ├── image_processor.py   # Image optimization
│   ├── ipc_handler.py       # Inter-process communication
│   ├── llm_client.py        # AI model API client
│   ├── logger.py            # Logging utilities
│   ├── mouse_listener.py    # Mouse input handling
│   └── screenshot.py        # Screenshot capture
├── conversations/           # Saved conversations
├── logs/                   # Application logs
├── screenshot-llm.py       # Main daemon script
├── run.sh                  # Main startup script
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
   - Log out and back in.

3. **"API key not configured"**
   - Open the settings from the main chat window and add your API key.

### Log Files
Check the `logs/` directory for detailed log files.

## Development

### Running Tests
```bash
# Test individual modules
python -m lib.screenshot
python -m lib.context_detector
python -m lib.llm_client
```

### Contributing
Pull requests are welcome! Please fork the repository, create a feature branch, and submit your changes with relevant tests.

## License

This project is licensed under the MIT License.

## Changelog

### Version 2.0.0
- **UI Overhaul**: Migrated from Tkinter to a modern GTK-based interface.
- **Quick Answer Pop-up**: Added an immediate, at-cursor pop-up for fast answers.
- **Redesigned Chat Window**: The main chat window is now a native GTK application.
- **Settings Dialog**: Added a new GTK settings window for easier configuration.
- **Zenity Fallback Removed**: Replaced the `zenity` dependency with the new pop-up window.