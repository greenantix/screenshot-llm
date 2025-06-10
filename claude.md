# Claude.md - Master Refactor Plan

## 1. Current Code Audit

### Assessment Summary
The current project is a Python-based desktop application that captures screenshots and analyzes them using AI models. While innovative in concept, the implementation reveals several architectural limitations:

### Top 5 Weaknesses

1. **Complex Dependency Chain**: The application requires numerous system-level dependencies (GTK3, evdev, screenshot tools, X11/Wayland APIs) making it difficult to install and maintain across different Linux distributions.

2. **Platform Lock-in**: The heavy reliance on Linux-specific tools (evdev for mouse input, grim/maim for screenshots) makes cross-platform support virtually impossible without major rewrites.

3. **Fragmented Architecture**: The codebase is split across multiple Python scripts with complex IPC mechanisms (Unix sockets, subprocess calls) creating potential race conditions and making debugging challenging.

4. **Limited UI Framework**: GTK3, while functional, provides a dated user experience compared to modern web technologies. The UI code is verbose and difficult to style consistently.

5. **Maintenance Burden**: The current approach requires maintaining custom implementations for screenshot capture, window detection, and AI integration rather than leveraging existing web interfaces that are continuously updated by the service providers.

## 2. New Architecture & Tech Stack Recommendation

### Primary Technology: **Tauri**

**Justification:**
- **Performance**: Tauri produces significantly smaller binaries (5-10MB vs Electron's 50-150MB) with lower memory usage
- **Security**: Built-in security features with a smaller attack surface than Electron
- **Native Feel**: Uses the OS's native webview, resulting in better system integration
- **Modern Stack**: Rust backend provides memory safety and excellent performance
- **Cross-Platform**: Seamless deployment to Windows, macOS, and Linux from a single codebase

### CSS Framework: **Tailwind CSS**

**Justification:**
- **Utility-First**: Perfect for rapid prototyping and consistent design system
- **Small Bundle Size**: Only includes CSS for classes actually used
- **Dark Mode**: Built-in dark mode support with minimal configuration
- **Component Patterns**: Easy to create reusable UI components
- **Developer Experience**: Excellent IDE support and documentation

### Project Structure

```
ai-chat-shell/
├── src/
│   ├── index.html          # Main app entry point
│   ├── styles/
│   │   └── main.css        # Tailwind imports and custom styles
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   ├── settings.js     # Settings panel logic
│   │   └── webview.js      # Webview management
│   └── components/
│       ├── sidebar.html    # Service selector sidebar
│       └── settings.html   # Settings panel template
├── src-tauri/
│   ├── src/
│   │   ├── main.rs         # Tauri backend entry point
│   │   └── commands.rs     # IPC command handlers
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri configuration
├── package.json            # Node dependencies
├── tailwind.config.js      # Tailwind configuration
└── settings.json           # User preferences (generated)
```

## 3. Phased Implementation Guide

### Phase 1: Foundation & Setup

#### Step 1: Initialize Project
```bash
# Install Rust and Node.js prerequisites
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Tauri CLI
cargo install tauri-cli

# Create new Tauri project
npm create tauri-app@latest ai-chat-shell -- --template vanilla
cd ai-chat-shell
```

#### Step 2: Install Dependencies
```bash
# Frontend dependencies
npm install -D tailwindcss@latest autoprefixer@latest
npm install lucide

# Initialize Tailwind
npx tailwindcss init -p
```

#### Step 3: Configure Tailwind
**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'ai-blue': '#3B82F6',
        'ai-purple': '#8B5CF6',
        'ai-green': '#10B981',
        'ai-dark': '#1F2937',
        'ai-darker': '#111827'
      }
    },
  },
  plugins: [],
}
```

#### Step 4: Basic Window Setup
**src-tauri/tauri.conf.json:**
```json
{
  "build": {
    "distDir": "../dist"
  },
  "package": {
    "productName": "AI Chat Shell",
    "version": "1.0.0"
  },
  "tauri": {
    "windows": [
      {
        "title": "AI Chat Shell",
        "width": 1200,
        "height": 800,
        "resizable": true,
        "fullscreen": false,
        "decorations": true,
        "transparent": false,
        "center": true
      }
    ],
    "security": {
      "csp": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com"
    }
  }
}
```

**src/index.html:**
```html
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat Shell</title>
    <link rel="stylesheet" href="./styles/main.css">
