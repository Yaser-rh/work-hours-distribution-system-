/* ==============================================================================
   Dashboard Page
   ============================================================================== */

App.registerPage('dashboard', {
    async render(container) {
        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Dashboard</h1>
            </div>
            <div class="kpi-grid" id="kpiGrid">
                <div class="card kpi-card"><div class="kpi-icon blue">🏙️</div><div><div class="kpi-value" id="kpiCities">—</div><div class="kpi-label">Active Cities</div></div></div>
                <div class="card kpi-card"><div class="kpi-icon green">👤</div><div><div class="kpi-value" id="kpiDrivers">—</div><div class="kpi-label">Drivers</div></div></div>
                <div class="card kpi-card"><div class="kpi-icon blue">📋</div><div><div class="kpi-value" id="kpiTimesheets">—</div><div class="kpi-label">Timesheets</div></div></div>
                <div class="card kpi-card"><div class="kpi-icon amber">✅</div><div><div class="kpi-value" id="kpiFinalized">—</div><div class="kpi-label">Finalized</div></div></div>
            </div>
            <div class="dash-grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Recent Timesheets</span>
                    </div>
                    <div class="recent-list" id="recentList">
                        <div class="empty-state" style="padding:40px"><div class="empty-state-text">Loading...</div></div>
                    </div>
                </div>
                <div>
                    <div class="card" style="margin-bottom:16px">
                        <div class="card-header"><span class="card-title">Quick Actions</span></div>
                        <div class="card-body">
                            <div class="quick-actions">
                                <button class="quick-action-btn" onclick="location.hash='timesheets'">
                                    <span>📋</span> <span>New Timesheets</span>
                                </button>
                                <button class="quick-action-btn" onclick="location.hash='timesheets'">
                                    <span>⚡</span> <span>Distribute Schedules</span>
                                </button>
                                <button class="quick-action-btn" onclick="location.hash='analytics'">
                                    <span>📊</span> <span>View Analytics</span>
                                </button>
                                <button class="quick-action-btn" onclick="App.backupDatabase()">
                                    <span>💾</span> <span>Backup Database</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadStats();
    },

    async loadStats() {
        try {
            const stats = await App.api('/api/dashboard/stats');

            // Animate counters
            this.animateCounter('kpiCities', stats.city_count);
            this.animateCounter('kpiDrivers', stats.driver_count);
            this.animateCounter('kpiTimesheets', stats.timesheet_count);
            this.animateCounter('kpiFinalized', stats.finalized_count);

            // Render recent timesheets
            const list = document.getElementById('recentList');
            if (!stats.recent || stats.recent.length === 0) {
                list.innerHTML = `<div class="empty-state" style="padding:40px"><div class="empty-state-icon">📋</div><div class="empty-state-text">No timesheets yet. Go to Timesheets to create one.</div></div>`;
                return;
            }

            list.innerHTML = stats.recent.map(ts => `
                <div class="recent-item" onclick="location.hash='timesheets'">
                    <div>
                        <div class="recent-item-name">${ts.employee_name}</div>
                        <div class="recent-item-meta">${ts.city_name} · ${String(ts.month).padStart(2,'0')}/${ts.year} · ${ts.target_hours}h</div>
                    </div>
                    <span class="badge badge-${ts.status.toLowerCase()}">${ts.status}</span>
                </div>
            `).join('');

        } catch (e) {
            console.error('Dashboard load error:', e);
        }
    },

    animateCounter(elementId, target) {
        const el = document.getElementById(elementId);
        if (!el) return;
        const duration = 600;
        const start = performance.now();
        const from = 0;

        function step(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(from + (target - from) * eased);
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }
});
