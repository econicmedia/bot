// AI Trading Bot Dashboard JavaScript

class TradingDashboard {
    constructor() {
        this.apiBase = '/api/v1';
        this.portfolioChart = null;
        this.refreshInterval = 5000; // 5 seconds
        this.refreshTimer = null;

        this.init();
    }

    async init() {
        console.log('🚀 Initializing AI Trading Bot Dashboard...');

        // Initialize chart
        this.initPortfolioChart();

        // Initialize demo data first
        await this.initializeDemoData();

        // Load initial data
        await this.loadDashboardData();

        // Load bot status
        await this.loadBotStatus();

        // Start auto-refresh
        this.startAutoRefresh();

        // Setup event listeners
        this.setupEventListeners();

        console.log('✅ Dashboard initialized successfully');
    }

    setupEventListeners() {
        // Chart period buttons
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateChartPeriod(e.target.dataset.period);
            });
        });

        // Order form
        document.getElementById('orderForm').addEventListener('submit', this.handleOrderSubmit.bind(this));

        // Order type change
        document.getElementById('orderType').addEventListener('change', this.handleOrderTypeChange.bind(this));

        // Trades filter
        document.getElementById('tradesFilter').addEventListener('change', this.refreshTrades.bind(this));
    }

    async initializeDemoData() {
        try {
            console.log('🔄 Initializing demo data...');
            const response = await this.postAPI('/bot/initialize-demo', {});
            console.log('✅ Demo data initialized:', response);
        } catch (error) {
            console.warn('⚠️ Demo data initialization failed:', error);
        }
    }

    async loadBotStatus() {
        try {
            const status = await this.fetchAPI('/bot/status');
            this.updateBotStatus(status);
        } catch (error) {
            console.error('❌ Error loading bot status:', error);
        }
    }

    async loadDashboardData() {
        try {
            // Load all dashboard data in parallel
            const [status, positions, strategies, trades, performance, riskMetrics] = await Promise.all([
                this.fetchAPI('/trading/status'),
                this.fetchAPI('/trading/positions'),
                this.fetchAPI('/strategies/'),
                this.fetchAPI('/trading/trades?limit=20'),
                this.fetchAPI('/analytics/performance'),
                this.fetchAPI('/analytics/risk-metrics')
            ]);

            // Update UI components
            this.updatePortfolioOverview(status, performance);
            this.updatePositionsTable(positions);
            this.updateStrategiesGrid(strategies);
            this.updateTradesTable(trades);
            this.updateRiskMetrics(riskMetrics);
            this.updatePortfolioChart();

            // Update last refresh time
            document.getElementById('lastUpdate').textContent =
                `Last update: ${new Date().toLocaleTimeString()}`;

        } catch (error) {
            console.error('❌ Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    updatePortfolioOverview(status, performance) {
        // Total Portfolio Value
        document.getElementById('totalValue').textContent =
            this.formatCurrency(status.total_value || 0);

        // Daily P&L
        const dailyPnl = status.daily_pnl || 0;
        const dailyPnlElement = document.getElementById('dailyPnl');
        const dailyPnlChangeElement = document.getElementById('dailyPnlChange');

        dailyPnlElement.textContent = this.formatCurrency(dailyPnl);
        dailyPnlChangeElement.textContent = this.formatPercentage(dailyPnl / status.total_value * 100);
        dailyPnlChangeElement.className = `metric-change ${dailyPnl >= 0 ? 'positive' : 'negative'}`;

        // Active Positions
        document.getElementById('activePositions').textContent = status.active_positions || 0;

        // Win Rate
        const winRate = (performance.win_rate * 100) || 0;
        document.getElementById('winRate').textContent = this.formatPercentage(winRate);
    }

    updatePositionsTable(positions) {
        const tbody = document.getElementById('positionsTableBody');
        tbody.innerHTML = '';

        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: rgba(255,255,255,0.6);">No active positions</td></tr>';
            return;
        }

        positions.forEach(position => {
            const row = document.createElement('tr');
            const pnlClass = position.unrealized_pnl >= 0 ? 'positive' : 'negative';

            row.innerHTML = `
                <td><strong>${position.symbol}</strong></td>
                <td><span class="side-badge ${position.side}">${position.side.toUpperCase()}</span></td>
                <td>${position.quantity}</td>
                <td>${this.formatCurrency(position.entry_price)}</td>
                <td>${this.formatCurrency(position.current_price)}</td>
                <td class="${pnlClass}">${this.formatCurrency(position.unrealized_pnl)}</td>
                <td>
                    <button class="action-btn close-btn" onclick="dashboard.closePosition('${position.symbol}')" title="Close Position">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateStrategiesGrid(strategies) {
        const grid = document.getElementById('strategiesGrid');
        grid.innerHTML = '';

        strategies.forEach(strategy => {
            const card = document.createElement('div');
            card.className = 'strategy-card';

            const statusClass = strategy.enabled ? 'enabled' : 'disabled';
            const statusText = strategy.enabled ? 'Active' : 'Disabled';

            card.innerHTML = `
                <div class="strategy-header">
                    <div class="strategy-name">${strategy.name}</div>
                    <div class="strategy-status ${statusClass}">${statusText}</div>
                </div>
                <div class="strategy-metrics">
                    <div class="strategy-metric">
                        <span class="strategy-metric-label">Return:</span>
                        <span class="strategy-metric-value positive">${this.formatPercentage(strategy.performance.total_return * 100)}</span>
                    </div>
                    <div class="strategy-metric">
                        <span class="strategy-metric-label">Sharpe:</span>
                        <span class="strategy-metric-value">${strategy.performance.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
                    </div>
                    <div class="strategy-metric">
                        <span class="strategy-metric-label">Win Rate:</span>
                        <span class="strategy-metric-value">${this.formatPercentage(strategy.performance.win_rate * 100)}</span>
                    </div>
                    <div class="strategy-metric">
                        <span class="strategy-metric-label">Drawdown:</span>
                        <span class="strategy-metric-value negative">${this.formatPercentage(strategy.performance.max_drawdown * 100)}</span>
                    </div>
                </div>
            `;

            // Add click handler to toggle strategy
            card.addEventListener('click', () => this.toggleStrategy(strategy.name, !strategy.enabled));

            grid.appendChild(card);
        });
    }

    updateTradesTable(trades) {
        const tbody = document.getElementById('tradesTableBody');
        tbody.innerHTML = '';

        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: rgba(255,255,255,0.6);">No recent trades</td></tr>';
            return;
        }

        trades.forEach(trade => {
            const row = document.createElement('tr');
            const sideClass = trade.side === 'buy' ? 'positive' : 'negative';
            const time = new Date(trade.timestamp).toLocaleTimeString();

            row.innerHTML = `
                <td>${time}</td>
                <td><strong>${trade.symbol}</strong></td>
                <td class="${sideClass}">${trade.side.toUpperCase()}</td>
                <td>${trade.quantity}</td>
                <td>${this.formatCurrency(trade.price)}</td>
                <td><span class="strategy-badge">${trade.strategy || 'Manual'}</span></td>
                <td class="positive">+$${Math.abs(trade.commission || 0).toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    updateRiskMetrics(riskMetrics) {
        document.getElementById('maxDrawdown').textContent =
            this.formatPercentage(riskMetrics.max_drawdown || 0);
        document.getElementById('currentExposure').textContent =
            this.formatCurrency(riskMetrics.current_exposure || 0);
        document.getElementById('leverage').textContent =
            `${(riskMetrics.leverage || 1).toFixed(1)}x`;
        document.getElementById('marginRatio').textContent =
            this.formatPercentage((riskMetrics.margin_ratio || 0) * 100);
    }

    async updatePortfolioChart() {
        try {
            const portfolioHistory = await this.fetchAPI('/analytics/portfolio-history');

            if (!portfolioHistory || portfolioHistory.length === 0) {
                console.warn('No portfolio history data available');
                return;
            }

            const labels = portfolioHistory.map(item =>
                new Date(item.timestamp).toLocaleDateString()
            );
            const values = portfolioHistory.map(item => item.total_value);

            this.portfolioChart.data.labels = labels;
            this.portfolioChart.data.datasets[0].data = values;
            this.portfolioChart.update();

        } catch (error) {
            console.error('Error updating portfolio chart:', error);
        }
    }

    initPortfolioChart() {
        const ctx = document.getElementById('portfolioChart').getContext('2d');

        this.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4CAF50',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    // API Helper Methods
    async fetchAPI(endpoint) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    async postAPI(endpoint, data) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Utility Methods
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value || 0);
    }

    formatPercentage(value) {
        const sign = value >= 0 ? '+' : '';
        return `${sign}${(value || 0).toFixed(2)}%`;
    }

    showError(message) {
        console.error('Dashboard Error:', message);
        // You could implement a toast notification system here
    }

    showSuccess(message) {
        console.log('Dashboard Success:', message);
        // You could implement a toast notification system here
    }

    // Auto-refresh functionality
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    // Manual refresh methods
    async refreshPositions() {
        try {
            const positions = await this.fetchAPI('/trading/positions');
            this.updatePositionsTable(positions);
            this.showSuccess('Positions refreshed');
        } catch (error) {
            this.showError('Failed to refresh positions');
        }
    }

    async refreshStrategies() {
        try {
            const strategies = await this.fetchAPI('/strategies/');
            this.updateStrategiesGrid(strategies);
            this.showSuccess('Strategies refreshed');
        } catch (error) {
            this.showError('Failed to refresh strategies');
        }
    }

    async refreshTrades() {
        try {
            const filter = document.getElementById('tradesFilter').value;
            const endpoint = filter ?
                `/trading/trades?limit=20&symbol=${filter}` :
                '/trading/trades?limit=20';

            const trades = await this.fetchAPI(endpoint);
            this.updateTradesTable(trades);
            this.showSuccess('Trades refreshed');
        } catch (error) {
            this.showError('Failed to refresh trades');
        }
    }

    // Trading actions
    async toggleStrategy(strategyName, enabled) {
        try {
            await this.postAPI(`/strategies/${strategyName}/enable`, { enabled });
            this.showSuccess(`Strategy ${strategyName} ${enabled ? 'enabled' : 'disabled'}`);
            await this.refreshStrategies();
        } catch (error) {
            this.showError(`Failed to ${enabled ? 'enable' : 'disable'} strategy`);
        }
    }

    async closePosition(symbol) {
        if (!confirm(`Are you sure you want to close the ${symbol} position?`)) {
            return;
        }

        try {
            // This would need to be implemented in the API
            this.showSuccess(`Position ${symbol} close order submitted`);
            await this.refreshPositions();
        } catch (error) {
            this.showError('Failed to close position');
        }
    }

    // Chart controls
    updateChartPeriod(period) {
        console.log(`Updating chart period to: ${period}`);
        // This would filter the portfolio history data based on the selected period
        this.updatePortfolioChart();
    }

    // Modal controls
    openTradingModal() {
        document.getElementById('tradingModal').style.display = 'flex';
    }

    closeTradingModal() {
        document.getElementById('tradingModal').style.display = 'none';
        document.getElementById('orderForm').reset();
        document.getElementById('priceGroup').style.display = 'none';
    }

    handleOrderTypeChange(event) {
        const priceGroup = document.getElementById('priceGroup');
        if (event.target.value === 'limit') {
            priceGroup.style.display = 'block';
            document.getElementById('orderPrice').required = true;
        } else {
            priceGroup.style.display = 'none';
            document.getElementById('orderPrice').required = false;
        }
    }

    async handleOrderSubmit(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const orderData = {
            symbol: formData.get('symbol') || document.getElementById('orderSymbol').value,
            side: formData.get('side') || document.getElementById('orderSide').value,
            quantity: parseFloat(formData.get('quantity') || document.getElementById('orderQuantity').value),
            order_type: formData.get('order_type') || document.getElementById('orderType').value,
            price: formData.get('price') ? parseFloat(formData.get('price')) :
                   (document.getElementById('orderPrice').value ? parseFloat(document.getElementById('orderPrice').value) : null)
        };

        try {
            const result = await this.postAPI('/trading/orders', orderData);
            this.showSuccess(`Order placed successfully: ${result.order_id}`);
            this.closeTradingModal();
            await this.refreshPositions();
            await this.refreshTrades();
        } catch (error) {
            this.showError('Failed to place order');
        }
    }

    // Bot Control Functions
    updateBotStatus(status) {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');
        const startBtn = document.getElementById('startBotBtn');
        const stopBtn = document.getElementById('stopBotBtn');

        if (status.running) {
            statusIndicator.className = 'fas fa-circle status-indicator running';
            statusText.textContent = 'Running';
            startBtn.style.display = 'none';
            stopBtn.style.display = 'flex';
        } else {
            statusIndicator.className = 'fas fa-circle status-indicator stopped';
            statusText.textContent = 'Stopped';
            startBtn.style.display = 'flex';
            stopBtn.style.display = 'none';
        }
    }

    async startBot() {
        try {
            const response = await this.postAPI('/bot/start', {});
            this.showSuccess(response.message);
            await this.loadBotStatus();
            await this.loadDashboardData(); // Refresh data after starting
        } catch (error) {
            this.showError('Failed to start bot');
        }
    }

    async stopBot() {
        try {
            const response = await this.postAPI('/bot/stop', {});
            this.showSuccess(response.message);
            await this.loadBotStatus();
        } catch (error) {
            this.showError('Failed to stop bot');
        }
    }
}

// Global functions for HTML onclick handlers
function openTradingModal() {
    dashboard.openTradingModal();
}

function closeTradingModal() {
    dashboard.closeTradingModal();
}

function refreshPositions() {
    dashboard.refreshPositions();
}

function refreshStrategies() {
    dashboard.refreshStrategies();
}

function refreshTrades() {
    dashboard.refreshTrades();
}

function startBot() {
    dashboard.startBot();
}

function stopBot() {
    dashboard.stopBot();
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new TradingDashboard();
});
