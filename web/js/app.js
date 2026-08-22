/* ==============================================================================
   App Core — Router, API Client, Theme Manager, Modal, Toast
   ============================================================================== */

const App = {
    currentPage: null,
    pages: {},

    // ---- Initialization ----
    init() {
        this.initTheme();
        this.initRouter();
    },

    // ---- Theme Manager ----
    initTheme() {
        const saved = localStorage.getItem('shiftplan-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
    },

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('shiftplan-theme', next);
        // Re-render current page to update charts
        if (this.currentPage && this.pages[this.currentPage] && this.pages[this.currentPage].onThemeChange) {
            this.pages[this.currentPage].onThemeChange();
        }
    },

    getTheme() {
        return document.documentElement.getAttribute('data-theme');
    },

    // ---- Router ----
    initRouter() {
        window.addEventListener('hashchange', () => this.route());
        this.route();
    },

    route() {
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        this.navigateTo(hash);
    },

    navigateTo(page) {
        this.currentPage = page;

        // Update nav active state
        document.querySelectorAll('.nav-item[data-page]').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Update breadcrumb (whitelist only — never interpolate the raw hash,
        // which would allow script injection via the URL fragment)
        const names = {
            dashboard: 'Dashboard',
            cities: 'Cities',
            drivers: 'Drivers',
            timesheets: 'Timesheets',
            'simple-generator': 'Simple Generator',
            analytics: 'Analytics',
            logs: 'System Logs',
            'user-guide': 'User Guide'
        };
        document.getElementById('breadcrumb').innerHTML =
            `<span class="breadcrumb-item">${names[page] || 'Dashboard'}</span>`;

        // Render page
        const container = document.getElementById('pageContainer');
        container.innerHTML = '';
        if (page === 'timesheets' || page === 'drivers' || page === 'analytics' || page === 'logs' || page === 'simple-generator') {
            container.className = 'page-container page-enter fixed-layout';
        } else {
            container.className = 'page-container page-enter';
        }

        if (this.pages[page] && this.pages[page].render) {
            this.pages[page].render(container);
        } else {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🚧</div><div class="empty-state-title">Page not found</div></div>`;
        }

        // Restore global solver UI if solving
        if (this.solver && this.solver.isSolving) {
            this.solver.updateUI();
        }
    },

    // ---- Global Solver Manager ----
    solver: {
        isSolving: false,
        startTime: 0,
        timeoutLimit: 30,
        timerInterval: null,
        timesheetIds: [],

        start(timesheetIds, timeoutLimit = 30) {
            this.isSolving = true;
            this.startTime = Date.now();
            this.timeoutLimit = timeoutLimit;
            this.timesheetIds = timesheetIds;

            const banner = document.getElementById('globalSolverBanner');
            if (banner) banner.classList.remove('hidden');

            if (this.timerInterval) clearInterval(this.timerInterval);
            this.updateUI();

            this.timerInterval = setInterval(() => {
                this.updateUI();
            }, 1000);
        },

        stop(result = null, error = null) {
            this.isSolving = false;
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }

            const banner = document.getElementById('globalSolverBanner');
            if (banner) banner.classList.add('hidden');

            if (error) {
                App.toast('Solver error: ' + (error.message || error), 'error');
            } else if (result) {
                if (result.status === 'failed') {
                    App.toast('Solver failed to find a feasible schedule.', 'error');
                } else {
                    App.toast(result.message || 'Solver completed successfully.', 'success', 6000);
                }
            }

            if (App.currentPage === 'timesheets' && App.pages.timesheets && App.pages.timesheets.loadTimesheets) {
                App.pages.timesheets.loadTimesheets();
                if (App.pages.timesheets.selectedTs) App.pages.timesheets.selectTimesheet(App.pages.timesheets.selectedTs);
            }
        },

        updateUI() {
            if (!this.isSolving) return;

            const elapsedSec = Math.floor((Date.now() - this.startTime) / 1000);
            const timerBadge = document.getElementById('globalSolverTimer');
            if (timerBadge) {
                const mm = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
                const ss = String(elapsedSec % 60).padStart(2, '0');
                timerBadge.textContent = `${mm}:${ss} / ${Math.round(this.timeoutLimit)}s`;
            }

            const fill = document.getElementById('globalProgressBarFill');
            if (fill) {
                const pct = Math.min(100, (elapsedSec / this.timeoutLimit) * 100);
                fill.style.width = `${pct}%`;
            }

            if (App.currentPage === 'timesheets') {
                const btn = document.getElementById('tsDistributeBtn');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = `⏳ Solving... (${elapsedSec}s)`;
                }
                const p1 = document.getElementById('tsSolverProgress');
                const p2 = document.getElementById('tsListSolverProgress');
                if (p1) p1.classList.remove('hidden');
                if (p2) p2.classList.remove('hidden');
            }
        }
    },

    // ---- Global Export Preferences Manager ----
    getExportConfig() {
        return {
            remember: localStorage.getItem('shiftplan_remember_dir') === 'true',
            format: localStorage.getItem('shiftplan_export_format') || 'docx',
            dir: localStorage.getItem('shiftplan_export_dir') || ''
        };
    },

    setExportConfig(config) {
        if (config.remember !== undefined) localStorage.setItem('shiftplan_remember_dir', config.remember ? 'true' : 'false');
        if (config.format) localStorage.setItem('shiftplan_export_format', config.format);
        if (config.dir !== undefined) localStorage.setItem('shiftplan_export_dir', config.dir);
    },

    toggleRememberDir(remember) {
        this.setExportConfig({ remember: !!remember });
        const textEl = document.getElementById('rememberStatusHint');
        if (textEl) {
            textEl.textContent = remember
                ? 'Slid RIGHT: Saved directory will be remembered automatically for all exports.'
                : 'Slid LEFT: Ask for format & location each time.';
        }
        App.toast(remember ? 'Save location will be remembered.' : 'Will ask save location each time.', 'info');
    },

    promptChangeDir(callback) {
        const current = this.getExportConfig().dir;
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Set Save Directory</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <p style="color:var(--text-secondary);margin-bottom:12px;">Specify the absolute folder path on your computer where exports will be saved (e.g. <code>C:\\Users\\Username\\Downloads</code>):</p>
                <input class="form-input" id="inputCustomDir" value="${current}" placeholder="e.g. C:\\Users\\Username\\Desktop\\Exports">
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="btnSaveDir">Save Location</button>
            </div>
        `);

        document.getElementById('btnSaveDir').addEventListener('click', () => {
            const val = document.getElementById('inputCustomDir').value.trim();
            this.setExportConfig({ dir: val });
            App.closeModal();
            App.toast(val ? `Save directory set to: ${val}` : 'Reset to default downloads folder.', 'success');
            if (typeof callback === 'function') callback(val);
        });
    },

    registerPage(name, handler) {
        this.pages[name] = handler;
    },

    // ---- API Client ----
    async api(path, options = {}) {
        const { method = 'GET', body, params } = options;
        let url = path;
        if (params) {
            const qs = new URLSearchParams();
            Object.entries(params).forEach(([k, v]) => {
                if (v !== null && v !== undefined && v !== '') qs.append(k, v);
            });
            const qsStr = qs.toString();
            if (qsStr) url += '?' + qsStr;
        }

        const fetchOpts = { method, headers: {} };
        // Per-session token required by the server on all mutating routes
        if (window.AUTH_TOKEN) fetchOpts.headers['X-Auth-Token'] = window.AUTH_TOKEN;
        if (body) {
            fetchOpts.headers['Content-Type'] = 'application/json';
            fetchOpts.body = JSON.stringify(body);
        }

        const res = await fetch(url, fetchOpts);
        if (res.headers.get('content-type')?.includes('application/json')) {
            const data = await res.json();
            if (!res.ok && data.error) {
                throw new Error(data.error);
            }
            return data;
        }
        // Handle file downloads
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res;
    },

    // ---- Input normalization helpers ----
    // Interprets loose time input and returns a valid "HH:MM" string, or null.
    // Accepts typos: "900" -> "09:00", "0930" -> "09:30", "9,30"/"9.30" -> "09:30".
    normalizeTimeInput(raw) {
        const s = String(raw ?? '').trim().replace(/[.,]/g, ':').replace(/[^0-9:]/g, '');
        if (!s) return null;
        let h, m = '00';
        const idx = s.indexOf(':');
        if (idx === -1) {
            if (s.length <= 2) h = s;                                  // "9" / "14" -> top of the hour
            else if (s.length === 3) { h = s.slice(0, 1); m = s.slice(1); }  // "930" -> 9:30
            else if (s.length === 4) { h = s.slice(0, 2); m = s.slice(2); }  // "0930" -> 09:30
            else return null;
        } else {
            h = s.slice(0, idx);
            m = s.slice(idx + 1) || '00';
        }
        if (h === '' || h.length > 2 || m.length > 2) return null;
        const hh = parseInt(h, 10), mm = parseInt(m, 10);
        if (isNaN(hh) || isNaN(mm) || hh < 0 || hh > 23 || mm < 0 || mm > 59) return null;
        return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
    },

    // Returns the parsed number if it is numeric and within [min, max], else null.
    validateHoursInput(raw, min, max) {
        const v = parseFloat(String(raw ?? '').replace(',', '.'));
        if (isNaN(v) || v < min || v > max) return null;
        return v;
    },

    // ---- Modal ----
    openModal(html, options = {}) {
        const overlay = document.getElementById('modalOverlay');
        const content = document.getElementById('modalContent');
        content.className = 'modal' + (options.wide ? ' wide' : '');
        content.innerHTML = html;
        overlay.classList.add('visible');
    },

    closeModal() {
        const overlay = document.getElementById('modalOverlay');
        overlay.classList.remove('visible');
    },

    confirmDialog(title, message, onConfirm, options = {}) {
        const type = options.danger ? 'danger' : 'info';
        const icon = options.danger ? '⚠' : 'ℹ';
        const btnClass = options.danger ? 'btn-danger' : 'btn-primary';
        const btnText = options.confirmText || 'Confirm';

        this.openModal(`
            <div class="modal-body" style="padding-top:32px;">
                <div class="confirm-icon ${type}">${icon}</div>
                <div style="text-align:center;font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:8px;">${title}</div>
                <div class="confirm-text">${message}</div>
                <div style="display:flex;gap:8px;justify-content:center;">
                    <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                    <button class="btn ${btnClass}" id="confirmBtn">${btnText}</button>
                </div>
            </div>
        `);
        document.getElementById('confirmBtn').addEventListener('click', () => {
            App.closeModal();
            onConfirm();
        });
    },

    // ---- Toast Notifications ----
    toast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toastContainer');
        const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || 'ℹ'}</div>
            <div style="flex:1">${message}</div>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    // ---- Database Tools ----
    async backupDatabase() {
        try {
            const result = await this.api('/api/database/backup', { method: 'POST', body: {} });
            this.toast(`Database backed up successfully.`, 'success');
        } catch (e) {
            this.toast(`Backup failed: ${e.message}`, 'error');
        }
    },

    // ---- Utility: format date ----
    formatDate(dateStr) {
        if (!dateStr) return '';
        if (dateStr.includes('-')) {
            const [y, m, d] = dateStr.split('-');
            return `${d}.${m}.${y}`;
        }
        return dateStr;
    },

    // Utility: get day of week name
    getDayName(dateStr, year, month) {
        try {
            let d;
            if (dateStr.includes('-')) {
                d = new Date(dateStr);
            } else {
                const parts = dateStr.split('.');
                d = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
            }
            return d.toLocaleDateString('en', { weekday: 'short' });
        } catch {
            return '';
        }
    },

    isWeekend(dateStr) {
        try {
            let d;
            if (dateStr.includes('-')) {
                d = new Date(dateStr);
            } else {
                const parts = dateStr.split('.');
                d = new Date(parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]));
            }
            const day = d.getDay();
            return day === 0 || day === 6;
        } catch {
            return false;
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
