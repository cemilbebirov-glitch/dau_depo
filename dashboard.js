/* ============================================
   DAU JARVIS DASHBOARD - CORE ENGINE
   ============================================ */

// ---- GLOBAL STATE ----
const DAU = {
    socket: null,
    currentModule: 'memory',
    startTime: Date.now(),
    monitorInterval: null,
    chatHistory: []
};

// ---- BOOT SEQUENCE ----
document.addEventListener('DOMContentLoaded', () => {
    bootSequence();
});

function bootSequence() {
    const bootBar = document.getElementById('bootBar');
    const bootText = document.getElementById('bootText');
    const bootScreen = document.getElementById('bootScreen');
    const mainDashboard = document.getElementById('mainDashboard');

    const steps = [
        { pct: 10, text: 'SİSTEM ÇEKİRLƏYİ YÜKLƏNİR...' },
        { pct: 25, text: 'NEURAL ŞƏBƏKƏ BAĞLANIR...' },
        { pct: 40, text: 'YADDAŞ MODULU AKTİVLAŞDIRILIR...' },
        { pct: 55, text: 'AGENT SİSTEMİ BAŞLAYIR...' },
        { pct: 70, text: 'MONİTOR İNTERFEYSİ HAZIRLANIR...' },
        { pct: 85, text: 'TƏHLÜKƏSİZLİK PROTOKOLU YOXLANILIR...' },
        { pct: 95, text: 'SON HAZIRLIQLAR...' },
        { pct: 100, text: 'JARVIS SİSTEMİ HAZIRDIR' }
    ];

    let i = 0;
    const interval = setInterval(() => {
        if (i < steps.length) {
            bootBar.style.width = steps[i].pct + '%';
            bootText.textContent = steps[i].text;
            i++;
        } else {
            clearInterval(interval);
            setTimeout(() => {
                bootScreen.classList.add('fade-out');
                setTimeout(() => {
                    bootScreen.style.display = 'none';
                    mainDashboard.style.display = 'flex';
                    initDashboard();
                }, 800);
            }, 500);
        }
    }, 350);
}

// ---- DASHBOARD INIT ----
function initDashboard() {
    initSocket();
    initClock();
    initUptime();
    checkServices();
    loadInitialData();
}

// ---- SOCKET.IO ----
function initSocket() {
    DAU.socket = io();

    DAU.socket.on('connect', () => {
        console.log('[DAU] Socket bağlandı');
        showToast('Socket bağlantısı quruldu', 'success');
    });

    DAU.socket.on('disconnect', () => {
        console.log('[DAU] Socket kəsildi');
        showToast('Socket bağlantısı kəsildi', 'error');
    });

    DAU.socket.on('chat_response', (data) => {
        handleChatResponse(data);
    });

    DAU.socket.on('monitor_data', (data) => {
        if (typeof updateMonitorLive === 'function') {
            updateMonitorLive(data);
        }
        updateHudMetrics(data);
    });
}

// ---- CLOCK ----
function initClock() {
    function updateClock() {
        const now = new Date();
        const months = ['YAN', 'FEV', 'MAR', 'APR', 'MAY', 'İYN', 'İYL', 'AVQ', 'SEN', 'OKT', 'NOY', 'DEK'];
        const dateStr = `${now.getDate().toString().padStart(2, '0')} ${months[now.getMonth()]} ${now.getFullYear()}`;
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;

        const hudDate = document.getElementById('hudDate');
        const hudTime = document.getElementById('hudTime');
        if (hudDate) hudDate.textContent = dateStr;
        if (hudTime) hudTime.textContent = timeStr;
    }
    updateClock();
    setInterval(updateClock, 1000);
}

// ---- UPTIME ----
function initUptime() {
    function updateUptime() {
        const elapsed = Date.now() - DAU.startTime;
        const days = Math.floor(elapsed / 86400000);
        const hours = Math.floor((elapsed % 86400000) / 3600000);
        const mins = Math.floor((elapsed % 3600000) / 60000);
        const el = document.getElementById('sysUptime');
        if (el) el.textContent = `${days}g ${hours}s ${mins}d`;
    }
    updateUptime();
    setInterval(updateUptime, 60000);
}

// ---- SERVICE CHECKS ----
function checkServices() {
    // Check Ollama
    fetch('http://localhost:11434/api/tags', { method: 'GET', signal: AbortSignal.timeout(3000) })
        .then(r => {
            if (r.ok) {
                document.getElementById('hudOllamaStatus').textContent = 'AKTİV';
                document.getElementById('hudOllamaStatus').style.color = '#00ff66';
            } else {
                throw new Error();
            }
        })
        .catch(() => {
            document.getElementById('hudOllamaStatus').textContent = 'DEAKTİV';
            document.getElementById('hudOllamaStatus').style.color = '#ff3333';
        });

    // Check DB
    fetch('/api/memory/list', { signal: AbortSignal.timeout(3000) })
        .then(r => {
            if (r.ok) {
                document.getElementById('hudDbStatus').textContent = 'AKTİV';
                document.getElementById('hudDbStatus').style.color = '#00ff66';
            } else {
                throw new Error();
            }
        })
        .catch(() => {
            document.getElementById('hudDbStatus').textContent = 'XƏTA';
            document.getElementById('hudDbStatus').style.color = '#ff3333';
        });
}

