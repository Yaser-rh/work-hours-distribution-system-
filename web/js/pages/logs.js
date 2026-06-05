/* ==============================================================================
   Logs Page — System Logs & Diagnostics Dashboard
   ============================================================================== */

App.registerPage('logs', {
    logs: [],
    filterLevel: '',
    autoRefreshInterval: null,

    async render(container) {
        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">System Logs</h1>
                <div class="flex gap-8">
                    <button class="btn btn-ghost btn-sm" id="btnLogsClear" onclick="App.pages.logs.clearLogs()">
                        Clear Logs
                    </button>
                    <button class="btn btn-primary" onclick="App.pages.logs.loadLogs()">
                        🔄 Refresh
                    </button>
                </div>
            </div>
            
            <div class="filter-bar mb-16">
                <label class="form-label">Filter Level</label>
                <select class="form-select" id="logFilterLevel" onchange="App.pages.logs.changeFilter(this.value)" style="width:150px">
                    <option value="">All Levels</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                </select>
                
                <div style="display:flex;align-items:center;gap:8px;margin-left:auto;">
                    <input type="checkbox" id="logAutoRefresh" onchange="App.pages.logs.toggleAutoRefresh(this.checked)" style="accent-color:var(--accent-primary);width:16px;height:16px;">
                    <label for="logAutoRefresh" style="cursor:pointer;font-size:0.9rem;color:var(--text-primary)">Auto-refresh (5s)</label>
                </div>
            </div>
            
            <div class="card" style="flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden;padding:16px 20px;">
                <div class="logs-container" id="logsContainer" style="flex:1;overflow-y:auto;font-family:'Courier New', Courier, monospace;font-size:0.9rem;padding:8px 0;line-height:1.5;">
                    <div style="color:var(--text-secondary);text-align:center;padding:40px;">Loading logs...</div>
                </div>
            </div>
        `;

        this.loadLogs();
        
        // Handle interval cleanup when leaving page
        const originalNavigate = App.navigateTo;
        const self = this;
        App.navigateTo = function(page) {
            self.stopAutoRefresh();
            App.navigateTo = originalNavigate;
            App.navigateTo(page);
        };
    },

    async loadLogs() {
        try {
            this.logs = await App.api('/api/logs');
            this.renderLogsList();
        } catch (e) {
            App.toast('Failed to load logs: ' + e.message, 'error');
        }
    },

    renderLogsList() {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        let filtered = this.logs;
        if (this.filterLevel) {
            filtered = this.logs.filter(l => l.level === this.filterLevel);
        }

        if (filtered.length === 0) {
            container.innerHTML = `<div style="color:var(--text-secondary);text-align:center;padding:40px;">No logs recorded.</div>`;
            return;
        }

        // Render logs from newest to oldest
        container.innerHTML = filtered.map(log => {
            let color = 'var(--text-primary)';
            let labelClass = 'info';
            
            if (log.level === 'WARNING') {
                color = '#dd6b20';
                labelClass = 'warning';
            } else if (log.level === 'ERROR') {
                color = '#e53e3e';
                labelClass = 'danger';
            } else if (log.level === 'INFO') {
                color = 'var(--text-secondary)';
                labelClass = 'success';
            }

            return `
                <div class="log-item" style="border-bottom:1px solid var(--border-color);padding:8px 0;display:flex;gap:12px;align-items:flex-start;">
                    <span style="color:var(--text-secondary);white-space:nowrap;font-size:0.85rem;">[${log.timestamp}]</span>
                    <span class="badge badge-${labelClass}" style="width:70px;text-align:center;flex-shrink:0;">${log.level}</span>
                    <span style="color:${color};word-break:break-all;">${log.message}</span>
                </div>
            `;
        }).join('');
        
        // Scroll to the bottom of the container
        container.scrollTop = container.scrollHeight;
    },

    changeFilter(val) {
        this.filterLevel = val;
        this.renderLogsList();
    },

    async clearLogs() {
        App.confirmDialog(
            'Clear Logs?',
            'This will clear all logs from memory.',
            async () => {
                try {
                    await App.api('/api/logs/clear', { method: 'POST' });
                    App.toast('Logs cleared.', 'success');
                    this.loadLogs();
                } catch (e) {
                    App.toast('Failed to clear logs: ' + e.message, 'error');
                }
            },
            { danger: true }
        );
    },

    toggleAutoRefresh(checked) {
        if (checked) {
            this.autoRefreshInterval = setInterval(() => this.loadLogs(), 5000);
        } else {
            this.stopAutoRefresh();
        }
    },

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
});
