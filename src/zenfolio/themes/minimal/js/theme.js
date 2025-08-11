/**
 * Minimal Theme JavaScript
 * Enhanced copy functionality and smooth reveal animations
 */

// Enhanced copy functionality with better UX
function copyBibtex(button) {
    const bibtex = button.getAttribute('data-bibtex');
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(bibtex).then(() => {
            showCopyFeedback(button, 'Copied!');
        }).catch(() => {
            fallbackCopyTextToClipboard(bibtex, button);
        });
    } else {
        fallbackCopyTextToClipboard(bibtex, button);
    }
}

function fallbackCopyTextToClipboard(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopyFeedback(button, 'Copied!');
    } catch (err) {
        showCopyFeedback(button, 'Failed to copy');
    }
    
    document.body.removeChild(textArea);
}

function showCopyFeedback(button, message) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i> ' + message;
    button.classList.add('copied');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('copied');
    }, 2000);
}

// Safari-compatible reveal animations with multiple fallbacks
function initRevealSystem() {
    function revealElement(el) {
        const rect = el.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        // Reveal if element is in viewport or close to it (within 200px)
        if (rect.top < windowHeight + 200) {
            el.classList.add('revealed');
        }
    }
    
    // Get all reveal elements
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    
    // Safari fallback: If no elements found, try again after a short delay
    if (revealElements.length === 0) {
        setTimeout(() => {
            const retryElements = document.querySelectorAll('.reveal-on-scroll');
            retryElements.forEach(el => el.classList.add('revealed'));
        }, 100);
        return;
    }
    
    // Initial check for elements already in viewport
    revealElements.forEach(revealElement);
    
    // Multiple safety nets for Safari
    setTimeout(() => {
        document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(el => el.classList.add('revealed'));
    }, 500);
    
    setTimeout(() => {
        document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(el => el.classList.add('revealed'));
    }, 1500);
    
    // IntersectionObserver with Safari-compatible options
    if ('IntersectionObserver' in window) {
        try {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => { 
                    if (entry.isIntersecting) entry.target.classList.add('revealed'); 
                });
            }, { threshold: 0.05, rootMargin: '100px' });
            revealElements.forEach(el => observer.observe(el));
        } catch (e) {
            // Fallback if IntersectionObserver fails in Safari
            revealElements.forEach(el => el.classList.add('revealed'));
        }
    } else {
        // No IntersectionObserver support - reveal all
        revealElements.forEach(el => el.classList.add('revealed'));
    }
}

// Multiple initialization methods for maximum Safari compatibility
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRevealSystem);
} else {
    initRevealSystem();
}

// Additional safeguard
window.addEventListener('load', function() {
    setTimeout(() => {
        document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(el => el.classList.add('revealed'));
    }, 100);
});

// Search functionality for publications page
if (document.title.includes('Publications')) {
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('search-input');
        if (!searchInput) return;
        
        // Get all publication items once
        const allPublications = document.querySelectorAll('.publication-card');
        
        // Simple search function
        function filterPublications(searchTerm) {
            const searchLower = searchTerm.toLowerCase().trim();
            
            allPublications.forEach(item => {
                const searchText = item.textContent.toLowerCase();
                const parentGroup = item.closest('.group-section');
                
                if (!searchTerm || searchText.includes(searchLower)) {
                    // Show item and its parent group
                    item.style.display = '';
                    if (parentGroup) parentGroup.style.display = '';
                } else {
                    // Hide item
                    item.style.display = 'none';
                }
            });
            
            // Hide empty year groups
            document.querySelectorAll('.group-section').forEach(group => {
                const visibleItems = group.querySelectorAll('.publication-card:not([style*="display: none"])');
                group.style.display = visibleItems.length > 0 ? '' : 'none';
            });
        }
        
        // Set up search input listener
        searchInput.addEventListener('input', function(e) {
            filterPublications(e.target.value);
        });
        
        // Clear search on escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                filterPublications('');
                this.blur();
            }
        });
    });
}