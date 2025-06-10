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
        await this.applyThemeToWebviews(isDark);
        await this.save();
    }
    
    async applyThemeToWebviews(isDark) {
        const webviews = document.querySelectorAll('webview');
        
        webviews.forEach(webview => {
            try {
                // Attempt to inject CSS into webview (cross-origin safe)
                const css = isDark ?
                    `
                    * { filter: invert(1) hue-rotate(180deg) !important; }
                    img, video, iframe, svg, embed, object { filter: invert(1) hue-rotate(180deg) !important; }
                    [style*="background-image"] { filter: invert(1) hue-rotate(180deg) !important; }
                    ` :
                    `
                    * { filter: none !important; }
                    `;
                
                // Try to inject CSS if same-origin or permissions allow
                webview.insertCSS(css).catch(() => {
                    // Silently fail for cross-origin webviews
                    console.log('Could not apply theme to cross-origin webview');
                });
            } catch (error) {
                // Cross-origin restrictions prevent theme injection
                console.log('Theme injection blocked by cross-origin policy');
            }
        });
    }
    
    async updateDefaultService(service) {
        this.settings.defaultService = service;
        await this.save();
    }
    
    getSettings() {
        return { ...this.settings };
    }
    
    async saveSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        return await this.save();
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
        
        // Update toggle visual state based on current theme
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            const span = darkModeToggle.querySelector('span');
            const isDark = settings.theme === 'dark';
            span.classList.toggle('translate-x-1', !isDark);
            span.classList.toggle('translate-x-6', isDark);
        }
        
        this.bindEvents();
    }
}

export default SettingsManager;