</head>
<body class="h-full bg-gray-50 dark:bg-ai-darker text-gray-900 dark:text-gray-100">
    <div id="app" class="h-full flex">
        <!-- Content will be injected here -->
    </div>
    <script src="./js/app.js" type="module"></script>
</body>
</html>
```

**src/styles/main.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
    .sidebar-item {
        @apply flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 cursor-pointer;
        @apply hover:bg-gray-200 dark:hover:bg-gray-700;
    }
    
    .sidebar-item.active {
        @apply bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300;
    }
}
```

### Phase 2: The Native Settings Panel

#### Settings UI Design Concept
- Clean, card-based layout
- Toggle switches for boolean options
- Dropdown for service selection
- Clear section headers
- Immediate visual feedback

**src/components/settings.html:**
```html
<div class="p-6 max-w-2xl mx-auto">
    <h2 class="text-2xl font-bold mb-6">Settings</h2>
    
    <!-- Theme Settings -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <h3 class="text-lg font-semibold mb-4">Appearance</h3>
        <div class="flex items-center justify-between">
            <label for="darkMode" class="text-sm font-medium">Dark Mode</label>
            <button id="darkModeToggle" class="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 dark:bg-gray-600 transition-colors">
                <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform translate-x-1 dark:translate-x-6"></span>
            </button>
        </div>
    </div>
    
    <!-- Default Service -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
        <h3 class="text-lg font-semibold mb-4">Default Service</h3>
        <select id="defaultService" class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-300 dark:border-gray-600">
            <option value="claude">Claude</option>
            <option value="chatgpt">ChatGPT</option>
            <option value="gemini">Gemini</option>
        </select>
    </div>
    
    <!-- Future Placeholders -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <h3 class="text-lg font-semibold mb-4">Advanced</h3>
        <p class="text-sm text-gray-600 dark:text-gray-400">API keys and custom instructions coming soon...</p>
    </div>
</div>
```

**src/js/settings.js:**
```javascript
import { invoke } from '@tauri-apps/api/tauri';
import { writeTextFile, readTextFile, BaseDirectory } from '@tauri-apps/api/fs';

class SettingsManager {
    constructor() {
        this.settings = {
            theme: 'light',
            defaultService: 'claude',
            // Future settings
            apiKeys: {},
            customInstructions: {}
        };
        this.settingsFile = 'settings.json';
    }
    
    async load() {
        try {
            const content = await readTextFile(this.settingsFile, { 
                dir: BaseDirectory.AppConfig 
            });
            this.settings = JSON.parse(content);
        } catch (error) {
            // First run, use defaults
            await this.save();
        }
        return this.settings;
    }
    
    async save() {
        await writeTextFile(this.settingsFile, JSON.stringify(this.settings, null, 2), {
            dir: BaseDirectory.AppConfig
        });
    }
    
    async updateTheme(isDark) {
        this.settings.theme = isDark ? 'dark' : 'light';
        document.documentElement.classList.toggle('dark', isDark);
        await this.save();
    }
    
    async updateDefaultService(service) {
        this.settings.defaultService = service;
        await this.save();
    }
    
    bindEvents() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        const defaultServiceSelect = document.getElementById('defaultService');
        
        darkModeToggle?.addEventListener('click', async () => {
            const isDark = !document.documentElement.classList.contains('dark');
            await this.updateTheme(isDark);
            
            // Update toggle visual state
            const span = darkModeToggle.querySelector('span');
            span.classList.toggle('translate-x-1', !isDark);
            span.classList.toggle('translate-x-6', isDark);
        });
        
        defaultServiceSelect?.addEventListener('change', async (e) => {
            await this.updateDefaultService(e.target.value);
        });
    }
    
    async initialize() {
        const settings = await this.load();
        
        // Apply theme
        document.documentElement.classList.toggle('dark', settings.theme === 'dark');
        
        // Set default service
        const serviceSelect = document.getElementById('defaultService');
        if (serviceSelect) {
            serviceSelect.value = settings.defaultService;
        }
        
        this.bindEvents();
    }
}

export default SettingsManager;
```

