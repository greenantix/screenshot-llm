# AI Chat Shell - Tauri Application

A multi-service AI chat interface built with Tauri, providing access to Claude, ChatGPT, Gemini, and Perplexity in a native desktop application.

## Current Status

✅ **Working:**
- Tauri application structure setup
- Sidebar navigation with service icons
- Settings management system with theme switching
- Module resolution and Tauri API integration
- Null-safe DOM element handling

⚠️ **Partially Working:**
- Application launches and displays UI
- Tauri API loading (with fallback to mock functions)
- Webview container creation

❌ **Not Working:**
- Webview content loading (main content area is empty)
- Service switching functionality
- Cross-origin iframe content display

## Key Issues to Resolve

### 1. Webview Content Loading
**Problem:** Main content area shows empty/blank instead of loading AI service websites
**Files:** `src/js/webview.js`, `src/js/app.js`
**Likely Causes:**
- CSP restrictions preventing iframe loading
- Cross-origin restrictions
- Missing webview permissions in Tauri config

### 2. Service URL Loading
**Problem:** iframes not displaying external websites (claude.ai, chatgpt.com, etc.)
**Files:** `src-tauri/tauri.conf.json`
**Need to investigate:**
- Tauri allowlist permissions
- CSP policy adjustments
- Alternative webview implementation

### 3. Cross-Origin Policy
**Problem:** External AI services may block iframe embedding
**Potential Solutions:**
- Use Tauri's native webview instead of iframe
- Implement custom user agent
- Add webview-specific permissions

## Next Steps to Complete

### Immediate (High Priority)
1. **Fix Webview Loading**
   - Debug why iframe content isn't displaying
   - Check browser console for CSP/CORS errors
   - Test with a simple URL first (e.g., example.com)

2. **Update Tauri Permissions**
   - Add webview permissions to `tauri.conf.json`
   - Review and expand allowlist for external domains
   - Update CSP to allow external content

3. **Implement Native Webview**
   - Consider using Tauri's native webview API instead of iframe
   - Investigate `@tauri-apps/api/webview` for better integration

### Medium Priority
4. **Service Integration Testing**
   - Test each AI service URL individually
   - Handle service-specific requirements
   - Implement fallback for blocked services

5. **Settings Persistence**
   - Verify file system permissions work properly
   - Test settings save/load functionality
   - Handle cases where settings file doesn't exist

6. **UI Polish**
   - Ensure proper loading states
   - Add error handling for failed service loads
   - Implement retry mechanisms

### Future Enhancements
7. **Keyboard Shortcuts**
   - Test all defined shortcuts (Ctrl+1, Ctrl+2, etc.)
   - Add visual feedback for shortcuts

8. **Theme System**
   - Test dark/light mode switching
   - Ensure theme applies to webview content

9. **Additional Features**
   - Service health monitoring
   - Custom user agent strings
   - Session management

## Development Commands

```bash
# Start development server
npm run dev

# Build CSS
npm run build:css

# Watch CSS changes
npm run watch:css

# Build for production
npm run build

# Clean build artifacts
npm run clean
```

## File Structure Overview

```
src/
├── components/
│   ├── sidebar.html          # Navigation sidebar
│   └── settings.html         # Settings panel
├── js/
│   ├── app.js                # Main application logic
│   ├── settings.js           # Settings management
│   └── webview.js           # Webview/iframe handling
├── styles/
│   ├── main.css             # Tailwind input
│   └── output.css           # Generated CSS
└── index.html               # Main HTML entry point

src-tauri/
├── src/
│   ├── main.rs              # Rust backend
│   └── commands.rs          # Tauri commands
└── tauri.conf.json          # Tauri configuration
```

## Debugging Tips

1. **Check Browser Console:** Look for CSP, CORS, or loading errors
2. **Tauri Dev Tools:** Use webview inspector for debugging
3. **Network Tab:** Monitor failed requests to AI services
4. **Console Logs:** App includes extensive logging for debugging

## Known Working Features

- ✅ Application startup and window creation
- ✅ Sidebar rendering and styling
- ✅ Settings panel navigation
- ✅ CSS compilation and hot reload
- ✅ Tauri API integration with fallbacks
- ✅ Dark/light theme switching
- ✅ Keyboard shortcut definitions

The main blocker is getting the webview/iframe content to actually load and display the AI service websites.