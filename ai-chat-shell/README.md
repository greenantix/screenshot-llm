# AI Chat Shell

A modern, cross-platform desktop application that provides a unified interface for multiple AI chat services including Claude, ChatGPT, Gemini, and Perplexity.

## 🎉 Phase 4 - Integration & Polish Complete ✅

This project has completed all 4 phases of the refactor plan, delivering a production-ready AI chat desktop application with:

### ✨ Features

- **Multi-Service Support**: Seamlessly switch between Claude, ChatGPT, Gemini, and Perplexity
- **Modern UI**: Clean, responsive interface with smooth animations
- **Dark/Light Themes**: Built-in theme switching with webview integration
- **Keyboard Shortcuts**: Comprehensive shortcuts for power users
- **Settings Management**: Persistent settings with cross-session memory
- **Window Controls**: Optional custom window controls for frameless mode
- **Cross-Platform**: Runs on Windows, macOS, and Linux

### 🎯 Phase Completion Status

- ✅ **Phase 1 - Foundation**: Tauri setup, Tailwind CSS, basic structure
- ✅ **Phase 2 - Settings Panel**: Native settings with theme switching
- ✅ **Phase 3 - Webview Core**: Multi-service webview management
- ✅ **Phase 4 - Integration & Polish**: Final integration and production features

## 🚀 Quick Start

### Prerequisites

- Node.js 16+
- Rust 1.60+
- Tauri CLI

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Install Tauri CLI (if not already installed):
   ```bash
   npm install -g @tauri-apps/cli
   ```

### Development

Start the development server:
```bash
npm run dev
```

Watch CSS changes (in separate terminal):
```bash
npm run watch:css
```

### Building

Build for production:
```bash
npm run build
```

Build optimized release:
```bash
npm run build:release
```

Build debug version:
```bash
npm run build:debug
```

Verify build configuration:
```bash
npm run verify:build
```

Clean build artifacts:
```bash
npm run clean
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + 1` | Switch to Claude |
| `Ctrl/Cmd + 2` | Switch to ChatGPT |
| `Ctrl/Cmd + 3` | Switch to Gemini |
| `Ctrl/Cmd + 4` | Switch to Perplexity |
| `Ctrl/Cmd + ,` | Open Settings |
| `Ctrl/Cmd + R` | Refresh Current Service |
| `Ctrl/Cmd + T` | Toggle Theme |
| `Escape` | Return from Settings to Chat |

## 🏗️ Project Structure

```
ai-chat-shell/
├── src/
│   ├── index.html              # Main app entry point
│   ├── components/
│   │   ├── sidebar.html        # Service navigation sidebar
│   │   └── settings.html       # Settings panel
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   ├── settings.js        # Settings management
│   │   └── webview.js         # Webview management
│   └── styles/
│       ├── main.css           # Tailwind setup with components
│       └── output.css         # Generated CSS (auto-generated)
├── src-tauri/
│   ├── src/
│   │   ├── main.rs            # Tauri backend entry
│   │   └── commands.rs        # Custom Tauri commands
│   ├── Cargo.toml             # Rust dependencies
│   ├── tauri.conf.json        # App configuration
│   └── build.rs              # Build script
├── package.json               # Node dependencies & scripts
└── tailwind.config.js         # Tailwind configuration
```

## 🎨 Design System

### Color Palette

- **Primary**: Indigo (`#4F46E5`) - Main actions and active states
- **Secondary**: Purple (`#8B5CF6`) - Accents and highlights
- **Success**: Emerald (`#10B981`) - Success states
- **Warning**: Amber (`#F59E0B`) - Warning states
- **Error**: Red (`#EF4444`) - Error states

### Dark Theme

- **Background**: Gray-900 (`#111827`)
- **Surface**: Gray-800 (`#1F2937`)
- **Border**: Gray-700 (`#374151`)

## 🔧 Configuration

### App Settings

Settings are automatically saved in the app's configuration directory:
- **Windows**: `%APPDATA%/ai-chat-shell/settings.json`
- **macOS**: `~/Library/Application Support/ai-chat-shell/settings.json`
- **Linux**: `~/.config/ai-chat-shell/settings.json`

### Supported Services

| Service | URL | Status |
|---------|-----|--------|
| Claude | https://claude.ai | ✅ Active |
| ChatGPT | https://chat.openai.com | ✅ Active |
| Gemini | https://gemini.google.com | ✅ Active |
| Perplexity | https://perplexity.ai | ✅ Active |

## 🛠️ Development Features

### Error Handling
- Graceful webview loading with retry mechanisms
- Connection status indicators
- Service health checks
- Comprehensive error recovery

### Performance
- Optimized webview management
- Efficient theme switching
- Minimal memory footprint
- Fast startup times

### Accessibility
- Keyboard navigation support
- Screen reader compatibility
- High contrast theme support
- Focus management

## 🚢 Production Deployment

### Build Optimization
- Minified CSS output
- Optimized Rust binary
- Reduced bundle size
- Platform-specific optimizations

### Distribution
- Windows: `.msi` installer
- macOS: `.dmg` image
- Linux: `.deb`, `.rpm`, and `.AppImage`

## 🔐 Security

- **Webview Isolation**: Each service runs in isolated webview
- **No Data Collection**: All data stays local
- **Secure Settings**: Encrypted settings storage
- **Update Security**: Signed updates via Tauri updater

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Tauri](https://tauri.app/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Icons from [Heroicons](https://heroicons.com/)

---

**AI Chat Shell** - Unifying AI conversations in one beautiful desktop app.