/* ==============================================================================
   Timesheets Page — Core Workflow
   ============================================================================== */

App.registerPage('timesheets', {
    timesheets: [],
    selectedTs: null,
    selectedIds: new Set(),
    cities: [],
    drivers: [],
    editingRow: null,
    activeTab: 'Draft',

    async render(container) {
        // Pre-load cities and drivers
        this.cities = await App.api('/api/cities');
        this.drivers = await App.api('/api/drivers');

        const cityOptions = this.cities.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        const now = new Date();
        const curMonth = now.getMonth() + 1;
        const curYear = now.getFullYear();

        const isDraftActive = this.activeTab === 'Draft';
        const isFinalizedActive = this.activeTab === 'Finalized';

        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Timesheets</h1>
                <button class="btn btn-primary" onclick="App.pages.timesheets.openNewModal()">
                    <span>+</span> New Timesheets
                </button>
            </div>
            <div class="filter-bar mb-16">
                <label class="form-label">City</label>
                <select class="form-select" id="tsFilterCity" onchange="App.pages.timesheets.loadTimesheets()">
                    <option value="">All Cities</option>
                    ${cityOptions}
                </select>
                <label class="form-label">Month</label>
                <select class="form-select" id="tsFilterMonth" onchange="App.pages.timesheets.loadTimesheets()" style="width:130px">
                    <option value="">All Months</option>
                    ${Array.from({length:12}, (_,i) => `<option value="${i+1}" ${i+1===curMonth?'selected':''}>${new Date(2000, i).toLocaleString('en', {month:'long'})}</option>`).join('')}
                </select>
                <label class="form-label">Year</label>
                <select class="form-select" id="tsFilterYear" onchange="App.pages.timesheets.loadTimesheets()" style="width:100px">
                    <option value="">All Years</option>
                    <option value="${curYear}" selected>${curYear}</option>
                    <option value="${curYear+1}">${curYear+1}</option>
                </select>
                <label class="form-label">Timeout</label>
                <select class="form-select" id="tsTimeoutLimit" style="width:100px">
                    <option value="10">10s</option>
                    <option value="20">20s</option>
                    <option value="30" selected>30s</option>
                    <option value="60">60s</option>
                    <option value="120">120s</option>
                    <option value="180">180s</option>
                </select>
            </div>
            <div class="ts-layout">
                <div class="card ts-list-panel">
                    <div class="ts-tabs">
                        <button class="ts-tab ${isDraftActive ? 'active' : ''}" data-tab="Draft" onclick="App.pages.timesheets.changeTab('Draft')">Drafts</button>
                        <button class="ts-tab ${isFinalizedActive ? 'active' : ''}" data-tab="Finalized" onclick="App.pages.timesheets.changeTab('Finalized')">Finalized</button>
                    </div>
                    <div class="select-all-bar">
                        <input type="checkbox" id="tsSelectAll" onchange="App.pages.timesheets.toggleSelectAll()" style="accent-color:var(--accent-primary)">
                        <label for="tsSelectAll" style="cursor:pointer">Select All</label>
                        <span class="ml-auto text-sm" id="tsSelectedCount"></span>
                    </div>
                    <div class="ts-list-scroll" id="tsList"></div>
                    <div class="ts-list-actions">
                        <div id="tsListSolverProgress" class="hidden mb-12">
                            <div class="solver-progress"><div class="solver-progress-bar"></div></div>
                            <div class="text-xs text-secondary text-center" style="margin-top: 4px;">Solver is running...</div>
                        </div>
                        <button class="btn btn-primary w-full" id="tsDistributeBtn" onclick="App.pages.timesheets.distributeSelected()">
                            ⚡ Distribute Selected
                        </button>
                        <div class="flex gap-8">
                            <button class="btn btn-success w-full btn-sm" onclick="App.pages.timesheets.finalizeSelected()">✅ Finalize</button>
                            <button class="btn btn-ghost w-full btn-sm" onclick="App.pages.timesheets.revertSelected()">↩️ Revert</button>
                        </div>
                        <div class="flex gap-8">
                            <button class="btn btn-ghost w-full btn-sm" onclick="App.pages.timesheets.exportSelected()">📄 Export</button>
                            <button class="btn btn-ghost w-full btn-sm" style="color:var(--accent-danger)" onclick="App.pages.timesheets.deleteSelected()">🗑 Delete</button>
                        </div>
                    </div>
                </div>
                <div class="card ts-detail-panel" id="tsDetail">
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <div class="empty-state-title">No Timesheet Selected</div>
                        <div class="empty-state-text">Select a timesheet from the list to view and edit the daily schedule.</div>
                    </div>
                </div>
            </div>
        `;

        this.selectedTs = null;
        this.selectedIds = new Set();
        await this.loadTimesheets();
    },

    async loadTimesheets() {
        const cityId = document.getElementById('tsFilterCity')?.value || '';
        const month = document.getElementById('tsFilterMonth')?.value || '';
        const year = document.getElementById('tsFilterYear')?.value || '';
        const status = this.activeTab;

        let params = {};
        if (cityId) params.city_id = cityId;
        if (status) params.status = status;
        if (month) params.month = parseInt(month);
        if (year) params.year = parseInt(year);

        try {
            this.timesheets = await App.api('/api/timesheets', { params });
            this.renderList();
        } catch (e) {
            App.toast('Failed to load timesheets: ' + e.message, 'error');
        }
    },

    changeTab(tab) {
        this.activeTab = tab;
        document.querySelectorAll('.ts-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        this.selectedIds.clear();
        this.selectedTs = null;
        const detail = document.getElementById('tsDetail');
        if (detail) {
            detail.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-title">No Timesheet Selected</div>
                    <div class="empty-state-text">Select a timesheet from the list to view and edit the daily schedule.</div>
                </div>
            `;
        }
        this.loadTimesheets();
    },

    renderList() {
        const list = document.getElementById('tsList');
        if (!list) return;

        if (!this.timesheets || this.timesheets.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="padding:40px">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-title">No timesheets found</div>
                    <div class="empty-state-text">Create new timesheets or change filters.</div>
                </div>
            `;
            this.updateSelectedCount();
            return;
        }

        list.innerHTML = this.timesheets.map(ts => {
            const pct = ts.target_hours > 0 ? Math.min(100, ((ts.actual_hours || 0) / ts.target_hours) * 100) : 0;
            const isChecked = this.selectedIds.has(ts.id);
            const isActive = this.selectedTs === ts.id;

            return `
                <div class="ts-list-item ${isActive ? 'active' : ''}" data-ts-id="${ts.id}">
                    <input type="checkbox" class="ts-checkbox" ${isChecked ? 'checked' : ''} 
                           onchange="App.pages.timesheets.toggleCheck(${ts.id}, this.checked)"
                           onclick="event.stopPropagation()">
                    <div class="ts-item-info" onclick="App.pages.timesheets.selectTimesheet(${ts.id})">
                        <div class="ts-item-name">${ts.employee_name}</div>
                        <div class="ts-item-meta">
                            <span>${ts.target_hours}h</span>
                            <span>·</span>
                            <span class="badge badge-${ts.status.toLowerCase()}">${ts.status}</span>
                            ${ts.is_distribution_locked ? '<span class="badge badge-locked">🔒</span>' : ''}
                        </div>
                        <div class="ts-progress-bar">
                            <div class="ts-progress-fill" style="width:${pct}%;background:${pct >= 100 ? 'var(--accent-success)' : 'var(--accent-primary)'}"></div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.updateSelectedCount();
    },

    toggleCheck(id, checked) {
        if (checked) this.selectedIds.add(id);
        else this.selectedIds.delete(id);
        this.updateSelectedCount();
    },

    toggleSelectAll() {
        const checkAll = document.getElementById('tsSelectAll')?.checked;
        this.selectedIds.clear();
        if (checkAll) {
            this.timesheets.forEach(ts => this.selectedIds.add(ts.id));
        }
        this.renderList();
    },

    updateSelectedCount() {
        const el = document.getElementById('tsSelectedCount');
        if (el) el.textContent = this.selectedIds.size > 0 ? `${this.selectedIds.size} selected` : '';
    },

    async selectTimesheet(id) {
        this.selectedTs = id;
        this.isEditingAll = false; // Reset editing mode
        // Re-highlight in list
        document.querySelectorAll('.ts-list-item').forEach(el => {
            el.classList.toggle('active', parseInt(el.dataset.tsId) === id);
        });

        const detail = document.getElementById('tsDetail');
        detail.innerHTML = `<div class="empty-state"><div class="empty-state-text">Loading schedule...</div></div>`;

        try {
            const ts = await App.api(`/api/timesheets/${id}`);
            this.activeTsDetail = ts;
            this.renderDetail(ts);
        } catch (e) {
            detail.innerHTML = `<div class="empty-state"><div class="empty-state-text" style="color:var(--accent-danger)">Failed to load.</div></div>`;
        }
    },

    renderDetail(ts) {
        const detail = document.getElementById('tsDetail');
        const actualHours = ts.entries.reduce((s, e) => s + e.hours_worked, 0);
        const isDraft = ts.status === 'Draft';
        const canEdit = isDraft && !ts.is_distribution_locked;

        detail.innerHTML = `
            <div class="ts-detail-header">
                <div class="ts-detail-title">${ts.employee_name} · ${ts.city_name} · ${String(ts.month).padStart(2,'0')}/${ts.year}</div>
                <div class="ts-detail-meta">
                    <span>Target: <strong>${ts.target_hours}h</strong></span>
                    <span>Actual: <strong>${actualHours.toFixed(1)}h</strong></span>
                    <span>Status: <span class="badge badge-${ts.status.toLowerCase()}">${ts.status}</span></span>
                    ${ts.is_distribution_locked ? '<span class="badge badge-locked">🔒 Locked</span>' : ''}
                </div>
            </div>
            <div id="tsSolverProgress" class="hidden" style="padding:0 22px;"><div class="solver-progress"><div class="solver-progress-bar"></div></div><div class="text-sm text-secondary" style="padding:4px 0">Solver is running...</div></div>
            <div class="ts-grid-container">
                <table class="schedule-table data-table" id="scheduleTable">
                    <thead><tr>
                        <th>Date</th><th>Day</th><th>Start</th><th>End</th><th>Break</th><th>Hours</th><th>Remarks</th>
                    </tr></thead>
                    <tbody id="scheduleBody"></tbody>
                </table>
            </div>
            <div class="ts-detail-actions">
                ${isDraft ? `
                    <button class="btn btn-success btn-sm" onclick="App.pages.timesheets.finalizeSelected()">✅ Finalize</button>
                ` : `
                    <button class="btn btn-ghost btn-sm" onclick="App.pages.timesheets.revertSelected()">↩️ Revert to Draft</button>
                `}
                ${ts.is_distribution_locked ? `
                    <button class="btn btn-ghost btn-sm" onclick="App.pages.timesheets.unlockTimesheet(${ts.id})">🔓 Unlock</button>
                ` : ''}
                ${canEdit ? `
                    <button class="btn ${this.isEditingAll ? 'btn-primary' : 'btn-ghost'} btn-sm" id="tsEditSaveBtn" onclick="App.pages.timesheets.toggleTableEdit(${ts.id})">
                        ${this.isEditingAll ? '💾 Save' : '📝 Edit'}
                    </button>
                ` : `
                    <button class="btn btn-ghost btn-sm" id="tsEditSaveBtn" disabled style="opacity:0.5;cursor:not-allowed;">
                        📝 Edit
                    </button>
                `}
                ${this.isEditingAll ? `
                    <button class="btn btn-ghost btn-sm" onclick="App.pages.timesheets.cancelTableEdit(${ts.id})">Cancel</button>
                ` : ''}
                ${canEdit ? '<div class="ml-auto text-sm text-secondary">Double-click a row to edit</div>' : ''}
            </div>
        `;

        // Render schedule rows
        this.renderScheduleRows(ts);
    },

    renderScheduleRows(ts) {
        const body = document.getElementById('scheduleBody');
        if (!body) return;

        if (!ts.entries || ts.entries.length === 0) {
            body.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--text-secondary)">No schedule data. Run the solver to distribute hours.</td></tr>`;
            return;
        }

        const canEdit = ts.status === 'Draft' && !ts.is_distribution_locked;

        if (this.isEditingAll) {
            body.innerHTML = ts.entries.map((entry, idx) => {
                const weekend = App.isWeekend(entry.work_date);
                const dayName = App.getDayName(entry.work_date);
                const dateFormatted = App.formatDate(entry.work_date);

                return `
                    <tr class="${weekend ? 'weekend' : ''}" data-idx="${idx}">
                        <td>${dateFormatted}</td>
                        <td>${dayName}</td>
                        <td><input class="inline-input edit-start" value="${entry.start_time || ''}"></td>
                        <td><input class="inline-input edit-end" value="${entry.end_time || ''}"></td>
                        <td><input class="inline-input edit-break" value="${entry.break_duration || ''}" style="width:55px"></td>
                        <td><input class="inline-input edit-hours" value="${entry.hours_worked}" style="width:55px"></td>
                        <td style="text-align:left">
                            <input class="inline-input edit-remarks" value="${entry.remarks || ''}" style="width:100%;text-align:left">
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            body.innerHTML = ts.entries.map((entry, idx) => {
                const isOff = entry.hours_worked === 0;
                const weekend = App.isWeekend(entry.work_date);
                const dayName = App.getDayName(entry.work_date);
                const dateFormatted = App.formatDate(entry.work_date);

                return `
                    <tr class="${isOff ? 'day-off' : ''} ${weekend ? 'weekend' : ''}" 
                        ${canEdit ? `ondblclick="App.pages.timesheets.startInlineEdit(${idx}, ${ts.id})"` : ''}
                        data-idx="${idx}">
                        <td>${dateFormatted}</td>
                        <td>${dayName}</td>
                        <td>${entry.start_time || ''}</td>
                        <td>${entry.end_time || ''}</td>
                        <td>${entry.break_duration || ''}</td>
                        <td style="font-weight:${isOff ? '400' : '600'}">${isOff ? '' : entry.hours_worked}</td>
                        <td style="text-align:left;font-size:0.8rem;color:var(--text-secondary)">${entry.remarks || ''}</td>
                    </tr>
                `;
            }).join('');
        }
    },

    startInlineEdit(idx, tsId) {
        this.editingRow = idx;
        const ts = this.timesheets.find(t => t.id === tsId);
        // Reload detail to get fresh entries
        App.api(`/api/timesheets/${tsId}`).then(fullTs => {
            const entry = fullTs.entries[idx];
            if (!entry) return;

            const row = document.querySelector(`tr[data-idx="${idx}"]`);
            if (!row) return;

            row.innerHTML = `
                <td>${App.formatDate(entry.work_date)}</td>
                <td>${App.getDayName(entry.work_date)}</td>
                <td><input class="inline-input" id="editStart" value="${entry.start_time || ''}"></td>
                <td><input class="inline-input" id="editEnd" value="${entry.end_time || ''}"></td>
                <td><input class="inline-input" id="editBreak" value="${entry.break_duration || ''}" style="width:55px"></td>
                <td><input class="inline-input" id="editHours" value="${entry.hours_worked}" style="width:55px"></td>
                <td style="text-align:left">
                    <input class="inline-input" id="editRemarks" value="${entry.remarks || ''}" style="width:100%;text-align:left">
                </td>
            `;

            // Focus start time
            document.getElementById('editStart')?.focus();

            // Save on Enter, cancel on Escape
            const inputs = row.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') this.saveInlineEdit(tsId, fullTs, idx, entry.work_date);
                    if (e.key === 'Escape') this.selectTimesheet(tsId);
                });
            });
        });
    },

    async saveInlineEdit(tsId, fullTs, idx, workDate) {
        const start = document.getElementById('editStart').value.trim();
        const end = document.getElementById('editEnd').value.trim();
        const brk = document.getElementById('editBreak').value.trim();
        const hours = parseFloat(document.getElementById('editHours').value) || 0;
        const remarks = document.getElementById('editRemarks').value.trim();

        // Build updated entries array
        const entries = fullTs.entries.map((e, i) => {
            if (i === idx) {
                return {
                    work_date: e.work_date,
                    hours_worked: hours,
                    start_time: hours > 0 ? start : '',
                    end_time: hours > 0 ? end : '',
                    break_duration: hours > 0 ? brk : '',
                    remarks: remarks
                };
            }
            return e;
        });

        // Show lock/redistribute choice
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Save Changes</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <p style="color:var(--text-secondary);margin-bottom:20px;">How would you like to save your manual edits?</p>
                <div class="quick-actions">
                    <button class="quick-action-btn" id="btnLockOnly">
                        <span>🔒</span>
                        <div>
                            <div style="font-weight:600">Lock This Driver & Save</div>
                            <div style="font-size:0.78rem;color:var(--text-secondary)">Saves edits and locks this driver from future batch solves.</div>
                        </div>
                    </button>
                    <button class="quick-action-btn" id="btnRedistribute">
                        <span>🔄</span>
                        <div>
                            <div style="font-weight:600">Save & Redistribute Others</div>
                            <div style="font-size:0.78rem;color:var(--text-secondary)">Locks this driver's schedule, then re-runs the solver for all other unlocked drafts in this city/month.</div>
                        </div>
                    </button>
                </div>
            </div>
        `);

        document.getElementById('btnLockOnly').addEventListener('click', async () => {
            App.closeModal();
            try {
                await App.api(`/api/timesheets/${tsId}/entries`, {
                    method: 'PUT',
                    body: { entries, lock: true }
                });
                App.toast('Schedule saved and locked.', 'success');
                await this.selectTimesheet(tsId);
                await this.loadTimesheets();
            } catch (e) {
                App.toast('Save failed: ' + e.message, 'error');
            }
        });

        document.getElementById('btnRedistribute').addEventListener('click', async () => {
            App.closeModal();
            try {
                // First save and lock this timesheet
                await App.api(`/api/timesheets/${tsId}/entries`, {
                    method: 'PUT',
                    body: { entries, lock: true }
                });

                // Find all other draft timesheets in same city/month
                const ts = fullTs;
                const allTs = this.timesheets.filter(t =>
                    t.city_id === ts.city_id &&
                    t.year === ts.year &&
                    t.month === ts.month &&
                    t.id !== tsId &&
                    t.status === 'Draft' &&
                    !t.is_distribution_locked
                );

                if (allTs.length === 0) {
                    App.toast('No other unlocked drafts to redistribute.', 'info');
                    await this.selectTimesheet(tsId);
                    await this.loadTimesheets();
                    return;
                }

                // Show progress
                this.setSolverProgressActive(true);

                const timeoutLimit = parseFloat(document.getElementById('tsTimeoutLimit')?.value) || 30.0;
                const otherIds = allTs.map(t => t.id);
                const result = await App.api('/api/timesheets/solve', {
                    method: 'POST',
                    body: { timesheet_ids: [...otherIds, tsId], redistribute_around: tsId, timeout: timeoutLimit }
                });

                this.setSolverProgressActive(false);

                if (result.status === 'failed') {
                    App.toast('Solver failed to find a feasible redistribution.', 'error');
                } else {
                    App.toast(`Redistribution complete: ${result.altered_count} schedule(s) updated in ${result.solve_time}s.`, 'success', 6000);
                }

                await this.selectTimesheet(tsId);
                await this.loadTimesheets();

            } catch (e) {
                App.toast('Redistribution failed: ' + e.message, 'error');
            }
        });
    },

    setSolverProgressActive(active) {
        const p1 = document.getElementById('tsSolverProgress');
        const p2 = document.getElementById('tsListSolverProgress');
        if (p1) p1.classList.toggle('hidden', !active);
        if (p2) p2.classList.toggle('hidden', !active);
    },

    // ---- Solver ----
    async distributeSelected() {
        const ids = this.selectedIds.size > 0 ? [...this.selectedIds] : (this.selectedTs ? [this.selectedTs] : []);
        if (ids.length === 0) {
            App.toast('Select or open a timesheet to distribute.', 'warning');
            return;
        }

        // Show progress
        this.setSolverProgressActive(true);

        const btn = document.getElementById('tsDistributeBtn');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Solving...'; }

        try {
            const timeoutLimit = parseFloat(document.getElementById('tsTimeoutLimit')?.value) || 30.0;
            const result = await App.api('/api/timesheets/solve', {
                method: 'POST',
                body: { timesheet_ids: ids, timeout: timeoutLimit }
            });

            if (result.status === 'failed') {
                App.toast('Solver failed to find a feasible schedule.', 'error');
            } else {
                App.toast(result.message, 'success', 5000);
            }

            await this.loadTimesheets();
            if (this.selectedTs) await this.selectTimesheet(this.selectedTs);

        } catch (e) {
            App.toast('Solver error: ' + e.message, 'error');
        } finally {
            this.setSolverProgressActive(false);
            if (btn) { btn.disabled = false; btn.textContent = '⚡ Distribute Selected'; }
        }
    },

    // ---- Status ----
    async finalizeSelected() {
        const ids = this.selectedIds.size > 0 ? [...this.selectedIds] : (this.selectedTs ? [this.selectedTs] : []);
        if (ids.length === 0) {
            App.toast('Select or open a timesheet to finalize.', 'warning');
            return;
        }

        App.confirmDialog(
            `Finalize ${ids.length} Timesheet(s)?`,
            'This will finalize the selected timesheets and lock them from future batch solves.',
            async () => {
                let successCount = 0;
                for (const id of ids) {
                    try {
                        await App.api(`/api/timesheets/${id}/status`, {
                            method: 'PUT',
                            body: { status: 'Finalized' }
                        });
                        successCount++;
                    } catch (e) {
                        App.toast(`Failed to finalize timesheet #${id}: ${e.message}`, 'error');
                    }
                }
                if (successCount > 0) App.toast(`${successCount} timesheet(s) finalized.`, 'success');
                await this.loadTimesheets();
                if (this.selectedTs) await this.selectTimesheet(this.selectedTs);
            }
        );
    },

    async revertSelected() {
        const ids = this.selectedIds.size > 0 ? [...this.selectedIds] : (this.selectedTs ? [this.selectedTs] : []);
        if (ids.length === 0) {
            App.toast('Select or open a timesheet to revert.', 'warning');
            return;
        }

        App.confirmDialog(
            `Revert ${ids.length} Timesheet(s)?`,
            'This will revert the selected timesheets back to Draft status and unlock them.',
            async () => {
                let successCount = 0;
                for (const id of ids) {
                    try {
                        await App.api(`/api/timesheets/${id}/status`, {
                            method: 'PUT',
                            body: { status: 'Draft' }
                        });
                        successCount++;
                    } catch (e) {
                        App.toast(`Failed to revert timesheet #${id}: ${e.message}`, 'error');
                    }
                }
                if (successCount > 0) App.toast(`${successCount} timesheet(s) reverted to Draft.`, 'success');
                await this.loadTimesheets();
                if (this.selectedTs) await this.selectTimesheet(this.selectedTs);
            }
        );
    },

    async unlockTimesheet(id) {
        try {
            await App.api(`/api/timesheets/${id}/unlock`, { method: 'POST' });
            App.toast('Timesheet unlocked.', 'success');
            await this.loadTimesheets();
            await this.selectTimesheet(id);
        } catch (e) {
            App.toast('Failed to unlock: ' + e.message, 'error');
        }
    },

    // ---- Table Edit Mode ----
    toggleTableEdit(tsId) {
        if (this.isEditingAll) {
            this.saveTableEdit(tsId);
        } else {
            this.isEditingAll = true;
            this.renderDetail(this.activeTsDetail);
        }
    },

    cancelTableEdit(tsId) {
        this.isEditingAll = false;
        this.selectTimesheet(tsId);
    },

    async saveTableEdit(tsId) {
        const rows = document.querySelectorAll('#scheduleBody tr');
        const entries = [];

        rows.forEach(row => {
            const idx = parseInt(row.dataset.idx);
            const start = row.querySelector('.edit-start').value.trim();
            const end = row.querySelector('.edit-end').value.trim();
            const brk = row.querySelector('.edit-break').value.trim();
            const hoursVal = row.querySelector('.edit-hours').value;
            const hours = parseFloat(hoursVal) || 0;
            const remarks = row.querySelector('.edit-remarks').value.trim();
            
            const originalEntry = this.activeTsDetail.entries[idx];

            entries.push({
                work_date: originalEntry.work_date,
                hours_worked: hours,
                start_time: hours > 0 ? start : '',
                end_time: hours > 0 ? end : '',
                break_duration: hours > 0 ? brk : '',
                remarks: remarks
            });
        });

        // Show lock/redistribute choice
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Save Changes</span>
                <button class="modal-close" onclick="App.pages.timesheets.cancelTableEdit(${tsId})">✕</button>
            </div>
            <div class="modal-body">
                <p style="color:var(--text-secondary);margin-bottom:20px;">How would you like to save your manual edits?</p>
                <div class="quick-actions">
                    <button class="quick-action-btn" id="btnLockOnly">
                        <span>🔒</span>
                        <div>
                            <div style="font-weight:600">Lock This Driver & Save</div>
                            <div style="font-size:0.78rem;color:var(--text-secondary)">Saves edits and locks this driver from future batch solves.</div>
                        </div>
                    </button>
                    <button class="quick-action-btn" id="btnRedistribute">
                        <span>🔄</span>
                        <div>
                            <div style="font-weight:600">Save & Redistribute Others</div>
                            <div style="font-size:0.78rem;color:var(--text-secondary)">Locks this driver's schedule, then re-runs the solver for all other unlocked drafts in this city/month.</div>
                        </div>
                    </button>
                </div>
            </div>
        `);

        document.getElementById('btnLockOnly').addEventListener('click', async () => {
            App.closeModal();
            try {
                await App.api(`/api/timesheets/${tsId}/entries`, {
                    method: 'PUT',
                    body: { entries, lock: true }
                });
                App.toast('Schedule saved and locked.', 'success');
                this.isEditingAll = false;
                await this.selectTimesheet(tsId);
                await this.loadTimesheets();
            } catch (e) {
                App.toast('Save failed: ' + e.message, 'error');
            }
        });

        document.getElementById('btnRedistribute').addEventListener('click', async () => {
            App.closeModal();
            try {
                // First save and lock this timesheet
                await App.api(`/api/timesheets/${tsId}/entries`, {
                    method: 'PUT',
                    body: { entries, lock: true }
                });

                // Find all other draft timesheets in same city/month
                const ts = this.activeTsDetail;
                const allTs = this.timesheets.filter(t =>
                    t.city_id === ts.city_id &&
                    t.year === ts.year &&
                    t.month === ts.month &&
                    t.id !== tsId &&
                    t.status === 'Draft' &&
                    !t.is_distribution_locked
                );

                if (allTs.length === 0) {
                    App.toast('No other unlocked drafts to redistribute.', 'info');
                    this.isEditingAll = false;
                    await this.selectTimesheet(tsId);
                    await this.loadTimesheets();
                    return;
                }

                // Show progress
                this.setSolverProgressActive(true);

                const timeoutLimit = parseFloat(document.getElementById('tsTimeoutLimit')?.value) || 30.0;
                const otherIds = allTs.map(t => t.id);
                const result = await App.api('/api/timesheets/solve', {
                    method: 'POST',
                    body: { timesheet_ids: [...otherIds, tsId], redistribute_around: tsId, timeout: timeoutLimit }
                });

                this.setSolverProgressActive(false);

                if (result.status === 'failed') {
                    App.toast('Solver failed to find a feasible redistribution.', 'error');
                } else {
                    App.toast(`Redistribution complete: ${result.altered_count} schedule(s) updated in ${result.solve_time}s.`, 'success', 6000);
                }

                this.isEditingAll = false;
                await this.selectTimesheet(tsId);
                await this.loadTimesheets();

            } catch (e) {
                App.toast('Redistribution failed: ' + e.message, 'error');
            }
        });
    },

    // ---- Export ----
    async exportTimesheet(id) {
        try {
            const res = await App.api(`/api/timesheets/${id}/export`, { method: 'POST' });
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = res.headers?.get('content-disposition')?.split('filename=')[1] || 'timesheet.docx';
            a.click();
            URL.revokeObjectURL(url);
            App.toast('Exported to Word document.', 'success');
        } catch (e) {
            App.toast('Export failed: ' + e.message, 'error');
        }
    },

    async exportSelected() {
        const ids = this.selectedIds.size > 0 ? [...this.selectedIds] : (this.selectedTs ? [this.selectedTs] : []);
        if (ids.length === 0) {
            App.toast('Select or open a timesheet to export.', 'warning');
            return;
        }
        for (const id of ids) {
            await this.exportTimesheet(id);
        }
    },

    // ---- Delete ----
    deleteSelected() {
        const ids = this.selectedIds.size > 0 ? [...this.selectedIds] : (this.selectedTs ? [this.selectedTs] : []);
        if (ids.length === 0) { App.toast('Select or open a timesheet to delete.', 'warning'); return; }

        App.confirmDialog(
            `Delete ${ids.length} Timesheet(s)?`,
            'This will permanently delete the selected timesheets and all their daily entries.',
            async () => {
                for (const id of ids) {
                    try { await App.api(`/api/timesheets/${id}`, { method: 'DELETE' }); }
                    catch (e) { App.toast(`Failed to delete: ${e.message}`, 'error'); }
                }
                // Clear selection if it was deleted
                ids.forEach(id => this.selectedIds.delete(id));
                if (ids.includes(this.selectedTs)) this.selectedTs = null;

                App.toast(`${ids.length} timesheet(s) deleted.`, 'success');
                await this.loadTimesheets();

                if (this.selectedTs) {
                    await this.selectTimesheet(this.selectedTs);
                } else {
                    document.getElementById('tsDetail').innerHTML = `
                        <div class="empty-state"><div class="empty-state-icon">📋</div><div class="empty-state-title">No Timesheet Selected</div></div>
                    `;
                }
            },
            { danger: true, confirmText: 'Delete All' }
        );
    },

    // ---- New Timesheets Modal (Multi-Driver) ----
    openNewModal() {
        const cityOptions = this.cities.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        const now = new Date();

        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">New Timesheets</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">City</label>
                        <select class="form-select" id="newTsCity">${cityOptions}</select>
                    </div>
                    <div class="form-group" style="flex:0.5">
                        <label class="form-label">Month</label>
                        <select class="form-select" id="newTsMonth">
                            ${Array.from({length:12}, (_,i) => `<option value="${i+1}" ${i+1===now.getMonth()+1?'selected':''}>${String(i+1).padStart(2,'0')}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group" style="flex:0.5">
                        <label class="form-label">Year</label>
                        <select class="form-select" id="newTsYear">
                            <option value="${now.getFullYear()}">${now.getFullYear()}</option>
                            <option value="${now.getFullYear()+1}">${now.getFullYear()+1}</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Target Hours Mode</label>
                    <div class="flex gap-16" style="margin-bottom:8px">
                        <label style="display:flex;align-items:center;gap:6px;font-size:0.88rem;color:var(--text-primary);cursor:pointer">
                            <input type="radio" name="hoursMode" value="same" checked onchange="App.pages.timesheets.toggleHoursMode()"> Same for all
                        </label>
                        <label style="display:flex;align-items:center;gap:6px;font-size:0.88rem;color:var(--text-primary);cursor:pointer">
                            <input type="radio" name="hoursMode" value="custom" onchange="App.pages.timesheets.toggleHoursMode()"> Custom per driver
                        </label>
                    </div>
                    <div id="sameHoursRow">
                        <input class="form-input" id="newTsHours" type="number" step="0.5" min="10" max="208" value="120" placeholder="Target hours" style="width:120px">
                    </div>
                </div>
                <div class="form-group">
                    <div class="flex items-center justify-between mb-8">
                        <label class="form-label" style="margin:0">Select Drivers</label>
                        <label style="display:flex;align-items:center;gap:6px;font-size:0.82rem;color:var(--text-secondary);cursor:pointer">
                            <input type="checkbox" id="newTsSelectAll" onchange="App.pages.timesheets.toggleNewSelectAll()"> Select All
                        </label>
                    </div>
                    <div class="checkbox-list" id="newTsDriverList"></div>
                </div>
                <div class="form-hint">Target must be 10.0–208.0h in 0.5h increments.</div>
                <div class="form-error" id="newTsError"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="newTsCreateBtn">Create Timesheets</button>
            </div>
        `, { wide: true });

        this.renderDriverCheckboxes();

        document.getElementById('newTsCreateBtn').addEventListener('click', () => this.createTimesheets());
        document.getElementById('newTsCity').addEventListener('change', () => this.renderDriverCheckboxes());
        document.getElementById('newTsMonth').addEventListener('change', () => this.renderDriverCheckboxes());
        document.getElementById('newTsYear').addEventListener('change', () => this.renderDriverCheckboxes());
    },

    async renderDriverCheckboxes() {
        const list = document.getElementById('newTsDriverList');
        const cityId = document.getElementById('newTsCity')?.value;
        const month = document.getElementById('newTsMonth')?.value;
        const year = document.getElementById('newTsYear')?.value;

        // Check which drivers already have timesheets for this city+month
        let existingTs = [];
        if (cityId && month && year) {
            try {
                existingTs = await App.api('/api/timesheets', {
                    params: { city_id: cityId, month, year }
                });
            } catch (e) {}
        }
        const existingDriverIds = new Set(existingTs.map(t => t.employee_id));

        const isCustom = document.querySelector('input[name="hoursMode"]:checked')?.value === 'custom';
        const defaultHours = document.getElementById('newTsHours')?.value || '120';

        list.innerHTML = this.drivers.map(d => {
            const exists = existingDriverIds.has(d.id);
            return `
                <div class="checkbox-item ${exists ? 'disabled' : ''}">
                    <input type="checkbox" class="newTsDriverCheck" data-driver-id="${d.id}" ${exists ? 'disabled' : ''}>
                    <span class="checkbox-item-label">${d.name} <span style="color:var(--text-tertiary);font-size:0.78rem">(${d.personal_id})</span></span>
                    ${isCustom ? `<input class="checkbox-item-input" data-driver-hours="${d.id}" type="number" step="0.5" min="10" max="208" value="${defaultHours}" ${exists ? 'disabled' : ''}>` : ''}
                    ${exists ? '<span style="font-size:0.72rem;color:var(--accent-warning)">exists</span>' : ''}
                </div>
            `;
        }).join('');
    },

    toggleHoursMode() {
        const isCustom = document.querySelector('input[name="hoursMode"]:checked')?.value === 'custom';
        document.getElementById('sameHoursRow').style.display = isCustom ? 'none' : 'block';
        this.renderDriverCheckboxes();
    },

    toggleNewSelectAll() {
        const checked = document.getElementById('newTsSelectAll')?.checked;
        document.querySelectorAll('.newTsDriverCheck:not(:disabled)').forEach(cb => cb.checked = checked);
    },

    async createTimesheets() {
        const cityId = parseInt(document.getElementById('newTsCity').value);
        const month = parseInt(document.getElementById('newTsMonth').value);
        const year = parseInt(document.getElementById('newTsYear').value);
        const errEl = document.getElementById('newTsError');
        const isCustom = document.querySelector('input[name="hoursMode"]:checked')?.value === 'custom';

        const selectedDrivers = [];
        document.querySelectorAll('.newTsDriverCheck:checked').forEach(cb => {
            const driverId = parseInt(cb.dataset.driverId);
            let targetHours;
            if (isCustom) {
                const hoursInput = document.querySelector(`input[data-driver-hours="${driverId}"]`);
                targetHours = parseFloat(hoursInput?.value) || 0;
            } else {
                targetHours = parseFloat(document.getElementById('newTsHours').value) || 0;
            }
            selectedDrivers.push({ employee_id: driverId, city_id: cityId, year, month, target_hours: targetHours });
        });

        if (selectedDrivers.length === 0) { errEl.textContent = 'Select at least one driver.'; return; }

        // Validate hours
        for (const d of selectedDrivers) {
            if (d.target_hours < 10 || d.target_hours > 208 || d.target_hours % 0.5 !== 0) {
                errEl.textContent = 'Target hours must be 10.0–208.0 in 0.5h steps.';
                return;
            }
        }

        try {
            const result = await App.api('/api/timesheets', { method: 'POST', body: selectedDrivers });
            const created = result.created?.length || 0;
            const errors = result.errors?.length || 0;

            if (created > 0) App.toast(`${created} timesheet(s) created.`, 'success');
            if (errors > 0) App.toast(`${errors} timesheet(s) already existed.`, 'warning');

            App.closeModal();
            await this.loadTimesheets();
        } catch (e) {
            errEl.textContent = e.message;
        }
    }
});