### Phase 3: The Webview Core

#### Main Layout Implementation
**src/components/sidebar.html:**
```html
<aside class="w-64 bg-gray-100 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
    <div class="p-4">
        <h1 class="text-xl font-bold">AI Chat Shell</h1>
    </div>
    
    <nav class="flex-1 px-3">
        <div class="space-y-1">
            <div class="sidebar-item active" data-service="claude">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
                </svg>
                <span>Claude</span>
            </div>
            
            <div class="sidebar-item" data-service="chatgpt">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
                </svg>
                <span>ChatGPT</span>
            </div>
            
            <div class="sidebar-item" data-service="gemini">
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
                </svg>
                <span>Gemini</span>
            </div>
        </div>
    </nav>
    
    <div class="p-3 border-t border-gray-200 dark:border-gray-700">
        <button id="settingsBtn" class="sidebar-item w-full">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            <span>Settings</span>
        </button>
    </div>
</aside>
```

**src/js/webview.js:**
```javascript
import { WebviewWindow } from '@tauri-apps/api/window';

class WebviewManager {
    constructor() {
        this.services = {
            claude: {
                name: 'Claude',
                url: 'https://claude.ai/chats',
                icon: 'claude-icon'
            },
            chatgpt: {
                name: 'ChatGPT', 
                url: 'https://chatgpt.com/',
                icon: 'chatgpt-icon'
            },
            gemini: {
                name: 'Gemini',
                url: 'https://gemini.google.com/',
                icon: 'gemini-icon'
            }
        };
        this.currentService = null;
        this.webviewContainer = null;
    }
    
    initialize(containerId) {
        this.webviewContainer = document.getElementById(containerId);
        this.bindSidebarEvents();
    }
    
    bindSidebarEvents() {
        const sidebarItems = document.querySelectorAll('.sidebar-item[data-service]');
        
        sidebarItems.forEach(item => {
            item.addEventListener('click', () => {
                const service = item.dataset.service;
                this.switchService(service);
                
                // Update active state
                sidebarItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
        });
    }
    
    async switchService(serviceName) {
        if (!this.services[serviceName]) return;
        
        const service = this.services[serviceName];
        this.currentService = serviceName;
        
        // Clear current content
        this.webviewContainer.innerHTML = '';
        
        // Create iframe for webview
        const iframe = document.createElement('iframe');
        iframe.src = service.url;
        iframe.className = 'w-full h-full border-0';
        iframe.allow = 'clipboard-write; clipboard-read';
        
        // Add loading state
        const loader = document.createElement('div');
        loader.className = 'absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-900';
        loader.innerHTML = `
            <div class="text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-ai-blue mx-auto"></div>
                <p class="mt-4 text-gray-600 dark:text-gray-400">Loading ${service.name}...</p>
            </div>
        `;
        
        this.webviewContainer.appendChild(loader);
        this.webviewContainer.appendChild(iframe);
        
        // Remove loader when iframe loads
        iframe.onload = () => {
            loader.remove();
        };
    }
}

export default WebviewManager;
```

