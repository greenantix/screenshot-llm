class WebviewManager {
    constructor() {
        this.services = {
            claude: { 
                name: 'Claude', 
                url: 'https://claude.ai/chats',
                color: 'orange',
                status: 'unknown'
            },
            chatgpt: { 
                name: 'ChatGPT', 
                url: 'https://chatgpt.com/',
                color: 'green',
                status: 'unknown'
            },
            gemini: { 
                name: 'Gemini', 
                url: 'https://gemini.google.com/',
                color: 'blue',
                status: 'unknown'
            },
            perplexity: {
                name: 'Perplexity',
                url: 'https://www.perplexity.ai/',
                color: 'purple',
                status: 'unknown'
            }
        };
        
        this.currentService = null;
        this.onServiceChange = null;
        this.onStatusChange = null;
        this.retryCount = 0;
        this.maxRetries = 3;
    }
    
    async checkServiceHealth(serviceKey) {
        const service = this.services[serviceKey];
        if (!service) return false;
        
        try {
            // Simple fetch with timeout to check if service is reachable
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(service.url, {
                method: 'HEAD',
                signal: controller.signal,
                mode: 'no-cors' // Avoid CORS issues
            });
            
            clearTimeout(timeoutId);
            service.status = 'online';
            return true;
        } catch (error) {
            console.warn(`Service ${serviceKey} health check failed:`, error);
            service.status = 'offline';
            return false;
        }
    }
    
    async checkAllServices() {
        const healthChecks = Object.keys(this.services).map(async (serviceKey) => {
            const isHealthy = await this.checkServiceHealth(serviceKey);
            return { serviceKey, isHealthy };
        });
        
        const results = await Promise.all(healthChecks);
        
        if (this.onStatusChange) {
            this.onStatusChange(results);
        }
        
        return results;
    }
    
    init(container, defaultService = 'claude') {
        this.container = container;
        this.createWebviewContainer();
        this.switchService(defaultService);
    }
    
    createWebviewContainer() {
        this.container.innerHTML = `
            <div class="webview-container h-full relative">
                <!-- Loading overlay -->
                <div id="loadingOverlay" class="absolute inset-0 bg-white dark:bg-gray-900 flex items-center justify-center z-10 hidden">
                    <div class="text-center">
                        <div class="animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent mb-4 mx-auto"></div>
                        <p class="text-gray-600 dark:text-gray-400">Loading <span id="loadingServiceName">AI Service</span>...</p>
                        <div id="retryIndicator" class="mt-2 text-sm text-gray-500 dark:text-gray-500 hidden">
                            Retrying... (<span id="retryCount">0</span>/<span id="maxRetries">3</span>)
                        </div>
                    </div>
                </div>
                
                <!-- Webview iframe -->
                <iframe 
                    id="webviewFrame"
                    class="w-full h-full border-0 bg-white dark:bg-gray-900"
                    allow="clipboard-read; clipboard-write; microphone; camera"
                    sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"
                    loading="eager"
                ></iframe>
                
                <!-- Error state -->
                <div id="errorState" class="absolute inset-0 bg-white dark:bg-gray-900 flex items-center justify-center z-10 hidden">
                    <div class="text-center max-w-md px-4">
                        <div class="text-red-500 mb-4">
                            <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                            </svg>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Service Unavailable</h3>
                        <p class="text-gray-600 dark:text-gray-400 mb-4">Unable to load the selected AI service. Please check your internet connection.</p>
                        <div class="space-y-2">
                            <button id="retryBtn" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                                Try Again
                            </button>
                            <button id="healthCheckBtn" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors ml-2">
                                Check All Services
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Connection status indicator -->
                <div id="statusIndicator" class="absolute top-4 right-4 z-20 hidden">
                    <div class="flex items-center space-x-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg px-3 py-2 border border-gray-200 dark:border-gray-700">
                        <div id="statusDot" class="w-2 h-2 rounded-full bg-gray-400"></div>
                        <span id="statusText" class="text-sm text-gray-600 dark:text-gray-400">Connecting...</span>
                    </div>
                </div>
            </div>
        `;
        
        // Bind event handlers
        document.getElementById('retryBtn')?.addEventListener('click', () => {
            if (this.currentService) {
                this.switchService(this.currentService);
            }
        });
        
        document.getElementById('healthCheckBtn')?.addEventListener('click', () => {
            this.checkAllServices();
        });
    }
    
    switchService(serviceKey) {
        const service = this.services[serviceKey];
        if (!service) {
            console.error(`Service ${serviceKey} not found`);
            return;
        }
        
        this.currentService = serviceKey;
        this.retryCount = 0;
        this.loadService(serviceKey);
    }
    
    loadService(serviceKey, isRetry = false) {
        const service = this.services[serviceKey];
        this.showLoading(service.name);
        this.updateStatusIndicator('connecting', 'Connecting...');
        
        const iframe = document.getElementById('webviewFrame');
        const loadingOverlay = document.getElementById('loadingOverlay');
        const errorState = document.getElementById('errorState');
        
        // Hide error state
        errorState.classList.add('hidden');
        
        // Update retry indicator if this is a retry
        if (isRetry) {
            const retryIndicator = document.getElementById('retryIndicator');
            const retryCountEl = document.getElementById('retryCount');
            retryIndicator.classList.remove('hidden');
            retryCountEl.textContent = this.retryCount;
        }
        
        // Set up load event handlers
        const onLoad = () => {
            this.retryCount = 0;
            service.status = 'online';
            this.updateStatusIndicator('online', 'Connected');
            
            setTimeout(() => {
                this.hideLoading();
                this.hideStatusIndicator();
            }, 1000); // Show success for 1 second
            
            iframe.removeEventListener('load', onLoad);
            iframe.removeEventListener('error', onError);
            
            if (this.onStatusChange) {
                this.onStatusChange([{ serviceKey, isHealthy: true }]);
            }
        };
        
        const onError = () => {
            service.status = 'offline';
            this.hideLoading();
            this.updateStatusIndicator('error', 'Connection failed');
            
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying ${service.name} (attempt ${this.retryCount}/${this.maxRetries})`);
                setTimeout(() => {
                    this.loadService(serviceKey, true);
                }, 2000); // Wait 2 seconds before retry
            } else {
                this.showError();
                this.hideStatusIndicator();
                if (this.onStatusChange) {
                    this.onStatusChange([{ serviceKey, isHealthy: false }]);
                }
            }
            
            iframe.removeEventListener('load', onLoad);
            iframe.removeEventListener('error', onError);
        };
        
        iframe.addEventListener('load', onLoad);
        iframe.addEventListener('error', onError);
        
        // Set timeout for loading
        setTimeout(() => {
            if (!loadingOverlay.classList.contains('hidden')) {
                onError();
            }
        }, 15000); // 15 second timeout
        
        // Load the service
        iframe.src = service.url;
        
        // Notify service change (only on first load, not retries)
        if (!isRetry && this.onServiceChange) {
            this.onServiceChange(serviceKey, service);
        }
        
        console.log(`${isRetry ? 'Retrying' : 'Switching to'} ${service.name}: ${service.url}`);
    }
    
    showLoading(serviceName) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingServiceName = document.getElementById('loadingServiceName');
        const retryIndicator = document.getElementById('retryIndicator');
        
        if (loadingServiceName) {
            loadingServiceName.textContent = serviceName;
        }
        
        // Hide retry indicator for new loads
        retryIndicator.classList.add('hidden');
        loadingOverlay.classList.remove('hidden');
    }
    
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.add('hidden');
    }
    
    showError() {
        const errorState = document.getElementById('errorState');
        errorState.classList.remove('hidden');
    }
    
    updateStatusIndicator(status, message) {
        const indicator = document.getElementById('statusIndicator');
        const dot = document.getElementById('statusDot');
        const text = document.getElementById('statusText');
        
        indicator.classList.remove('hidden');
        text.textContent = message;
        
        // Update dot color based on status
        dot.className = 'w-2 h-2 rounded-full';
        switch (status) {
            case 'online':
                dot.classList.add('bg-green-500');
                break;
            case 'connecting':
                dot.classList.add('bg-yellow-500', 'animate-pulse');
                break;
            case 'error':
                dot.classList.add('bg-red-500');
                break;
            default:
                dot.classList.add('bg-gray-400');
        }
    }
    
    hideStatusIndicator() {
        const indicator = document.getElementById('statusIndicator');
        setTimeout(() => {
            indicator.classList.add('hidden');
        }, 3000); // Hide after 3 seconds
    }
    
    getCurrentService() {
        return this.currentService;
    }
    
    getServiceInfo(serviceKey) {
        return this.services[serviceKey];
    }
    
    getAllServices() {
        return this.services;
    }
    
    // Refresh current service
    refresh() {
        if (this.currentService) {
            this.switchService(this.currentService);
        }
    }
    
    // Navigate back in the current service
    goBack() {
        const iframe = document.getElementById('webviewFrame');
        try {
            iframe.contentWindow.history.back();
        } catch (error) {
            console.warn('Cannot navigate back due to security restrictions');
        }
    }
    
    // Navigate forward in the current service
    goForward() {
        const iframe = document.getElementById('webviewFrame');
        try {
            iframe.contentWindow.history.forward();
        } catch (error) {
            console.warn('Cannot navigate forward due to security restrictions');
        }
    }
}

export default WebviewManager;