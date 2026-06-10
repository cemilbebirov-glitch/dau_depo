/**
 * DAU Agent Sistemi - Agent seçimi və söhbət
 */

const AgentManager = {
    // Agent siyahısı
    agents: {
        jarvis: { name: 'JARVIS', internal: 'core', icon: '🤖', color: '#ff0040' },
        trader: { name: 'Trader', internal: 'trading', icon: '📈', color: '#00ff88' },
        coder: { name: 'Coder', internal: 'coding', icon: '💻', color: '#00aaff' },
        researcher: { name: 'Researcher', internal: 'research', icon: '🔍', color: '#ffaa00' },
        knowledge: { name: 'Knowledge', internal: 'knowledge', icon: '📚', color: '#aa00ff' }
    },

    currentAgent: 'jarvis',
    isLoading: false,

    // Agent siyahısını HTML-ə çevir
    renderAgentList: function() {
        const container = document.getElementById('agent-list');
        if (!container) return;

        let html = '';
        for (const [key, agent] of Object.entries(this.agents)) {
            const active = key === this.currentAgent ? 'active' : '';
            html += `
                <div class="agent-item ${active}" data-agent="${key}" onclick="AgentManager.selectAgent('${key}')">
                    <span class="agent-icon">${agent.icon}</span>
                    <span class="agent-name">${agent.name}</span>
                </div>
            `;
        }
        container.innerHTML = html;
    },

    // Agent seç
    selectAgent: function(agentKey) {
        this.currentAgent = agentKey;
        this.renderAgentList();

        // UI yenilə
        const chatTitle = document.getElementById('chat-title');
        if (chatTitle) {
            chatTitle.textContent = this.agents[agentKey].name;
        }

        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.placeholder = `${this.agents[agentKey].name}-a mesaj yaz...`;
        }

        console.log(`Agent seçildi: ${this.agents[agentKey].name}`);
    },

    // Mesaj göndər
    sendMessage: function(message) {
        if (!message || this.isLoading) return;

        this.isLoading = true;
        this.showTyping();

        fetch('/api/agent/delegate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 'default-user',
                message: message,
                agent_name: this.agents[this.currentAgent].internal
            })
        })
        .then(res => res.json())
        .then(data => {
            this.isLoading = false;
            this.hideTyping();

            const response = data.response || data.error || 'Cavab alına bilmədi';
            if (typeof DashboardEngine !== 'undefined' && DashboardEngine.addChatMessage) {
                DashboardEngine.addChatMessage('bot', response);
            }
        })
        .catch(err => {
            this.isLoading = false;
            this.hideTyping();
            console.error('Agent xətası:', err);
            if (typeof DashboardEngine !== 'undefined' && DashboardEngine.addChatMessage) {
                DashboardEngine.addChatMessage('bot', 'Xəta baş verdi. Yenidən cəhd edin.');
            }
        });
    },

    // Yazır göstəricisi
    showTyping: function() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.style.display = 'flex';
    },

    hideTyping: function() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.style.display = 'none';
    }
};

// Səhifə yüklənəndə agent siyahısını göstər
document.addEventListener('DOMContentLoaded', function() {
    AgentManager.renderAgentList();
});