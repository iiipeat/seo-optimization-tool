/**
 * SEO Tools - Main JavaScript Functions
 * Common utilities and shared functionality
 */

// Global utility functions
const SEOTools = {
    // API wrapper with error handling
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return { success: true, data };
        } catch (error) {
            console.error('API call failed:', error);
            return { success: false, error: error.message };
        }
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const toastContainer = this.getOrCreateToastContainer();
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${this.getToastIcon(type)} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove from DOM after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    },

    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format numbers with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    // Validate URL format
    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            try {
                new URL('https://' + string);
                return true;
            } catch (_) {
                return false;
            }
        }
    },

    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    },

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard!', 'success');
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                this.showToast('Copied to clipboard!', 'success');
                return true;
            } catch (err) {
                this.showToast('Failed to copy to clipboard', 'danger');
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    },

    // Export data as CSV
    exportToCSV(data, filename) {
        if (!data || data.length === 0) {
            this.showToast('No data to export', 'warning');
            return;
        }

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    // Escape quotes and wrap in quotes if contains comma or quote
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                }).join(',')
            )
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            this.showToast('File exported successfully!', 'success');
        } else {
            this.showToast('Export not supported in this browser', 'danger');
        }
    },

    // Show loading state on element
    showLoading(element, text = 'Loading...') {
        if (!element) return;
        
        element.dataset.originalContent = element.innerHTML;
        element.disabled = true;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
            ${text}
        `;
    },

    // Hide loading state on element
    hideLoading(element) {
        if (!element || !element.dataset.originalContent) return;
        
        element.disabled = false;
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    },

    // Animate number counting
    animateNumber(element, start, end, duration = 1000) {
        if (!element) return;
        
        const startTime = performance.now();
        const difference = end - start;
        
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (difference * easeOut));
            
            // Format number with commas
            element.textContent = this.formatNumber(current);
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        
        requestAnimationFrame(step);
    },

    // Get SEO score color class
    getScoreColorClass(score) {
        if (score >= 90) return 'text-success';
        if (score >= 70) return 'text-primary';
        if (score >= 50) return 'text-warning';
        return 'text-danger';
    },

    // Format date relative to now
    formatRelativeTime(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - new Date(date)) / 1000);
        
        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
        
        return new Date(date).toLocaleDateString();
    },

    // Initialize tooltips
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    },

    // Initialize popovers
    initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    },

    // Initialize animated counters
    initCounters() {
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.dataset.count);
                    const duration = 2000; // 2 seconds
                    
                    this.animateNumber(counter, 0, target, duration);
                    observer.unobserve(counter);
                }
            });
        }, observerOptions);

        // Observe all stat numbers
        document.querySelectorAll('.stat-number[data-count]').forEach(counter => {
            observer.observe(counter);
        });
    },

    // Smooth scroll to element
    scrollToElement(elementId, offset = 20) {
        const element = document.getElementById(elementId);
        if (element) {
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - offset;
            
            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    },

    // Track analytics event (placeholder for Google Analytics)
    trackEvent(action, category = 'SEO Tools', label = '') {
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                event_category: category,
                event_label: label
            });
        }
    },

    // Local storage helpers
    storage: {
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Failed to save to localStorage:', e);
                return false;
            }
        },

        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.error('Failed to read from localStorage:', e);
                return defaultValue;
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('Failed to remove from localStorage:', e);
                return false;
            }
        }
    }
};

// Initialize common functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    SEOTools.initTooltips();
    SEOTools.initPopovers();
    
    // Initialize animated counters
    SEOTools.initCounters();
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            SEOTools.scrollToElement(targetId);
        });
    });
    
    // Add loading states to form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                SEOTools.showLoading(submitBtn, 'Processing...');
            }
        });
    });
    
    // Auto-resize textareas
    document.querySelectorAll('textarea[data-auto-resize]').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Add copy buttons to code blocks
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
        button.innerHTML = '<i class="bi bi-clipboard"></i>';
        button.title = 'Copy code';
        
        const container = document.createElement('div');
        container.className = 'position-relative';
        block.parentNode.insertBefore(container, block);
        container.appendChild(block);
        container.appendChild(button);
        
        button.addEventListener('click', () => {
            SEOTools.copyToClipboard(block.textContent);
        });
    });
    
    // Fade in animations for cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });
});

// Handle network errors globally
window.addEventListener('online', () => {
    SEOTools.showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    SEOTools.showToast('Connection lost - some features may not work', 'warning');
});

// Export for use in other scripts
window.SEOTools = SEOTools;