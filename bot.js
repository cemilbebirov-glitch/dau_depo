// ============================================================
// DAU JARVIS - TRADING BOT MODULE (bot.js)
// Red JARVIS/Hacker Theme Trading Bot Frontend
// ============================================================

const BotManager = {
    bots: [],
    strategies: [],
    alerts: [],
    learningEntries: [],
    selectedBot: null,
    updateInterval: null,
    socket: null,

    // ==================== INIT ====================
    init() {
        console.log('[BOT] Trading Bot Module initializing...');
        this.loadStrategies();
        this.loadBots();
        this.loadAlerts();
        this.loadLearning();
        this.loadStats();
        this.setupWebSocket();
        this.setupEventListeners();
        console.log('[BOT] Trading Bot Module ready!');
    },

    setupWebSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.socket.on('bot_trade_update', (data) => {
                this.onTradeUpdate(data);
            });
            this.socket.on('bot_status_update', (data) => {
                this.onStatusUpdate(data);
            });
        }
    },

    setupEventListeners() {
        // Simvol select change - show price
        const symbolSelect = document.getElementById('botSymbol');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', () => {
                this.onSymbolChange();
            });
        }
    },

    // ==================== API CALLS ====================
    async apiCall(endpoint, method = 'GET', body = null) {
        try {
            const opts = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (body) opts.body = JSON.stringify(body);
            const resp = await fetch(`/api/bot${endpoint}`, opts);
            const data = await resp.json();
            if (!resp.ok) {
                this.showNotification('XƏTA', data.error || 'Naməlum xəta', 'error');
                return null;
            }
            return data;
        } catch (err) {
            console.error('[BOT] API Error:', err);
            this.showNotification('XƏTA', 'Server ilə əlaqə kəsildi', 'error');
            return null;
        }
    },

    // ==================== BOT CRUD ====================
    async loadBots() {
        const data = await this.apiCall('/list');
        if (data) {
            this.bots = data.bots || [];
            this.renderBotList();
            this.renderBotCards();
        }
    },

    async createBot() {
        const config = {
            name: document.getElementById('botName')?.value || 'Yeni Bot',
            symbol: document.getElementById('botSymbol')?.value || 'XAUUSDm',
            mode: document.getElementById('botMode')?.value || 'semi_autonomous',
            lot_size: parseFloat(document.getElementById('botLotSize')?.value || 0.01),
            stop_loss: parseFloat(document.getElementById('botStopLoss')?.value || 0),
            take_profit: parseFloat(document.getElementById('botTakeProfit')?.value || 0),
            trailing_stop: parseFloat(document.getElementById('botTrailingStop')?.value || 0),
            strategy_id: parseInt(document.getElementById('botStrategy')?.value || 1),
            timeframe: document.getElementById('botTimeframe')?.value || 'M15',
            max_daily_trades: parseInt(document.getElementById('botMaxTrades')?.value || 5),
            max_daily_loss: parseFloat(document.getElementById('botMaxLoss')?.value || 100),
            risk_per_trade: parseFloat(document.getElementById('botRiskPerTrade')?.value || 2.0)
        };

        if (!config.name.trim()) {
            this.showNotification('XƏTA', 'Bot adı boş ola bilməz', 'error');
            return;
        }

        const data = await this.apiCall('/create', 'POST', config);
        if (data) {
            this.showNotification('UGUR', `Bot "${config.name}" yaradildi!`, 'success');
            this.clearCreateForm();
            this.loadBots();
            this.loadStats();
        }
    },

    async deleteBot(botId) {
        if (!confirm('Bu botu silmək istəyirsiniz?')) return;
        const data = await this.apiCall(`/delete/${botId}`, 'DELETE');
        if (data) {
            this.showNotification('UGUR', 'Bot silindi!', 'success');
            if (this.selectedBot && this.selectedBot.id === botId) {
                this.selectedBot = null;
                this.hideBotDetail();
            }
            this.loadBots();
            this.loadStats();
        }
    },

    // ==================== BOT CONTROL ====================
    async startBot(botId) {
        const data = await this.apiCall(`/start/${botId}`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Bot isə salindi!', 'success');
            this.loadBots();
            this.startStatusPolling(botId);
        }
    },

    async stopBot(botId) {
        const data = await this.apiCall(`/stop/${botId}`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Bot dayandırıldı!', 'warning');
            this.loadBots();
            this.stopStatusPolling();
        }
    },

    async pauseBot(botId) {
        const data = await this.apiCall(`/pause/${botId}`, 'POST');
        if (data) {
            this.showNotification('BİLDİRİŞ', 'Bot fasilədədir', 'warning');
            this.loadBots();
        }
    },

    async resumeBot(botId) {
        const data = await this.apiCall(`/resume/${botId}`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Bot davam edir!', 'success');
            this.loadBots();
        }
    },

    async getBotStatus(botId) {
        const data = await this.apiCall(`/status/${botId}`);
        if (data) {
            this.updateBotStatusUI(data);
        }
    },

    // ==================== STATUS POLLING ====================
    startStatusPolling(botId) {
        this.stopStatusPolling();
        this.updateInterval = setInterval(() => {
            if (this.selectedBot) {
                this.getBotStatus(this.selectedBot.id);
            }
        }, 5000); // Hər 5 saniyə
    },

    stopStatusPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },

    // ==================== MANUAL TRADING ====================
    async manualTrade(direction) {
        if (!this.selectedBot) {
            this.showNotification('XƏTA', 'Əvvəlcə bot seçin', 'error');
            return;
        }

        const trade = {
            bot_id: this.selectedBot.id,
            symbol: this.selectedBot.symbol || document.getElementById('botSymbol')?.value || 'XAUUSDm',
            direction: direction, // 'BUY' or 'SELL'
            lot_size: parseFloat(document.getElementById('manualLotSize')?.value || 0.01),
            stop_loss: parseFloat(document.getElementById('manualSL')?.value || 0),
            take_profit: parseFloat(document.getElementById('manualTP')?.value || 0),
            comment: document.getElementById('manualComment')?.value || 'Manual trade'
        };

        const data = await this.apiCall('/trade/open', 'POST', trade);
        if (data) {
            this.showNotification('UGUR', `${direction} əmri göndərildi!`, 'success');
            this.loadBots();
            this.loadTrades(this.selectedBot.id);
        }
    },

    async closeTrade(ticket) {
        if (!confirm(`Ticket #${ticket} bağlamaq istəyirsiniz?`)) return;
        const data = await this.apiCall(`/trade/close/${ticket}`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Pozisiya bağlandı!', 'success');
            if (this.selectedBot) {
                this.loadTrades(this.selectedBot.id);
                this.getBotStatus(this.selectedBot.id);
            }
        }
    },

    // ==================== STRATEGIES ====================
    async loadStrategies() {
        const data = await this.apiCall('/strategies');
        if (data) {
            this.strategies = data.strategies || [];
            this.renderStrategies();
            this.populateStrategySelect();
        }
    },

    populateStrategySelect() {
        const select = document.getElementById('botStrategy');
        if (!select) return;
        select.innerHTML = '';
        this.strategies.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name;
            select.appendChild(opt);
        });
    },

    // ==================== TRADES ====================
    async loadTrades(botId) {
        const data = await this.apiCall(`/trades/${botId}`);
        if (data) {
            this.renderTrades(data.trades || []);
        }
    },

    async loadAllTrades() {
        const data = await this.apiCall('/trades/all');
        if (data) {
            this.renderTrades(data.trades || []);
        }
    },

    // ==================== ALERTS ====================
    async loadAlerts() {
        const data = await this.apiCall('/alerts');
        if (data) {
            this.alerts = data.alerts || [];
            this.renderAlerts();
        }
    },

    async markAlertRead(alertId) {
        const data = await this.apiCall(`/alerts/${alertId}/read`, 'POST');
        if (data) this.loadAlerts();
    },

    async actOnAlert(alertId) {
        const data = await this.apiCall(`/alerts/${alertId}/act`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Siqnal icra edildi!', 'success');
            this.loadAlerts();
        }
    },

    // ==================== LEARNING ====================
    async loadLearning() {
        const data = await this.apiCall('/learning');
        if (data) {
            this.learningEntries = data.entries || [];
            this.renderLearning();
        }
    },

    async applyLearning(entryId) {
        const data = await this.apiCall(`/learning/${entryId}/apply`, 'POST');
        if (data) {
            this.showNotification('UGUR', 'Dərs tətbiq edildi!', 'success');
            this.loadLearning();
        }
    },

    async rateLearning(entryId, rating) {
        const data = await this.apiCall(`/learning/${entryId}/rate`, 'POST', { rating });
        if (data) this.loadLearning();
    },

    // ==================== MARKET DATA ====================
    async getMarketData() {
        const symbol = document.getElementById('botSymbol')?.value || 'XAUUSDm';
        const data = await this.apiCall(`/market?symbol=${symbol}`);
        if (data) {
            this.renderMarketData(data);
        }
    },

    async onSymbolChange() {
        this.getMarketData();
    },

    // ==================== STATS ====================
    async loadStats() {
        const data = await this.apiCall('/stats');
        if (data) {
            this.renderStats(data);
        }
    },

    // ==================== MT5 CONNECTION ====================
    async connectMT5() {
        const data = await this.apiCall('/mt5/connect', 'POST');
        if (data) {
            this.showNotification('UGUR', 'MT5 qoşuldu!', 'success');
            this.updateMT5Status(true);
            this.loadMT5Account();
        }
    },

    async disconnectMT5() {
        const data = await this.apiCall('/mt5/disconnect', 'POST');
        if (data) {
            this.showNotification('BİLDİRİŞ', 'MT5 əlaqəsi kəsildi', 'warning');
            this.updateMT5Status(false);
        }
    },

    async loadMT5Account() {
        const data = await this.apiCall('/mt5/account');
        if (data && data.account) {
            this.renderMT5Account(data.account);
        }
    },

    async loadMT5Positions() {
        const data = await this.apiCall('/mt5/positions');
        if (data) {
            this.renderMT5Positions(data.positions || []);
        }
    },

    // ==================== SIMULATION ====================
    async runSimulation() {
        const params = {
            symbol: document.getElementById('botSymbol')?.value || 'XAUUSDm',
            strategy_id: parseInt(document.getElementById('botStrategy')?.value || 1),
            timeframe: document.getElementById('botTimeframe')?.value || 'M15',
            lot_size: parseFloat(document.getElementById('botLotSize')?.value || 0.01)
        };

        this.showNotification('BİLDİRİŞ', 'Simulyasiya başlayır...', 'info');
        const data = await this.apiCall('/simulate', 'POST', params);
        if (data) {
            this.showNotification('UGUR', 'Simulyasiya tamamlandı!', 'success');
            this.renderSimulationResults(data);
        }
    },

    // ==================== RENDER FUNCTIONS ====================

    renderBotList() {
        const container = document.getElementById('botListContainer');
        if (!container) return;

        if (this.bots.length === 0) {
            container.innerHTML = '<div class="hud-empty">Hələ bot yaradılmayıb. Yuxarıdakı formadan yeni bot yaradın.</div>';
            return;
        }

        container.innerHTML = this.bots.map(bot => {
            const statusClass = bot.status === 'running' ? 'bot-status-running' :
                               bot.status === 'paused' ? 'bot-status-paused' : 'bot-status-stopped';
            const statusText = bot.status === 'running' ? 'İŞLƏYİR' :
                              bot.status === 'paused' ? 'FAZİLƏDƏ' : 'DAYANIQ';
            const modeText = bot.mode === 'autonomous' ? 'AVTONOM' :
                            bot.mode === 'semi_autonomous' ? 'YARIMAVTONOM' : 'MANUAL';

            return `
                <div class="bot-list-item ${this.selectedBot && this.selectedBot.id === bot.id ? 'active' : ''}"
                     onclick="BotManager.selectBot(${bot.id})">
                    <div class="bot-list-info">
                        <div class="bot-list-name">${bot.name}</div>
                        <div class="bot-list-meta">
                            <span class="bot-symbol-tag">${bot.symbol}</span>
                            <span class="bot-mode-tag">${modeText}</span>
                        </div>
                    </div>
                    <div class="bot-list-status ${statusClass}">
                        <span class="bot-status-dot"></span>
                        ${statusText}
                    </div>
                </div>
            `;
        }).join('');
    },

    renderBotCards() {
        const container = document.getElementById('botCardsContainer');
        if (!container) return;

        if (this.bots.length === 0) {
            container.innerHTML = '<div class="hud-empty">Bot yoxdur</div>';
            return;
        }

        container.innerHTML = this.bots.map(bot => {
            const statusClass = bot.status === 'running' ? 'running' :
                               bot.status === 'paused' ? 'paused' : 'stopped';
            const statusText = bot.status === 'running' ? 'İŞLƏYİR' :
                              bot.status === 'paused' ? 'FAZİLƏDƏ' : 'DAYANIQ';
            const modeText = bot.mode === 'autonomous' ? 'AVTONOM' :
                            bot.mode === 'semi_autonomous' ? 'YARIMAVT.' : 'MANUAL';
            const pnlClass = (bot.total_pnl || 0) >= 0 ? 'pnl-positive' : 'pnl-negative';

            return `
                <div class="bot-card ${statusClass}" onclick="BotManager.selectBot(${bot.id})">
                    <div class="bot-card-header">
                        <div class="bot-card-name">${bot.name}</div>
                        <div class="bot-card-status ${statusClass}">
                            <span class="bot-status-dot"></span>${statusText}
                        </div>
                    </div>
                    <div class="bot-card-body">
                        <div class="bot-card-row">
                            <span class="bot-card-label">SİMVOL</span>
                            <span class="bot-card-value">${bot.symbol}</span>
                        </div>
                        <div class="bot-card-row">
                            <span class="bot-card-label">REJİM</span>
                            <span class="bot-card-value">${modeText}</span>
                        </div>
                        <div class="bot-card-row">
                            <span class="bot-card-label">HƏCM</span>
                            <span class="bot-card-value">${bot.lot_size}</span>
                        </div>
                        <div class="bot-card-row">
                            <span class="bot-card-label">TİCARƏT</span>
                            <span class="bot-card-value">${bot.total_trades || 0}</span>
                        </div>
                        <div class="bot-card-row">
                            <span class="bot-card-label">P&L</span>
                            <span class="bot-card-value ${pnlClass}">${(bot.total_pnl || 0).toFixed(2)}</span>
                        </div>
                    </div>
                    <div class="bot-card-actions">
                        ${bot.status !== 'running' ?
                            `<button class="btn-bot btn-start" onclick="event.stopPropagation(); BotManager.startBot(${bot.id})">▶ BAŞLA</button>` :
                            `<button class="btn-bot btn-stop" onclick="event.stopPropagation(); BotManager.stopBot(${bot.id})">■ DAYAN</button>`
                        }
                        ${bot.status === 'running' ?
                            `<button class="btn-bot btn-pause" onclick="event.stopPropagation(); BotManager.pauseBot(${bot.id})">⏸ FAZİLƏ</button>` : ''
                        }
                        ${bot.status === 'paused' ?
                            `<button class="btn-bot btn-resume" onclick="event.stopPropagation(); BotManager.resumeBot(${bot.id})">▶ DAVAM</button>` : ''
                        }
                        <button class="btn-bot btn-delete" onclick="event.stopPropagation(); BotManager.deleteBot(${bot.id})">✕ SİL</button>
                    </div>
                </div>
            `;
        }).join('');
    },

    selectBot(botId) {
        const bot = this.bots.find(b => b.id === botId);
        if (!bot) return;
        this.selectedBot = bot;
        this.showBotDetail(bot);
        this.loadTrades(botId);
        this.getBotStatus(botId);
        if (bot.status === 'running') {
            this.startStatusPolling(botId);
        }
    },

    showBotDetail(bot) {
        const detail = document.getElementById('botDetailPanel');
        if (!detail) return;
        detail.style.display = 'block';

        const modeText = bot.mode === 'autonomous' ? 'Aavtonom' :
                        bot.mode === 'semi_autonomous' ? 'Yarımavtonom' : 'Manual';
        const statusClass = bot.status === 'running' ? 'running' :
                           bot.status === 'paused' ? 'paused' : 'stopped';
        const statusText = bot.status === 'running' ? 'İŞLƏYİR' :
                          bot.status === 'paused' ? 'FAZİLƏDƏ' : 'DAYANIQ';
        const pnlClass = (bot.total_pnl || 0) >= 0 ? 'pnl-positive' : 'pnl-negative';

        detail.innerHTML = `
            <div class="bot-detail-header">
                <h3 class="bot-detail-title">${bot.name}</h3>
                <div class="bot-detail-status ${statusClass}">
                    <span class="bot-status-dot"></span>${statusText}
                </div>
            </div>
            <div class="bot-detail-grid">
                <div class="bot-detail-item">
                    <span class="detail-label">SİMVOL</span>
                    <span class="detail-value">${bot.symbol}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">REJİM</span>
                    <span class="detail-value">${modeText}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">HƏCM</span>
                    <span class="detail-value">${bot.lot_size}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">STRATEQİ</span>
                    <span class="detail-value">${this.getStrategyName(bot.strategy_id)}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">STOP LOSS</span>
                    <span class="detail-value">${bot.stop_loss || 'Yoxdur'}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">TAKE PROFİT</span>
                    <span class="detail-value">${bot.take_profit || 'Yoxdur'}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">TRAİLİNG</span>
                    <span class="detail-value">${bot.trailing_stop || 'Yoxdur'}</span>
                </div>
                <div class="bot-detail-item">
                    <span class="detail-label">TİMEFRAME</span>
                    <span class="detail-value">${bot.timeframe || 'M15'}</span>
                </div>
            </div>
            <div class="bot-detail-stats">
                <div class="detail-stat">
                    <span class="detail-stat-value">${bot.total_trades || 0}</span>
                    <span class="detail-stat-label">CƏMİ TİCARƏT</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-value">${bot.win_trades || 0}</span>
                    <span class="detail-stat-label">QAZANMA</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-value">${bot.loss_trades || 0}</span>
                    <span class="detail-stat-label">ITIRMA</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-value ${pnlClass}">${(bot.total_pnl || 0).toFixed(2)}</span>
                    <span class="detail-stat-label">CƏMİ P&L</span>
                </div>
            </div>
            <!-- Manual Trade Panel -->
            <div class="bot-manual-trade">
                <h4 class="subsection-title">MANUAL TİCARƏT</h4>
                <div class="manual-trade-row">
                    <div class="form-group">
                        <label class="hud-label">HƏCM</label>
                        <input type="number" id="manualLotSize" class="hud-input" step="0.01" value="${bot.lot_size}">
                    </div>
                    <div class="form-group">
                        <label class="hud-label">SL</label>
                        <input type="number" id="manualSL" class="hud-input" step="0.01" value="${bot.stop_loss || 0}">
                    </div>
                    <div class="form-group">
                        <label class="hud-label">TP</label>
                        <input type="number" id="manualTP" class="hud-input" step="0.01" value="${bot.take_profit || 0}">
                    </div>
                </div>
                <div class="form-group">
                    <label class="hud-label">QEYD</label>
                    <input type="text" id="manualComment" class="hud-input" placeholder="Qeyd...">
                </div>
                <div class="manual-trade-buttons">
                    <button class="btn-bot btn-buy" onclick="BotManager.manualTrade('BUY')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M7 14l5-5 5 5"/></svg>
                        ALIŞ
                    </button>
                    <button class="btn-bot btn-sell" onclick="BotManager.manualTrade('SELL')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M7 10l5 5 5-5"/></svg>
                        SATIŞ
                    </button>
                </div>
            </div>
        `;
    },

    hideBotDetail() {
        const detail = document.getElementById('botDetailPanel');
        if (detail) detail.style.display = 'none';
    },

    updateBotStatusUI(data) {
        if (!data || !data.bot) return;
        const bot = data.bot;
        // Update the selected bot
        if (this.selectedBot && this.selectedBot.id === bot.id) {
            this.selectedBot = bot;
            this.showBotDetail(bot);
        }
        // Update in bots list
        const idx = this.bots.findIndex(b => b.id === bot.id);
        if (idx >= 0) this.bots[idx] = bot;
        this.renderBotList();
        this.renderBotCards();
    },

    renderTrades(trades) {
        const container = document.getElementById('botTradesTableBody');
        if (!container) return;

        if (!trades || trades.length === 0) {
            container.innerHTML = '<tr><td colspan="8" class="hud-empty">Ticarət yoxdur</td></tr>';
            return;
        }

        container.innerHTML = trades.map(t => {
            const pnlClass = (t.pnl || 0) >= 0 ? 'pnl-positive' : 'pnl-negative';
            const dirClass = t.direction === 'BUY' ? 'trade-buy' : 'trade-sell';
            return `
                <tr>
                    <td><span class="trade-dir ${dirClass}">${t.direction}</span></td>
                    <td>${t.symbol}</td>
                    <td>${t.lot_size}</td>
                    <td>${t.entry_price ? t.entry_price.toFixed(5) : '--'}</td>
                    <td>${t.exit_price ? t.exit_price.toFixed(5) : 'Açıq'}</td>
                    <td class="${pnlClass}">${(t.pnl || 0).toFixed(2)}</td>
                    <td>${t.signal_source || '--'}</td>
                    <td>
                        ${!t.exit_price ? `<button class="btn-bot btn-close-pos" onclick="BotManager.closeTrade(${t.ticket})">BAĞLA</button>` : '--'}
                    </td>
                </tr>
            `;
        }).join('');
    },

    renderStrategies() {
        const container = document.getElementById('botStrategiesList');
        if (!container) return;

        if (this.strategies.length === 0) {
            container.innerHTML = '<div class="hud-empty">Strateqİ yoxdur</div>';
            return;
        }

        container.innerHTML = this.strategies.map(s => `
            <div class="strategy-card">
                <div class="strategy-header">
                    <span class="strategy-name">${s.name}</span>
                    <span class="strategy-type">${s.strategy_type}</span>
                </div>
                <div class="strategy-desc">${s.az_description || s.description || ''}</div>
                <div class="strategy-indicators">
                    ${(s.indicators || []).map(ind => `<span class="indicator-tag">${ind}</span>`).join('')}
                </div>
            </div>
        `).join('');
    },

    renderAlerts() {
        const container = document.getElementById('botAlertsList');
        if (!container) return;

        if (this.alerts.length === 0) {
            container.innerHTML = '<div class="hud-empty">Siqnal yoxdur</div>';
            return;
        }

        container.innerHTML = this.alerts.slice(0, 10).map(a => {
            const strengthClass = a.strength === 'strong' ? 'alert-strong' :
                                 a.strength === 'medium' ? 'alert-medium' : 'alert-weak';
            return `
                <div class="alert-card ${a.is_read ? 'read' : 'unread'}">
                    <div class="alert-header">
                        <span class="alert-type">${a.alert_type}</span>
                        <span class="alert-strength ${strengthClass}">${a.strength}</span>
                    </div>
                    <div class="alert-symbol">${a.symbol}</div>
                    <div class="alert-message">${a.message || ''}</div>
                    <div class="alert-actions">
                        ${!a.is_read ? `<button class="btn-bot btn-sm" onclick="BotManager.markAlertRead(${a.id})">OXUNDU</button>` : ''}
                        ${a.alert_type === 'signal' ? `<button class="btn-bot btn-sm btn-buy" onclick="BotManager.actOnAlert(${a.id})">İCRA ET</button>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    },

    renderLearning() {
        const container = document.getElementById('botLearningList');
        if (!container) return;

        if (this.learningEntries.length === 0) {
            container.innerHTML = '<div class="hud-empty">Öyrənmə məlumatı yoxdur</div>';
            return;
        }

        container.innerHTML = this.learningEntries.slice(0, 10).map(e => {
            const appliedClass = e.is_applied ? 'applied' : 'pending';
            return `
                <div class="learning-card ${appliedClass}">
                    <div class="learning-type">${e.learning_type}</div>
                    <div class="learning-lesson">${e.lesson}</div>
                    <div class="learning-meta">
                        <span>Etibar: ${(e.confidence * 100 || 0).toFixed(0)}%</span>
                        <span>Səmərə: ${(e.effectiveness * 100 || 0).toFixed(0)}%</span>
                    </div>
                    <div class="learning-actions">
                        ${!e.is_applied ? `<button class="btn-bot btn-sm" onclick="BotManager.applyLearning(${e.id})">TƏTBİQ ET</button>` : '<span class="applied-badge">TƏTBİQ EDİLDİ</span>'}
                        <div class="learning-rate">
                            <button class="btn-rate" onclick="BotManager.rateLearning(${e.id}, 1)">👍</button>
                            <button class="btn-rate" onclick="BotManager.rateLearning(${e.id}, -1)">👎</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderMarketData(data) {
        const container = document.getElementById('botMarketDisplay');
        if (!container || !data) return;
        container.style.display = 'block';

        const price = data.current_price || data.price || '--';
        container.innerHTML = `
            <div class="market-price-display">
                <span class="market-symbol">${data.symbol || ''}</span>
                <span class="market-price">${typeof price === 'number' ? price.toFixed(5) : price}</span>
                ${data.bid ? `<span class="market-sub">BİD: ${data.bid.toFixed(5)}</span>` : ''}
                ${data.ask ? `<span class="market-sub">ASK: ${data.ask.toFixed(5)}</span>` : ''}
            </div>
        `;
    },

    renderStats(data) {
        const totalEl = document.getElementById('botStatTotal');
        const activeEl = document.getElementById('botStatActive');
        const tradesEl = document.getElementById('botStatTrades');
        const pnlEl = document.getElementById('botStatPnl');

        if (totalEl) totalEl.textContent = data.total_bots || 0;
        if (activeEl) activeEl.textContent = data.active_bots || 0;
        if (tradesEl) tradesEl.textContent = data.total_trades || 0;
        if (pnlEl) {
            const pnl = data.total_pnl || 0;
            pnlEl.textContent = pnl.toFixed(2);
            pnlEl.className = `stat-value ${pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`;
        }
    },

    renderMT5Account(account) {
        const container = document.getElementById('botMT5Info');
        if (!container) return;
        container.style.display = 'block';
        container.innerHTML = `
            <div class="mt5-account-grid">
                <div class="mt5-acc-item">
                    <span class="mt5-acc-label">BALANS</span>
                    <span class="mt5-acc-value">${(account.balance || 0).toFixed(2)}</span>
                </div>
                <div class="mt5-acc-item">
                    <span class="mt5-acc-label">SƏRMAYƏ</span>
                    <span class="mt5-acc-value">${(account.equity || 0).toFixed(2)}</span>
                </div>
                <div class="mt5-acc-item">
                    <span class="mt5-acc-label">MƏNFƏƏT</span>
                    <span class="mt5-acc-value ${(account.profit || 0) >= 0 ? 'pnl-positive' : 'pnl-negative'}">${(account.profit || 0).toFixed(2)}</span>
                </div>
                <div class="mt5-acc-item">
                    <span class="mt5-acc-label">MARJIN</span>
                    <span class="mt5-acc-value">${(account.margin || 0).toFixed(2)}</span>
                </div>
            </div>
        `;
    },

    renderMT5Positions(positions) {
        const container = document.getElementById('botMT5Positions');
        if (!container) return;

        if (!positions || positions.length === 0) {
            container.innerHTML = '<div class="hud-empty">Açıq pozisiya yoxdur</div>';
            return;
        }

        container.innerHTML = `
            <table class="hud-table">
                <thead>
                    <tr><th>SİMVOL</th><th>TİP</th><th>HƏCM</th><th>GİRİŞ</th><th>P&L</th><th>ƏMƏLİYYAT</th></tr>
                </thead>
                <tbody>
                    ${positions.map(p => `
                        <tr>
                            <td>${p.symbol}</td>
                            <td><span class="trade-dir ${p.type === 0 ? 'trade-buy' : 'trade-sell'}">${p.type === 0 ? 'BUY' : 'SELL'}</span></td>
                            <td>${p.volume}</td>
                            <td>${p.price_open?.toFixed(5) || '--'}</td>
                            <td class="${(p.profit || 0) >= 0 ? 'pnl-positive' : 'pnl-negative'}">${(p.profit || 0).toFixed(2)}</td>
                            <td><button class="btn-bot btn-close-pos" onclick="BotManager.closeTrade(${p.ticket})">BAĞLA</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    renderSimulationResults(data) {
        const container = document.getElementById('botSimResults');
        if (!container) return;
        container.style.display = 'block';

        container.innerHTML = `
            <div class="sim-results">
                <h4 class="subsection-title">SİMULYASİYA NƏTİCƏLƏRİ</h4>
                <div class="sim-stats-grid">
                    <div class="sim-stat">
                        <span class="sim-stat-value">${data.signals?.length || 0}</span>
                        <span class="sim-stat-label">SİQNALLAR</span>
                    </div>
                    <div class="sim-stat">
                        <span class="sim-stat-value pnl-positive">${data.wins || 0}</span>
                        <span class="sim-stat-label">QAZANMA</span>
                    </div>
                    <div class="sim-stat">
                        <span class="sim-stat-value pnl-negative">${data.losses || 0}</span>
                        <span class="sim-stat-label">İTİRMƏ</span>
                    </div>
                    <div class="sim-stat">
                        <span class="sim-stat-value ${((data.total_pnl || 0) >= 0 ? 'pnl-positive' : 'pnl-negative')}">${(data.total_pnl || 0).toFixed(2)}</span>
                        <span class="sim-stat-label">CƏMİ P&L</span>
                    </div>
                </div>
                ${data.signals && data.signals.length > 0 ? `
                    <div class="sim-signals">
                        ${data.signals.map(s => `
                            <div class="sim-signal">
                                <span class="sim-signal-dir ${s.signal === 'BUY' ? 'trade-buy' : 'trade-sell'}">${s.signal}</span>
                                <span class="sim-signal-reason">${s.reason || ''}</span>
                                <span class="sim-signal-strength">${(s.strength * 100 || 0).toFixed(0)}%</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    },

    updateMT5Status(connected) {
        const indicator = document.getElementById('botMT5Status');
        const connectBtn = document.getElementById('botMT5ConnectBtn');
        if (indicator) {
            indicator.className = `mt5-status-indicator ${connected ? 'connected' : 'disconnected'}`;
            indicator.innerHTML = `
                <span class="status-dot"></span>
                <span>${connected ? 'QOŞULUB' : 'ƏLAQƏ YOXDUR'}</span>
            `;
        }
        if (connectBtn) {
            connectBtn.textContent = connected ? 'AYRIL' : 'QOŞUL';
            connectBtn.onclick = connected ? () => this.disconnectMT5() : () => this.connectMT5();
        }
    },

    // ==================== HELPERS ====================

    getStrategyName(strategyId) {
        const s = this.strategies.find(st => st.id === strategyId);
        return s ? s.name : 'Bilinmir';
    },

    clearCreateForm() {
        const fields = ['botName', 'botLotSize', 'botStopLoss', 'botTakeProfit', 'botTrailingStop', 'botMaxTrades', 'botMaxLoss', 'botRiskPerTrade'];
        fields.forEach(f => {
            const el = document.getElementById(f);
            if (el) el.value = '';
        });
    },

    showNotification(title, message, type = 'info') {
        const container = document.getElementById('botNotifications');
        if (!container) {
            // Fallback to console
            console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
            return;
        }

        const notif = document.createElement('div');
        notif.className = `bot-notification bot-notif-${type}`;
        notif.innerHTML = `
            <div class="notif-title">${title}</div>
            <div class="notif-message">${message}</div>
        `;
        container.appendChild(notif);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            notif.classList.add('notif-fade-out');
            setTimeout(() => notif.remove(), 500);
        }, 4000);
    },

    // ==================== WEBSOCKET HANDLERS ====================

    onTradeUpdate(data) {
        console.log('[BOT] Trade update:', data);
        this.showNotification('TİCARƏT', data.message || 'Yeni ticarət əməliyyatı', 'info');
        if (this.selectedBot) {
            this.loadTrades(this.selectedBot.id);
            this.getBotStatus(this.selectedBot.id);
        }
    },

    onStatusUpdate(data) {
        console.log('[BOT] Status update:', data);
        if (this.selectedBot && this.selectedBot.id === data.bot_id) {
            this.getBotStatus(data.bot_id);
        }
        this.loadBots();
    }
};

// ==================== TAB SWITCHING ====================

function switchBotTab(tabName) {
    // Hide all bot tabs
    document.querySelectorAll('.bot-tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    // Remove active from all tab buttons
    document.querySelectorAll('.bot-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    // Show selected tab
    const selectedTab = document.getElementById(`botTab-${tabName}`);
    if (selectedTab) selectedTab.style.display = 'block';
    // Activate button
    const activeBtn = document.querySelector(`.bot-tab-btn[data-tab="${tabName}"]`);
    if (activeBtn) activeBtn.classList.add('active');
}

// ==================== TOGGLE CREATE FORM ====================

function toggleBotCreateForm() {
    const form = document.getElementById('botCreateForm');
    if (!form) return;
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

// ==================== INIT ON MODULE SWITCH ====================

// When the user switches to the Bot module, initialize
const originalSwitchModule = window.switchModule;
window.switchModule = function(module) {
    if (module === 'bot') {
        // Call original switchModule logic first
        document.querySelectorAll('.module-panel').forEach(p => p.style.display = 'none');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const panel = document.getElementById('module-bot');
        if (panel) panel.style.display = 'block';
        const navItem = document.querySelector('.nav-item[data-module="bot"]');
        if (navItem) navItem.classList.add('active');
        // Initialize bot module
        BotManager.init();
    } else if (originalSwitchModule) {
        originalSwitchModule(module);
    }
};

// Override the original switchModule for bot module
const _origSwitch = window.switchModule;
window.switchModule = function(mod) {
    // Hide all panels
    document.querySelectorAll('.module-panel').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    // Show selected
    const panel = document.getElementById(`module-${mod}`);
    if (panel) panel.style.display = 'block';
    const nav = document.querySelector(`.nav-item[data-module="${mod}"]`);
    if (nav) nav.classList.add('active');

    // Init bot if needed
    if (mod === 'bot') {
        BotManager.init();
    }
};

console.log('[BOT] bot.js loaded successfully!');
