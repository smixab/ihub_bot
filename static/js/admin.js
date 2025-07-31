// Admin Dashboard JavaScript
let currentStats = {};
let currentActivity = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadConfiguration();
});

// Load dashboard statistics and activity
async function loadDashboardData() {
    try {
        const response = await fetch('/api/admin/stats');
        const data = await response.json();
        
        if (response.ok) {
            currentStats = data.stats;
            currentActivity = data.recent_activity;
            
            updateStatCards();
            displayActivity();
        } else {
            showError('Failed to load dashboard data: ' + data.error);
        }
    } catch (error) {
        showError('Error loading dashboard: ' + error.message);
    }
}

// Update statistic cards
function updateStatCards() {
    document.getElementById('total-users').textContent = currentStats.total_users || 0;
    document.getElementById('total-messages').textContent = currentStats.total_messages || 0;
    document.getElementById('flagged-messages').textContent = currentStats.flagged_messages || 0;
    document.getElementById('blocked-users').textContent = currentStats.blocked_users || 0;
}

// Display recent activity
function displayActivity() {
    const activityContent = document.getElementById('activity-content');
    
    if (currentActivity.length === 0) {
        activityContent.innerHTML = '<div class="loading">No recent activity found.</div>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'activity-table';
    
    table.innerHTML = `
        <thead>
            <tr>
                <th>Time</th>
                <th>IP Address</th>
                <th>Message</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${currentActivity.map(activity => `
                <tr>
                    <td>${formatDateTime(activity.timestamp)}</td>
                    <td><code>${activity.ip_address}</code></td>
                    <td><span title="${activity.message}">${activity.message}</span></td>
                    <td>
                        ${activity.is_flagged 
                            ? '<span class="flag-badge">Flagged</span>' 
                            : '<span class="normal-badge">Normal</span>'}
                    </td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewUserDetails('${activity.ip_address}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-danger" onclick="quickBlockUser('${activity.ip_address}')">
                            <i class="fas fa-ban"></i>
                        </button>
                    </td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    activityContent.innerHTML = '';
    activityContent.appendChild(table);
}

// Tab functionality
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'config') {
        loadConfiguration();
    }
}

