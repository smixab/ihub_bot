// Global state
let isLoading = false;
let currentConversation = [];

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');
const categoriesList = document.getElementById('categories-list');
const loadingOverlay = document.getElementById('loading-overlay');
const toolModal = document.getElementById('tool-modal');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadCategories();
    focusInput();
});

// Event listeners
function setupEventListeners() {
    // Chat input events
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Search input events
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });

    // Auto-search as user types (debounced)
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            if (searchInput.value.trim().length > 2) {
                performSearch();
            } else {
                clearSearchResults();
            }
        }, 300);
    });

    // Modal close events
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });

    // Click outside modal to close
    toolModal.addEventListener('click', function(e) {
        if (e.target === toolModal) {
            closeModal();
        }
    });
}

// Chat functions
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isLoading) return;

    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    setLoading(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        if (response.ok) {
            // Add bot response
            addMessage(data.response, 'bot', data.relevant_tools);
            
            // Store conversation
            currentConversation.push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.response, tools: data.relevant_tools }
            );
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'bot');
    } finally {
        setLoading(false);
        focusInput();
    }
}

function sendQuickMessage(message) {
    messageInput.value = message;
    sendMessage();
}

function addMessage(content, sender, tools = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    // Format message content
    let formattedContent = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedContent = formattedContent.replace(/\n/g, '<br>');
    textDiv.innerHTML = formattedContent;

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = formatTime(new Date());

    contentDiv.appendChild(textDiv);
    
    // Add tool cards if provided
    if (tools && tools.length > 0) {
        tools.forEach(tool => {
            const toolCard = createToolCard(tool);
            contentDiv.appendChild(toolCard);
        });
    }
    
    contentDiv.appendChild(timeDiv);

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createToolCard(tool) {
    const card = document.createElement('div');
    card.className = 'tool-card';
    card.onclick = () => showToolDetails(tool);

    card.innerHTML = `
        <div class="tool-card-header">
            <div class="tool-card-title">${tool.name}</div>
            <div class="tool-card-category">${tool.category}</div>
        </div>
        <div class="tool-card-location">
            <i class="fas fa-map-marker-alt"></i>
            ${tool.location}
        </div>
        <div class="tool-card-description">${tool.description}</div>
    `;

    return card;
}

// Search functions
async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        clearSearchResults();
        return;
    }

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query, limit: 5 })
        });

        const data = await response.json();

        if (response.ok) {
            displaySearchResults(data.results);
        } else {
            console.error('Search error:', data.error);
        }
    } catch (error) {
        console.error('Search error:', error);
    }
}

function displaySearchResults(results) {
    searchResults.innerHTML = '';

    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result">No results found. Try different keywords.</div>';
        return;
    }

    results.forEach(result => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'search-result';
        resultDiv.onclick = () => showToolDetails(result);

        resultDiv.innerHTML = `
            <div class="search-result-title">${result.name}</div>
            <div class="search-result-category">${result.category}</div>
            <div class="search-result-description">${result.description}</div>
        `;

        searchResults.appendChild(resultDiv);
    });
}

function clearSearchResults() {
    searchResults.innerHTML = '';
}

// Categories functions
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();

        if (response.ok) {
            displayCategories(data.categories);
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function displayCategories(categories) {
    categoriesList.innerHTML = '';

    categories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category-item';
        categoryDiv.textContent = category;
        categoryDiv.onclick = () => filterByCategory(category);

        categoriesList.appendChild(categoryDiv);
    });
}

function filterByCategory(category) {
    searchInput.value = category;
    performSearch();
}

// Modal functions
function showToolDetails(tool) {
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modalTitle.textContent = tool.name;

    modalBody.innerHTML = `
        <div class="mb-4">
            <span class="tool-card-category" style="display: inline-block; margin-bottom: 1rem;">${tool.category}</span>
        </div>
        
        <div class="mb-4">
            <strong><i class="fas fa-map-marker-alt"></i> Location</strong>
            <div style="margin-top: 0.5rem; color: var(--text-secondary);">${tool.location}</div>
        </div>

        <div class="mb-4">
            <strong><i class="fas fa-info-circle"></i> Description</strong>
            <div style="margin-top: 0.5rem; color: var(--text-secondary); line-height: 1.6;">${tool.description}</div>
        </div>

        <div class="mb-4">
            <strong><i class="fas fa-clock"></i> Availability</strong>
            <div style="margin-top: 0.5rem; color: var(--text-secondary);">${tool.availability}</div>
        </div>

        <div class="mb-4">
            <strong><i class="fas fa-graduation-cap"></i> Training Required</strong>
            <div style="margin-top: 0.5rem;">
                <span style="padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; ${tool.training_required ? 'background-color: var(--warning-color); color: white;' : 'background-color: var(--success-color); color: white;'}">
                    ${tool.training_required ? 'Yes - Training Required' : 'No Training Required'}
                </span>
            </div>
        </div>

        <div class="mb-4">
            <strong><i class="fas fa-phone"></i> Contact</strong>
            <div style="margin-top: 0.5rem; color: var(--text-secondary);">${tool.contact}</div>
        </div>

        <div style="margin-top: 2rem; padding: 1rem; background-color: var(--background-color); border-radius: var(--radius-md);">
            <strong>💡 Tip:</strong> 
            <span style="color: var(--text-secondary);">
                You can ask me for more specific information about this tool or related workflows!
            </span>
        </div>
    `;

    toolModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    toolModal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Utility functions
function setLoading(loading) {
    isLoading = loading;
    sendButton.disabled = loading;
    
    if (loading) {
        loadingOverlay.classList.remove('hidden');
    } else {
        loadingOverlay.classList.add('hidden');
    }
}

function focusInput() {
    setTimeout(() => {
        messageInput.focus();
    }, 100);
}

function formatTime(date) {
    return date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
}

// Scroll to bottom helper
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto-resize chat input
function autoResizeInput() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Add some helpful animations
function animateMessage(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        element.style.transition = 'all 0.3s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 50);
}

// Enhanced error handling
window.addEventListener('error', function(e) {
    console.error('Application error:', e.error);
});

// Service worker registration for offline capability (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Uncomment if you want to add a service worker
        // navigator.serviceWorker.register('/sw.js');
    });
}

// Export functions for testing or external use
window.chatApp = {
    sendMessage,
    sendQuickMessage,
    performSearch,
    showToolDetails,
    closeModal
};