import SettingsManager from './settings.js';
import WebviewManager from './webview.js';

class App {
    constructor() {
        this.settingsManager = new SettingsManager();
        this.webviewManager = new WebviewManager();
        this.currentView = 'webview';
        this.activeService = null;
        console.log('AI Chat Shell initializing...');
    }
    
    async initialize() {
        console.log('App initialized - Phase 3 webview core active');
        
        // Load saved settings first
        await this.settingsManager.initialize();
        
        // Get default service from settings
        const settings = this.settingsManager.getSettings();
        this.activeService = settings.defaultService || 'claude';
        
        // Build initial UI with sidebar and webview
        this.renderLayout();
        
        // Initialize webview manager
        this.initializeWebview();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    renderLayout() {
        const app = document.getElementById('app');
        
        if (this.currentView === 'webview') {
            this.renderWebviewLayout(app);
        } else if (this.currentView === 'settings') {
            this.renderSettingsLayout(app);
        }
    }
    
    async renderWebviewLayout(container) {
        // Load sidebar component
        const sidebarHTML = await this.loadComponent('sidebar');
        
        container.innerHTML = `
            <div class="h-full flex layout-transition">
                ${sidebarHTML}
                <main class="flex-1 flex flex-col">
                    <div id="webviewContainer" class="flex-1"></div>
                </main>
            </div>
        `;
        
        // Bind sidebar events
        this.bindSidebarEvents();
    }
    
    async renderSettingsLayout(container) {
        const settingsHTML = await this.loadComponent('settings');
        
        container.innerHTML = `
            <div class="h-full flex flex-col layout-transition">
                <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
                    <div class="flex items-center justify-between">
                        <h1 class="text-xl font-bold">AI Chat Shell Settings</h1>
                        <button id="backToWebview" class="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
                            Back to Chat
                        </button>
                    </div>
                </header>
                <main class="flex-1 overflow-auto custom-scrollbar">
                    ${settingsHTML}
                </main>
            </div>
        `;
        
        // Re-initialize settings bindings
        await this.settingsManager.initialize();
        
        // Bind back button
        const backBtn = document.getElementById('backToWebview');
        backBtn?.addEventListener('click', () => {
            this.showWebview();
        });
    }
    
    async loadComponent(name) {
        try {
            const response = await fetch(`./components/${name}.html`);
            if (!response.ok) throw new Error(`Component ${name} not found`);
            return await response.text();
        } catch (error) {
            console.error(`Failed to load component ${name}:`, error);
            return `<div class="p-6 text-red-500">Error loading ${name} component</div>`;
        }
    }
    
    initializeWebview() {
        if (this.currentView === 'webview') {
            const webviewContainer = document.getElementById('webviewContainer');
            if (webviewContainer) {
                // Set up service change callback
                this.webviewManager.onServiceChange = (serviceKey, service) => {
                    this.activeService = serviceKey;
                    this.updateSidebarActiveState();
                    
                    // Save to settings
                    const settings = this.settingsManager.getSettings();
                    settings.defaultService = serviceKey;
                    this.settingsManager.saveSettings(settings);
                };
                
                // Initialize with default service
                this.webviewManager.init(webviewContainer, this.activeService);
                this.updateSidebarActiveState();
            }
        }
    }
    
    bindSidebarEvents() {
        // Service selection
        const serviceItems = document.querySelectorAll('.service-item');
        serviceItems.forEach(item => {
            item.addEventListener('click', () => {
                const service = item.dataset.service;
                if (service && this.webviewManager) {
                    this.webviewManager.switchService(service);
                }
            });
        });
        
        // Settings button
        const settingsBtn = document.getElementById('sidebarSettingsBtn');
        settingsBtn?.addEventListener('click', () => {
            this.showSettings();
        });
    }
    
    updateSidebarActiveState() {
        // Remove active state from all service items
        const serviceItems = document.querySelectorAll('.service-item');
        serviceItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active state to current service
        const activeItem = document.querySelector(`[data-service="${this.activeService}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Check if Ctrl (or Cmd on Mac) is pressed
            const modifier = event.ctrlKey || event.metaKey;
            
            if (modifier && this.currentView === 'webview') {
                let actionTaken = false;
                let actionMessage = '';
                
                switch (event.key) {
                    case '1':
                        event.preventDefault();
                        this.webviewManager.switchService('claude');
                        actionTaken = true;
                        actionMessage = 'Switched to Claude';
                        break;
                    case '2':
                        event.preventDefault();
                        this.webviewManager.switchService('chatgpt');
                        actionTaken = true;
                        actionMessage = 'Switched to ChatGPT';
                        break;
                    case '3':
                        event.preventDefault();
                        this.webviewManager.switchService('gemini');
                        actionTaken = true;
                        actionMessage = 'Switched to Gemini';
                        break;
                    case '4':
                        event.preventDefault();
                        this.webviewManager.switchService('perplexity');
                        actionTaken = true;
                        actionMessage = 'Switched to Perplexity';
                        break;
                    case ',':
                        event.preventDefault();
                        this.showSettings();
                        actionTaken = true;
                        actionMessage = 'Opened Settings';
                        break;
                    case 'r':
                        event.preventDefault();
                        this.webviewManager.refresh();
                        actionTaken = true;
                        actionMessage = 'Refreshed Current Service';
                        break;
                    case 't':
                        event.preventDefault();
                        this.toggleTheme();
                        actionTaken = true;
                        actionMessage = 'Toggled Theme';
                        break;
                }
                
                // Show visual feedback for keyboard actions
                if (actionTaken) {
                    this.showKeyboardFeedback(actionMessage);
                }
            }
            
            // Escape key to go back to webview from settings
            if (event.key === 'Escape' && this.currentView === 'settings') {
                event.preventDefault();
                this.showWebview();
                this.showKeyboardFeedback('Returned to Chat');
            }
        });
    }
    
    showKeyboardFeedback(message) {
        // Create or get existing feedback element
        let feedback = document.getElementById('keyboardFeedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.id = 'keyboardFeedback';
            feedback.className = 'fixed top-4 right-4 bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300 z-50';
            document.body.appendChild(feedback);
        }
        
        feedback.textContent = message;
        feedback.classList.remove('translate-x-full');
        
        // Hide after 2 seconds
        setTimeout(() => {
            feedback.classList.add('translate-x-full');
        }, 2000);
    }
    
    async toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        await this.settingsManager.updateTheme(!isDark);
    }
    
    showWebview() {
        this.currentView = 'webview';
        this.renderLayout();
        this.initializeWebview();
    }
    
    showSettings() {
        this.currentView = 'settings';
        this.renderLayout();
    }
    
    // Public API methods
    getCurrentService() {
        return this.activeService;
    }
    
    switchService(serviceKey) {
        if (this.webviewManager && this.currentView === 'webview') {
            this.webviewManager.switchService(serviceKey);
        }
    }
    
    refreshCurrentService() {
        if (this.webviewManager && this.currentView === 'webview') {
            this.webviewManager.refresh();
        }
    }
    
    getAvailableServices() {
        return this.webviewManager.getAllServices();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const app = new App();
    await app.initialize();
    
    // Make app instance globally available for debugging
    window.aiChatShell = app;
});