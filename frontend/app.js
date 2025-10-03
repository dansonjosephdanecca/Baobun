// Global variables
let ws = null;
let currentConversationId = null;
let isConnected = false;

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatForm = document.getElementById('chatForm');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const searchResults = document.getElementById('searchResults');
const searchResultsList = document.getElementById('searchResultsList');
const conversationsList = document.getElementById('conversationsList');
const newChatBtn = document.getElementById('newChatBtn');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const setupModelBtn = document.getElementById('setupModelBtn');
const statusIndicator = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');
const ollamaStatus = document.getElementById('ollamaStatus');
const enableSearch = document.getElementById('enableSearch');
const themeSelect = document.getElementById('themeSelect');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Load theme
    loadTheme();

    // Check Ollama connection
    await checkOllamaStatus();

    // Load conversations
    await loadConversations();

    // Create or load conversation
    if (!currentConversationId) {
        await createNewConversation();
    }

    // Setup event listeners
    setupEventListeners();

    // Setup WebSocket
    connectWebSocket();
}

function setupEventListeners() {
    // Chat form
    chatForm.addEventListener('submit', handleSendMessage);

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = chatInput.scrollHeight + 'px';
        sendBtn.disabled = !chatInput.value.trim();
    });

    // Enter key to send (Shift+Enter for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (chatInput.value.trim()) {
                handleSendMessage(e);
            }
        }
    });

    // New chat button
    newChatBtn.addEventListener('click', createNewConversation);

    // Settings
    settingsBtn.addEventListener('click', () => {
        settingsModal.style.display = 'flex';
    });

    closeSettings.addEventListener('click', () => {
        settingsModal.style.display = 'none';
    });

    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    // Setup model button
    setupModelBtn.addEventListener('click', setupModel);

    // Theme selector
    themeSelect.addEventListener('change', (e) => {
        setTheme(e.target.value);
    });
}

function connectWebSocket() {
    if (!currentConversationId) return;

    const wsUrl = `ws://${window.location.host}/ws/${currentConversationId}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        isConnected = true;
        updateConnectionStatus(true);
        sendBtn.disabled = !chatInput.value.trim();
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        isConnected = false;
        updateConnectionStatus(false);
        sendBtn.disabled = true;

        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (currentConversationId) {
                connectWebSocket();
            }
        }, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'history':
            displayConversationHistory(data.messages);
            break;

        case 'status':
            showStatus(data.message);
            break;

        case 'search_results':
            displaySearchResults(data.results);
            break;

        case 'response_start':
            showTypingIndicator(false);
            addAssistantMessage('');
            break;

        case 'response_chunk':
            appendToLastMessage(data.content);
            break;

        case 'response_end':
            hideTypingIndicator();
            scrollToBottom();
            break;

        case 'pong':
            // Keep-alive response
            break;
    }
}

async function handleSendMessage(e) {
    e.preventDefault();

    const message = chatInput.value.trim();
    if (!message || !isConnected) return;

    // Add user message to UI
    addUserMessage(message);

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Show typing indicator
    showTypingIndicator(true);

    // Send message via WebSocket
    ws.send(JSON.stringify({
        type: 'chat',
        message: message,
        enable_search: enableSearch.checked
    }));

    scrollToBottom();
}

function addUserMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-avatar">U</div>
        <div class="message-content">
            <div class="message-text">${escapeHtml(content)}</div>
            <div class="message-time">${formatTime(new Date())}</div>
        </div>
    `;

    // Clear welcome message if present
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    chatMessages.appendChild(messageDiv);
}

function addAssistantMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <img src="/static/assets/bao-icon.svg" alt="Bao" class="message-avatar">
        <div class="message-content">
            <div class="message-text">${content}</div>
            <div class="message-time">${formatTime(new Date())}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
}

function appendToLastMessage(content) {
    const messages = chatMessages.querySelectorAll('.message.assistant');
    if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        const textElement = lastMessage.querySelector('.message-text');
        textElement.textContent += content;
        scrollToBottom();
    }
}

