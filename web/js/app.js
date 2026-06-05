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

        // Update breadcrumb
        const names = {
            dashboard: 'Dashboard',
            cities: 'Cities',
            drivers: 'Drivers',
            timesheets: 'Timesheets',
            analytics: 'Analytics',
            logs: 'System Logs'
        };
        document.getElementById('breadcrumb').innerHTML =
            `<span class="breadcrumb-item">${names[page] || page}</span>`;

        // Render page
        const container = document.getElementById('pageContainer');
        container.innerHTML = '';
        if (page === 'timesheets' || page === 'drivers' || page === 'analytics' || page === 'logs') {
            container.className = 'page-container page-enter fixed-layout';
        } else {
            container.className = 'page-container page-enter';
        }

        if (this.pages[page] && this.pages[page].render) {
            this.pages[page].render(container);
        } else {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🚧</div><div class="empty-state-title">Page not found</div></div>`;
        }
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