// ---- LOAD INITIAL DATA ----
function loadInitialData() {
    if (typeof memoryRefresh === 'function') memoryRefresh();
    if (typeof modelLoadActive === 'function') modelLoadActive();
    if (typeof modelLoadList === 'function') modelLoadList();
    if (typeof monitorRefresh === 'function') monitorRefresh();
    if (typeof workspaceRefresh === 'function') workspaceRefresh();
    if (typeof tradingLoadStrategies === 'function') tradingLoadStrategies();

    // Chat welcome time
    const now = new Date();
    const el = document.getElementById('chatWelcomeTime');
    if (el) el.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
}

// ---- MODULE SWITCHING ----
function switchModule(moduleName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.module === moduleName) {
            item.classList.add('active');
        }
    });

    // Update panels
    document.querySelectorAll('.module-panel').forEach(panel => {
        panel.style.display = 'none';
    });

    const targetPanel = document.getElementById('module-' + moduleName);
    if (targetPanel) {
        targetPanel.style.display = 'block';
    }

    DAU.currentModule = moduleName;

    // Load module data
    switch (moduleName) {
        case 'memory': if (typeof memoryRefresh === 'function') memoryRefresh(); break;
        case 'agent': break;
        case 'rag': if (typeof ragLoadDocs === 'function') ragLoadDocs(); break;
        case 'trading': if (typeof tradingRefresh === 'function') tradingRefresh(); break;
        case 'mt5': if (typeof mt5CheckStatus === 'function') mt5CheckStatus(); break;
        case 'workspace': if (typeof workspaceRefresh === 'function') workspaceRefresh(); break;
        case 'monitor': if (typeof monitorRefresh === 'function') monitorRefresh(); break;
        case 'model': if (typeof modelLoadList === 'function') modelLoadList(); break;
    }
}

// ---- UPDATE HUD METRICS ----
function updateHudMetrics(data) {
    if (data.cpu_percent !== undefined) {
        const hudCpu = document.getElementById('hudCpu');
        if (hudCpu) hudCpu.textContent = data.cpu_percent.toFixed(1) + '%';
    }
    if (data.memory_percent !== undefined) {
        const hudRam = document.getElementById('hudRam');
        if (hudRam) hudRam.textContent = data.memory_percent.toFixed(1) + '%';
    }
    if (data.cpu_temp !== undefined) {
        const hudTemp = document.getElementById('hudTemp');
        if (hudTemp) hudTemp.textContent = data.cpu_temp.toFixed(0) + '°C';
    }
    if (data.network_sent_speed !== undefined || data.network_recv_speed !== undefined) {
        const sent = data.network_sent_speed || 0;
        const recv = data.network_recv_speed || 0;
        const total = sent + recv;
        const el = document.getElementById('hudNetwork');
        if (el) {
            if (total > 1024 * 1024) {
                el.textContent = `NET: ${(total / 1024 / 1024).toFixed(1)} MB/s`;
            } else if (total > 1024) {
                el.textContent = `NET: ${(total / 1024).toFixed(1)} KB/s`;
            } else {
                el.textContent = `NET: ${total.toFixed(0)} B/s`;
            }
        }
    }
}

// ---- CHAT SYSTEM ----
function chatSend() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    addChatMessage('user', message);

    // Show typing indicator
    addTypingIndicator();

    // Send via Socket or API
    if (DAU.socket && DAU.socket.connected) {
        DAU.socket.emit('chat_message', { message: message });
    } else {
        // Fallback to REST API
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(r => r.json())
        .then(data => {
            removeTypingIndicator();
            if (data.response) {
                addChatMessage('assistant', data.response);
            } else if (data.error) {
                addChatMessage('system', 'Xəta: ' + data.error);
            }
        })
        .catch(err => {
            removeTypingIndicator();
            addChatMessage('system', 'Bağlantı xətası: ' + err.message);
        });
    }
}

function handleChatResponse(data) {
    removeTypingIndicator();
    if (data.response) {
        addChatMessage('assistant', data.response);
    } else if (data.error) {
        addChatMessage('system', 'Xəta: ' + data.error);
    }
}

function addChatMessage(role, text) {
    const container = document.getElementById('chatMessages');
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    const avatarMap = {
        'user': 'SİZ',
        'assistant': 'DAU',
        'system': 'SYS'
    };

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role === 'user' ? 'user' : ''}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatarMap[role] || 'DAU'}</div>
        <div class="msg-bubble">
            <div class="msg-text">${escapeHtml(text)}</div>
            <div class="msg-time">${timeStr}</div>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chatMessages');
    const indicator = document.createElement('div');
    indicator.className = 'chat-msg';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="msg-avatar">DAU</div>
        <div class="msg-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

// ---- TOAST NOTIFICATIONS ----
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✓',
        error: '✗',
        info: '●'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || '●'}</span> ${escapeHtml(message)}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ---- UTILITY FUNCTIONS ----
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '--';
    const d = new Date(dateStr);
    const months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'İyn', 'İyl', 'Avq', 'Sen', 'Okt', 'Noy', 'Dek'];
    return `${d.getDate().toString().padStart(2, '0')} ${months[d.getMonth()]} ${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '--';
    return parseFloat(num).toFixed(decimals);
}

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        return data;
    } catch (error) {
        console.error(`[DAU] API xətası: ${url}`, error);
        showToast(error.message, 'error');
        throw error;
    }
}

// ---- GAUGE UPDATE HELPER ----
function updateGauge(fillId, textId, percent, maxPercent = 100) {
    const circumference = 339.29;
    const clampedPercent = Math.min(Math.max(percent, 0), maxPercent);
    const offset = circumference - (clampedPercent / maxPercent * circumference);

    const fill = document.getElementById(fillId);
    const text = document.getElementById(textId);
    if (fill) fill.style.strokeDashoffset = offset;
    if (text) text.textContent = clampedPercent.toFixed(0) + '%';
}