**src/js/app.js:**
```javascript
import SettingsManager from './settings.js';
import WebviewManager from './webview.js';

class App {
    constructor() {
        this.settingsManager = new SettingsManager();
        this.webviewManager = new WebviewManager();
        this.currentView = 'webview';
    }
    
    async initialize() {
        // Load saved settings
        await this.settingsManager.initialize();
        
        // Build initial UI
        this.renderLayout();
        
        // Initialize webview manager
        this.webviewManager.initialize('mainContent');
        
        // Load default service
        const settings = await this.settingsManager.load();
        this.webviewManager.switchService(settings.defaultService);
        
        // Bind settings button
        this.bindSettingsButton();
    }
    
    renderLayout() {
        const app = document.getElementById('app');
        app.innerHTML = `
            ${this.loadComponent('sidebar')}
            <main id="mainContent" class="flex-1 relative">
                <!-- Webview content will be loaded here -->
            </main>
        `;
    }
    
    loadComponent(name) {
        // In production, these would be properly bundled
        const components = {
            sidebar: `<!-- Sidebar HTML from above -->`,
            settings: `<!-- Settings HTML from above -->`
        };
        return components[name] || '';
    }
    
    bindSettingsButton() {
        const settingsBtn = document.getElementById('settingsBtn');
        settingsBtn?.addEventListener('click', () => {
            this.showSettings();
        });
    }
    
    showSettings() {
        const mainContent = document.getElementById('mainContent');
        mainContent.innerHTML = this.loadComponent('settings');
        
        // Re-initialize settings bindings
        this.settingsManager.bindEvents();
        
        // Update sidebar active state
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.classList.remove('active');
        });
        document.getElementById('settingsBtn').classList.add('active');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const app = new App();
    await app.initialize();
});
```

### Phase 4: Integration & Polish

#### Theme Integration
**src-tauri/src/commands.rs:**
```rust
use tauri::Manager;

#[tauri::command]
async fn inject_theme(window: tauri::Window, theme: String) -> Result<(), String> {
    let css = if theme == "dark" {
        r#"
        :root {
            color-scheme: dark;
        }
        body {
            background-color: #1a1a1a !important;
        }
        "#
    } else {
        r#"
        :root {
            color-scheme: light;
        }
        "#
    };
    
    // This would inject CSS into the webview if possible
    // Implementation depends on the specific webview capabilities
    Ok(())
}
```

#### Enhanced Settings Integration
**src/js/settings.js (additions):**
```javascript
// Add to SettingsManager class
async applyThemeToWebviews() {
    const isDark = this.settings.theme === 'dark';
    
    // Attempt to inject basic theme CSS into iframes
    const iframes = document.querySelectorAll('iframe');
    iframes.forEach(iframe => {
        try {
            const style = iframe.contentDocument.createElement('style');
            style.textContent = isDark ? `
                :root { color-scheme: dark; }
                body { background: #1a1a1a !important; }
            ` : `
                :root { color-scheme: light; }
            `;
            iframe.contentDocument.head.appendChild(style);
        } catch (e) {
            // Cross-origin restrictions will prevent this for external sites
            console.log('Cannot inject styles due to cross-origin policy');
        }
    });
}
```

#### Final Polish Steps

1. **Add Window Controls** (for frameless window option):
```javascript
// Add custom window controls if using frameless window
const windowControls = `
<div class="window-controls flex items-center gap-2 absolute top-4 right-4">
    <button onclick="appWindow.minimize()" class="w-3 h-3 rounded-full bg-yellow-500"></button>
    <button onclick="appWindow.maximize()" class="w-3 h-3 rounded-full bg-green-500"></button>
    <button onclick="appWindow.close()" class="w-3 h-3 rounded-full bg-red-500"></button>
</div>
`;
```

2. **Add Keyboard Shortcuts**:
```javascript
// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case '1': webviewManager.switchService('claude'); break;
            case '2': webviewManager.switchService('chatgpt'); break;
            case '3': webviewManager.switchService('gemini'); break;
            case ',': app.showSettings(); break;
        }
    }
});
```

3. **Build and Package**:
```bash
# Development
npm run tauri dev

# Build for production
npm run tauri build

# The built application will be in:
# - Windows: src-tauri/target/release/bundle/msi/
# - macOS: src-tauri/target/release/bundle/dmg/
# - Linux: src-tauri/target/release/bundle/appimage/
```

## Conclusion

This refactor plan transforms a complex, platform-specific Python application into a modern, cross-platform shell that leverages existing web interfaces while maintaining a native feel through the settings panel. The phased approach ensures each component can be developed and tested independently, reducing risk and allowing for iterative improvements.

The final product will be a lightweight (~10MB), performant application that provides users with a unified interface to multiple AI services while staying automatically up-to-date with the latest features from each service provider.