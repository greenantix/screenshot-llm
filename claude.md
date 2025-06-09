# Screenshot LLM Assistant v2.0 - Interactive Persistent Chat

## Overview
Transform the current one-shot screenshot analyzer into an interactive, persistent chat assistant that maintains context across interactions and allows user input.

## Current State
- Single screenshot → LLM → Display response in zenity → Close
- No conversation history
- No ability to ask follow-up questions
- Context is lost after each interaction

## Target Features

### 1. Persistent Chat Window
Replace zenity with a custom GTK or Tkinter window that:
- Stays open after displaying response
- Shows conversation history (scrollable)
- Has an input field at the bottom for user questions
- Minimizes to system tray instead of closing

### 2. Smart Window Management
- If window is already open: bring to front and add new screenshot
- If window is closed: create new window
- Keyboard shortcuts: 
  - `Esc` to minimize (not close)
  - `Ctrl+Q` to actually quit
  - `Ctrl+C` to copy selected text
  - `Ctrl+Shift+C` to copy entire conversation

### 3. Conversation Context
- Maintain full conversation history in memory
- Each screenshot adds to context, not replaces it
- Show timestamps for each interaction
- Visual separation between user inputs, screenshots, and LLM responses

### 4. Enhanced Interaction Model
```
[Screenshot taken] → [Added to chat with timestamp]
[LLM analyzes with full context] → [Response appears]
[User can type follow-up] → [Send to LLM with context]
[Take another screenshot] → [Continues same conversation]
```

## Implementation Architecture

### Core Components

#### 1. Chat Window Manager (`chat_window.py`)
```python
class PersistentChatWindow:
    def __init__(self):
        self.conversation_history = []
        self.window = None
        self.is_visible = False
        
    def show_or_focus(self):
        """Bring existing window to front or create new"""
        
    def add_screenshot(self, image_path, context):
        """Add screenshot to conversation"""
        
    def add_user_message(self, text):
        """Add user text input to conversation"""
        
    def add_llm_response(self, response):
        """Add LLM response to conversation"""
```

#### 2. Conversation Manager (`conversation.py`)
```python
class ConversationManager:
    def __init__(self):
        self.messages = []  # Full conversation history
        self.current_context = {}  # App context, working directory, etc.
        
    def add_screenshot_message(self, image_path, context):
        """Format screenshot as conversation message"""
        
    def get_messages_for_api(self):
        """Format conversation for LLM API"""
        
    def save_conversation(self):
        """Save to disk for persistence"""
        
    def load_conversation(self):
        """Load previous conversation on startup"""
```

#### 3. Window Design (Tkinter-based for lightweight)
```
+------------------------------------------+
| Screenshot LLM Assistant - Active Chat    | [_][□][X]
+------------------------------------------+
| [Conversation Area - Scrollable]         |
| ┌────────────────────────────────────┐   |
| │ [2:45 PM] Screenshot: terminal      │   |
| │ [Image thumbnail - click to expand] │   |
| │                                     │   |
| │ [2:45 PM] Assistant:               │   |
| │ I see you're working on a Python   │   |
| │ script. The error on line 42...    │   |
| │                                     │   |
| │ [2:46 PM] You:                     │   |
| │ How do I fix the import error?     │   |
| │                                     │   |
| │ [2:46 PM] Assistant:               │   |
| │ To fix the import error, you need..│   |
| └────────────────────────────────────┘   |
|                                          |
| [Input Field]                     [Send] |
+------------------------------------------+
| Status: Connected | Context: Terminal    |
+------------------------------------------+
```

### Key Implementation Details

#### 1. Message Format
Each message in conversation history:
```json
{
    "timestamp": "2025-06-09T14:45:32",
    "type": "screenshot|user|assistant",
    "content": "text content",
    "image_path": "path/to/image.png",  // if screenshot
    "context": {
        "app": "terminal",
        "window_title": "zsh",
        "working_directory": "/home/user/project"
    }
}
```

#### 2. IPC (Inter-Process Communication)
Since the daemon runs separately from the window:
- Use Unix domain socket or named pipe
- Commands: `show_window`, `add_screenshot`, `close_window`
- Window process runs independently, daemon sends commands

#### 3. Persistence
- Save conversation to `~/.local/share/screenshot-llm/conversations/`
- Auto-save every message
- Load last conversation on startup
- Option to start new conversation

### File Structure Additions
```
~/.local/share/screenshot-llm/
├── lib/
│   ├── chat_window.py        # Persistent window implementation
│   ├── conversation.py       # Conversation management
│   └── ipc_handler.py       # Inter-process communication
├── conversations/           # Saved conversations
│   └── 2025-06-09_14-45.json
└── screenshot-llm-gui.py    # Separate GUI process
```

## Implementation Phases

### Phase 1: Basic Persistent Window
1. Create Tkinter-based chat window
2. Implement basic message display (text only)
3. Add input field and send functionality
4. Connect to existing screenshot daemon via IPC

### Phase 2: Screenshot Integration
1. Display screenshot thumbnails in chat
2. Click to view full size
3. Maintain screenshot context in conversation
4. Update daemon to send screenshots to window

### Phase 3: Conversation Management
1. Implement full conversation history for API
2. Add message timestamps and formatting
3. Save/load conversations
4. Add "New Conversation" button

### Phase 4: Enhanced Features
1. System tray integration
2. Keyboard shortcuts
3. Copy conversation/code blocks
4. Export conversation as markdown
5. Search within conversation

### Phase 5: Advanced Features
1. Multiple conversation tabs
2. Code syntax highlighting in responses
3. Quick actions (copy commands, run in terminal)
4. Conversation templates for different contexts

## Technical Decisions

### Why Tkinter over GTK4?
- More lightweight
- Better cross-platform
- Easier to customize
- No complex dependencies
- Built into Python

### IPC Method: Unix Domain Socket
- Fast local communication
- Secure (filesystem permissions)
- Reliable message delivery
- Easy to implement in Python

### Message Queue Design
- Daemon queues messages if window not ready
- Window requests queued messages on startup
- Prevents lost screenshots/responses

## Configuration Updates
Add to `config.json`:
```json
{
    "persistent_chat": true,
    "auto_save_conversations": true,
    "max_conversation_length": 50,  // messages before truncation
    "window_always_on_top": false,
    "start_minimized": false,
    "theme": "light"  // or "dark"
}
```

## Usage Flow
1. User presses mouse button 9
2. Screenshot captured by daemon
3. Daemon sends to GUI process via IPC
4. GUI adds screenshot to conversation
5. GUI sends full conversation to LLM API
6. Response displayed in chat
7. User can type follow-up questions
8. Window stays open for continued interaction

## Testing Plan
1. Test IPC between daemon and GUI
2. Verify conversation persistence
3. Test window focus/minimize behavior
4. Stress test with long conversations
5. Test with multiple screenshots in sequence

## Performance Considerations
- Lazy load images (thumbnails in chat)
- Truncate old messages for API (keep in UI)
- Async API calls to prevent UI freezing
- Efficient message rendering (virtual scrolling)

## Security Notes
- IPC socket permissions (user-only)
- Don't store API keys in conversation files
- Option to exclude sensitive screenshots
- Clear conversation history command

This implementation transforms the tool from a simple screenshot analyzer into a powerful debugging assistant that maintains context and allows natural back-and-forth interaction.