function displayConversationHistory(messages) {
    // Clear existing messages except welcome
    chatMessages.innerHTML = '';

    if (messages.length === 0) {
        // Show welcome message for new conversation
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <img src="/static/assets/bao-icon.svg" alt="Bao" class="welcome-avatar">
                <h3>Welcome! I'm Bao 🥟</h3>
                <p>I'm your friendly AI assistant, ready to help with anything you need. I can search the web, answer questions, and have conversations!</p>
                <p class="welcome-tips">Try asking me about current events, general knowledge, or just chat!</p>
            </div>
        `;
    } else {
        messages.forEach(msg => {
            if (msg.role === 'user') {
                addUserMessage(msg.content);
            } else if (msg.role === 'assistant') {
                addAssistantMessage(msg.content);
            }
        });
    }

    scrollToBottom();
}

function displaySearchResults(results) {
    if (!results || results.length === 0) {
        searchResults.style.display = 'none';
        return;
    }

    searchResultsList.innerHTML = results.map(result => `
        <div class="search-result-item">
            <div class="search-result-title">${escapeHtml(result.title)}</div>
            <div class="search-result-snippet">${escapeHtml(result.snippet)}</div>
            <div class="search-result-url">${escapeHtml(result.url)}</div>
        </div>
    `).join('');

    searchResults.style.display = 'block';

    // Hide search results after 10 seconds
    setTimeout(() => {
        searchResults.style.display = 'none';
    }, 10000);
}

function showTypingIndicator(show) {
    typingIndicator.style.display = show ? 'flex' : 'none';
    if (show) scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

function showStatus(message) {
    // Could show a temporary status message
    console.log('Status:', message);
}

async function loadConversations() {
    try {
        const response = await fetch('/conversations');
        const conversations = await response.json();

        conversationsList.innerHTML = conversations.map(conv => `
            <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}"
                 data-id="${conv.id}"
                 onclick="loadConversation('${conv.id}')">
                <div class="conversation-title">Chat ${new Date(conv.created_at).toLocaleDateString()}</div>
                <div class="conversation-preview">${escapeHtml(conv.last_message || 'New conversation')}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

async function createNewConversation() {
    try {
        const response = await fetch('/conversations', { method: 'POST' });
        const data = await response.json();
        currentConversationId = data.conversation_id;

        // Close existing WebSocket
        if (ws) {
            ws.close();
        }

        // Connect to new conversation
        connectWebSocket();

        // Reload conversations list
        await loadConversations();

        // Clear chat
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <img src="/static/assets/bao-icon.svg" alt="Bao" class="welcome-avatar">
                <h3>Welcome! I'm Bao 🥟</h3>
                <p>I'm your friendly AI assistant, ready to help with anything you need. I can search the web, answer questions, and have conversations!</p>
                <p class="welcome-tips">Try asking me about current events, general knowledge, or just chat!</p>
            </div>
        `;
    } catch (error) {
        console.error('Error creating conversation:', error);
    }
}

async function loadConversation(conversationId) {
    currentConversationId = conversationId;

    // Close existing WebSocket
    if (ws) {
        ws.close();
    }

    // Connect to conversation
    connectWebSocket();

    // Update UI
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === conversationId);
    });
}

async function checkOllamaStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        if (data.ollama_connected) {
            updateConnectionStatus(true);
            ollamaStatus.textContent = 'Connected';
            ollamaStatus.className = 'status-badge connected';
        } else {
            updateConnectionStatus(false);
            ollamaStatus.textContent = 'Disconnected';
            ollamaStatus.className = 'status-badge disconnected';
        }
    } catch (error) {
        updateConnectionStatus(false);
        ollamaStatus.textContent = 'Error';
        ollamaStatus.className = 'status-badge disconnected';
    }
}

async function setupModel() {
    setupModelBtn.disabled = true;
    setupModelBtn.textContent = 'Setting up...';

    try {
        const response = await fetch('/setup/model', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'available' || data.status === 'pulled') {
            alert('Model is ready!');
            await checkOllamaStatus();
        } else {
            alert('Failed to setup model. Please check Ollama installation.');
        }
    } catch (error) {
        alert('Error setting up model: ' + error.message);
    } finally {
        setupModelBtn.disabled = false;
        setupModelBtn.textContent = 'Setup Model';
    }
}

function updateConnectionStatus(connected) {
    if (connected) {
        statusIndicator.className = 'status-dot connected';
        statusText.textContent = 'Connected';
    } else {
        statusIndicator.className = 'status-dot error';
        statusText.textContent = 'Disconnected';
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function loadTheme() {
    const savedTheme = localStorage.getItem('bao-theme') || 'light';
    themeSelect.value = savedTheme;
    setTheme(savedTheme);
}

function setTheme(theme) {
    document.body.className = theme === 'dark' ? 'dark-theme' : '';
    localStorage.setItem('bao-theme', theme);
}

// Keep connection alive with periodic pings
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);