// Search for a specific user
async function searchUser() {
    const ip = document.getElementById('user-search').value.trim();
    if (!ip) {
        showError('Please enter an IP address to search.');
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/user/${encodeURIComponent(ip)}`);
        const data = await response.json();
        
        const resultsDiv = document.getElementById('user-search-results');
        
        if (response.ok && data.user) {
            displayUserDetails(data.user, resultsDiv);
        } else {
            resultsDiv.innerHTML = '<div class="error">User not found or no activity recorded.</div>';
        }
    } catch (error) {
        showError('Error searching for user: ' + error.message);
    }
}

// Display user details
function displayUserDetails(user, container) {
    container.innerHTML = `
        <div class="admin-section">
            <h3>User Details: <code>${user.ip_address}</code></h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total Messages</h4>
                    <p class="stat-value">${user.total_messages}</p>
                </div>
                <div class="stat-card">
                    <h4>Flagged Messages</h4>
                    <p class="stat-value">${user.flagged_messages}</p>
                </div>
                <div class="stat-card">
                    <h4>Last Activity</h4>
                    <p style="font-size: 0.875rem;">${formatDateTime(user.last_activity)}</p>
                </div>
                <div class="stat-card">
                    <h4>Status</h4>
                    <p>
                        ${user.is_blocked 
                            ? '<span class="blocked-badge">Blocked</span>' 
                            : '<span class="normal-badge">Active</span>'}
                    </p>
                </div>
            </div>
            ${user.is_blocked ? `
                <div class="error">
                    <strong>Block Reason:</strong> ${user.block_reason}
                </div>
            ` : ''}
            <div style="margin-top: 1rem;">
                ${user.is_blocked 
                    ? `<button class="btn btn-success" onclick="unblockUserConfirm('${user.ip_address}')">
                        <i class="fas fa-check"></i> Unblock User
                    </button>`
                    : `<button class="btn btn-danger" onclick="quickBlockUser('${user.ip_address}')">
                        <i class="fas fa-ban"></i> Block User
                    </button>`
                }
            </div>
        </div>
    `;
}

// Block user modal functions
function showBlockUserModal(ip = '') {
    document.getElementById('block-ip').value = ip;
    document.getElementById('block-reason').value = '';
    document.getElementById('block-duration').value = '24';
    document.getElementById('block-user-modal').classList.add('show');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => modal.classList.remove('show'));
}

// Quick block user with default settings
function quickBlockUser(ip) {
    showBlockUserModal(ip);
}

// Block user
async function blockUser() {
    const ip = document.getElementById('block-ip').value.trim();
    const reason = document.getElementById('block-reason').value.trim();
    const duration = parseInt(document.getElementById('block-duration').value);
    
    if (!ip) {
        showError('IP address is required.');
        return;
    }
    
    if (!reason) {
        showError('Reason for blocking is required.');
        return;
    }
    
    try {
        const response = await fetch('/api/admin/block', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ip: ip,
                reason: reason,
                duration_hours: duration
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(data.message);
            closeModal();
            loadDashboardData(); // Refresh data
        } else {
            showError('Failed to block user: ' + data.error);
        }
    } catch (error) {
        showError('Error blocking user: ' + error.message);
    }
}

// Unblock user with confirmation
function unblockUserConfirm(ip) {
    if (confirm(`Are you sure you want to unblock user ${ip}?`)) {
        unblockUser(ip);
    }
}

// Unblock user
async function unblockUser(ip) {
    try {
        const response = await fetch('/api/admin/unblock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ip: ip })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(data.message);
            loadDashboardData(); // Refresh data
            // Refresh user search if it was showing this user
            const searchIp = document.getElementById('user-search').value;
            if (searchIp === ip) {
                searchUser();
            }
        } else {
            showError('Failed to unblock user: ' + data.error);
        }
    } catch (error) {
        showError('Error unblocking user: ' + error.message);
    }
}

// Load configuration
async function loadConfiguration() {
    try {
        const [configResponse, badWordsResponse] = await Promise.all([
            fetch('/api/admin/config'),
            fetch('/api/admin/bad-words')
        ]);
        
        const configData = await configResponse.json();
        const badWordsData = await badWordsResponse.json();
        
        if (configResponse.ok && badWordsResponse.ok) {
            displayConfiguration(configData.config, badWordsData);
        } else {
            showError('Failed to load configuration');
        }
    } catch (error) {
        showError('Error loading configuration: ' + error.message);
    }
}

// Display configuration form
function displayConfiguration(config, badWordsData) {
    const configContent = document.getElementById('config-content');
    
    configContent.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div>
                <h3>Rate Limiting & Thresholds</h3>
                <div class="form-group">
                    <label for="max-messages-hour">Max Messages per Hour:</label>
                    <input type="number" id="max-messages-hour" value="${config.max_messages_per_hour}">
                </div>
                <div class="form-group">
                    <label for="auto-block-threshold">Auto-block Threshold:</label>
                    <input type="number" id="auto-block-threshold" value="${config.auto_block_threshold}">
                </div>
                <div class="form-group">
                    <label for="block-duration">Default Block Duration (hours):</label>
                    <input type="number" id="block-duration-config" value="${config.block_duration_hours}">
                </div>
                <div class="form-group">
                    <label for="warning-threshold">Warning Threshold:</label>
                    <input type="number" id="warning-threshold" value="${config.warning_threshold}">
                </div>
            </div>
            <div>
                <h3>Content Moderation</h3>
                <div class="form-group">
                    <label for="bad-words">Bad Words (one per line):</label>
                    <textarea id="bad-words" rows="10">${badWordsData.words.join('\\n')}</textarea>
                </div>
                <div class="form-group">
                    <label for="bad-patterns">Regex Patterns (one per line):</label>
                    <textarea id="bad-patterns" rows="5">${badWordsData.patterns.join('\\n')}</textarea>
                </div>
            </div>
        </div>
    `;
}

// Save configuration
async function saveConfig() {
    try {
        // Collect configuration data
        const config = {
            max_messages_per_hour: parseInt(document.getElementById('max-messages-hour').value),
            auto_block_threshold: parseInt(document.getElementById('auto-block-threshold').value),
            block_duration_hours: parseInt(document.getElementById('block-duration-config').value),
            warning_threshold: parseInt(document.getElementById('warning-threshold').value)
        };
        
        const badWords = document.getElementById('bad-words').value
            .split('\\n')
            .map(word => word.trim())
            .filter(word => word.length > 0);
        
        const badPatterns = document.getElementById('bad-patterns').value
            .split('\\n')
            .map(pattern => pattern.trim())
            .filter(pattern => pattern.length > 0);
        
        // Save configuration
        const [configResponse, badWordsResponse] = await Promise.all([
            fetch('/api/admin/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            }),
            fetch('/api/admin/bad-words', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    words: badWords,
                    patterns: badPatterns
                })
            })
        ]);
        
        if (configResponse.ok && badWordsResponse.ok) {
            showSuccess('Configuration saved successfully!');
        } else {
            showError('Failed to save configuration');
        }
    } catch (error) {
        showError('Error saving configuration: ' + error.message);
    }
}

// Refresh activity data
function refreshActivity() {
    loadDashboardData();
}

// View user details in modal or separate view
function viewUserDetails(ip) {
    document.getElementById('user-search').value = ip;
    showTab('moderation');
    searchUser();
}

// Utility functions
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showError(message) {
    // Create and show error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    // Insert at top of admin container
    const container = document.querySelector('.admin-container');
    container.insertBefore(errorDiv, container.firstChild);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

function showSuccess(message) {
    // Create and show success notification
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    
    // Insert at top of admin container
    const container = document.querySelector('.admin-container');
    container.insertBefore(successDiv, container.firstChild);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.parentNode.removeChild(successDiv);
        }
    }, 3000);
}

// Auto-refresh dashboard every 30 seconds
setInterval(loadDashboardData, 30000);