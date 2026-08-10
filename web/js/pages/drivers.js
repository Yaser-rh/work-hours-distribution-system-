/* ==============================================================================
   Drivers Page — Master-Detail Layout
   ============================================================================== */

App.registerPage('drivers', {
    selectedDriver: null,

    async render(container) {
        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Drivers</h1>
                <div class="flex gap-8">
                    <button class="btn btn-ghost" onclick="App.pages.drivers.openAutoAssignModal()">
                        ⚡ Auto-Assign Cities
                    </button>
                    <button class="btn btn-primary" onclick="App.pages.drivers.openAddModal()">
                        <span>+</span> Add Driver
                    </button>
                </div>
            </div>
            <div class="driver-list-layout">
                <div class="card driver-list-panel">
                    <div style="padding:12px 16px;border-bottom:1px solid var(--border)">
                        <input class="form-input" id="driverSearch" placeholder="Search drivers..." oninput="App.pages.drivers.filterList()">
                    </div>
                    <div id="driverList" style="overflow-y:auto;flex:1">
                        <div class="empty-state" style="padding:40px"><div class="empty-state-text">Loading...</div></div>
                    </div>
                </div>
                <div class="card ts-detail-panel" id="driverDetail">
                    <div class="empty-state">
                        <div class="empty-state-icon">👤</div>
                        <div class="empty-state-title">Select a Driver</div>
                        <div class="empty-state-text">Click on a driver from the list to view their details and timesheet history.</div>
                    </div>
                </div>
            </div>
        `;
        this.selectedDriver = null;
        this.drivers = [];
        await this.loadDrivers();
    },

    async loadDrivers() {
        try {
            this.drivers = await App.api('/api/drivers');
            this.renderList(this.drivers);
        } catch (e) {
            App.toast('Failed to load drivers: ' + e.message, 'error');
        }
    },

    renderList(drivers) {
        const list = document.getElementById('driverList');
        if (!drivers || drivers.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="padding:40px">
                    <div class="empty-state-icon">👤</div>
                    <div class="empty-state-title">No drivers yet</div>
                    <div class="empty-state-text">Add your first delivery driver.</div>
                </div>
            `;
            return;
        }

        list.innerHTML = drivers.map(d => `
            <div class="driver-list-item ${this.selectedDriver === d.id ? 'active' : ''}" onclick="App.pages.drivers.selectDriver(${d.id})" data-driver-id="${d.id}">
                <div class="driver-list-name">${d.name}</div>
                <div class="driver-list-id flex items-center justify-between" style="gap:6px">
                    <span>ID: ${d.personal_id}</span>
                    <span class="badge badge-${d.city_id ? 'draft' : 'ghost'}" style="font-size:0.7rem">${d.city_name ? '📍 ' + d.city_name : 'Unassigned'}</span>
                </div>
            </div>
        `).join('');
    },

    filterList() {
        const q = document.getElementById('driverSearch').value.toLowerCase();
        const filtered = this.drivers.filter(d =>
            d.name.toLowerCase().includes(q) ||
            d.personal_id.toLowerCase().includes(q) ||
            (d.city_name && d.city_name.toLowerCase().includes(q))
        );
        this.renderList(filtered);
    },

    async selectDriver(id) {
        this.selectedDriver = id;
        // Highlight in list
        document.querySelectorAll('.driver-list-item').forEach(el => {
            el.classList.toggle('active', parseInt(el.dataset.driverId) === id);
        });

        const driver = this.drivers.find(d => d.id === id);
        if (!driver) return;

        const detail = document.getElementById('driverDetail');
        const cityLabel = driver.city_name ? `📍 ${driver.city_name}` : 'Unassigned';
        const changeCityBtnText = driver.city_id ? '📍 Change City' : '📍 Assign City';

        detail.innerHTML = `
            <div class="ts-detail-header">
                <div class="ts-detail-title">${driver.name}</div>
                <div class="ts-detail-meta">
                    <span>Personal ID: <strong>${driver.personal_id}</strong></span>
                    <span>City: <strong>${cityLabel}</strong></span>
                </div>
            </div>
            <div style="padding:18px 22px;border-bottom:1px solid var(--border);display:flex;gap:8px;">
                <button class="btn btn-primary btn-sm" onclick="App.pages.drivers.openQuickAssignCityModal(${driver.id})">${changeCityBtnText}</button>
                <button class="btn btn-ghost btn-sm" onclick="App.pages.drivers.openEditModal(${driver.id})">Edit Driver</button>
                <button class="btn btn-ghost btn-sm" style="color:var(--accent-danger)" onclick="App.pages.drivers.deleteDriver(${driver.id}, '${driver.name.replace(/'/g, "\\'")}')">Delete</button>
            </div>
            <div style="padding:18px 22px;">
                <h3 style="font-size:0.95rem;font-weight:600;color:var(--text-primary);margin-bottom:14px;">Timesheet History</h3>
                <div id="driverTimesheets">Loading...</div>
            </div>
        `;

        // Load timesheet history
        try {
            const timesheets = await App.api(`/api/drivers/${id}/timesheets`);
            const el = document.getElementById('driverTimesheets');

            if (!timesheets || timesheets.length === 0) {
                el.innerHTML = `<div class="text-sm text-secondary">No timesheets found for this driver.</div>`;
                return;
            }

            el.innerHTML = `<table class="data-table">
                <thead><tr>
                    <th>Month</th><th>City</th><th>Target</th><th>Status</th>
                </tr></thead>
                <tbody>
                    ${timesheets.map(ts => `
                        <tr style="cursor:pointer" onclick="location.hash='timesheets'">
                            <td>${String(ts.month).padStart(2,'0')}/${ts.year}</td>
                            <td>${ts.city_name}</td>
                            <td class="text-center">${ts.target_hours}h</td>
                            <td class="text-center"><span class="badge badge-${ts.status.toLowerCase()}">${ts.status}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>`;

        } catch (e) {
            document.getElementById('driverTimesheets').innerHTML = `<div class="text-sm" style="color:var(--accent-danger)">Failed to load.</div>`;
        }
    },

    async openQuickAssignCityModal(driverId) {
        const driver = this.drivers.find(d => d.id === driverId);
        if (!driver) return;

        let cities = [];
        try { cities = await App.api('/api/cities'); } catch (e) {}

        const cityOptions = `
            <option value="">Unassigned (All Cities)</option>
            ${cities.map(c => `<option value="${c.id}" ${driver.city_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
        `;

        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Assign City to ${driver.name}</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <p style="color:var(--text-secondary);font-size:0.88rem;margin-bottom:16px;">
                    Select the city to bind driver <strong>${driver.name}</strong> (${driver.personal_id}):
                </p>
                <div class="form-group">
                    <label class="form-label">City</label>
                    <select class="form-select" id="quickDriverCity">
                        ${cityOptions}
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="quickSaveCityBtn">Save City</button>
            </div>
        `);

        document.getElementById('quickSaveCityBtn').addEventListener('click', async () => {
            const val = document.getElementById('quickDriverCity').value;
            const cityId = val ? parseInt(val) : null;
            try {
                await App.api(`/api/drivers/${driverId}/city`, {
                    method: 'PUT',
                    body: { city_id: cityId }
                });
                App.toast(`Updated city for ${driver.name}.`, 'success');
                App.closeModal();
                await this.loadDrivers();
                if (this.selectedDriver) this.selectDriver(this.selectedDriver);
            } catch (e) {
                App.toast('Failed to update city: ' + e.message, 'error');
            }
        });
    },

    async openAutoAssignModal() {
        try {
            const preview = await App.api('/api/drivers/auto-assign-preview');
            const cities = await App.api('/api/cities');

            if (!preview || preview.length === 0) {
                App.toast('No drivers found to auto-assign.', 'info');
                return;
            }

            App.openModal(`
                <div class="modal-header">
                    <span class="modal-title">⚡ Review Auto-Assigned Driver Cities</span>
                    <button class="modal-close" onclick="App.closeModal()">✕</button>
                </div>
                <div class="modal-body">
                    <div style="background:var(--bg-secondary);padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:0.85rem;color:var(--text-secondary)">
                        ℹ️ Analyzed driver timesheets in the database. Review the proposed city assignments below. You can adjust any proposed city before confirming.
                    </div>
                    <div style="max-height:360px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Driver</th>
                                    <th>Current City</th>
                                    <th>Timesheets</th>
                                    <th>Proposed City</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${preview.map(item => {
                                    const currentLabel = item.current_city_name ? `📍 ${item.current_city_name}` : '<span style="color:var(--text-tertiary)">Unassigned</span>';
                                    const optionsHtml = `
                                        <option value="">Unassigned</option>
                                        ${cities.map(c => `<option value="${c.id}" ${item.proposed_city_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
                                    `;
                                    const tsHint = item.timesheet_count > 0 ? `${item.timesheet_count} timesheet(s)` : 'No history';

                                    return `
                                        <tr>
                                            <td>
                                                <strong>${item.driver_name}</strong>
                                                <div style="font-size:0.75rem;color:var(--text-tertiary)">${item.personal_id}</div>
                                            </td>
                                            <td>${currentLabel}</td>
                                            <td class="text-sm text-secondary">${tsHint}</td>
                                            <td>
                                                <select class="form-select mass-city-select" data-driver-id="${item.driver_id}" style="padding:4px 8px;font-size:0.85rem">
                                                    ${optionsHtml}
                                                </select>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                    <button class="btn btn-primary" id="confirmMassAssignBtn">✅ Confirm & Assign All</button>
                </div>
            `, { wide: true });

            document.getElementById('confirmMassAssignBtn').addEventListener('click', async () => {
                const selects = document.querySelectorAll('.mass-city-select');
                const assignments = [];
                selects.forEach(sel => {
                    const driverId = parseInt(sel.dataset.driverId);
                    const val = sel.value;
                    const cityId = val ? parseInt(val) : null;
                    assignments.push({ driver_id: driverId, city_id: cityId });
                });

                try {
                    const res = await App.api('/api/drivers/mass-assign-cities', {
                        method: 'POST',
                        body: assignments
                    });
                    App.toast(`Successfully updated city assignments for ${res.updated_count || assignments.length} driver(s).`, 'success');
                    App.closeModal();
                    await this.loadDrivers();
                    if (this.selectedDriver) this.selectDriver(this.selectedDriver);
                } catch (e) {
                    App.toast('Failed to apply assignments: ' + e.message, 'error');
                }
            });

        } catch (e) {
            App.toast('Failed to load auto-assign preview: ' + e.message, 'error');
        }
    },

    openAddModal() {
        this.openDriverModal('Add Driver', null);
    },

    openEditModal(id) {
        const driver = this.drivers.find(d => d.id === id);
        this.openDriverModal('Edit Driver', driver);
    },

    async openDriverModal(title, driver) {
        let cities = [];
        try {
            cities = await App.api('/api/cities');
        } catch (e) {}

        const cityOptions = `
            <option value="">Unassigned (All Cities)</option>
            ${cities.map(c => `<option value="${c.id}" ${driver && driver.city_id === c.id ? 'selected' : ''}>${c.name}</option>`).join('')}
        `;

        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">${title}</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Driver Name</label>
                    <input class="form-input" id="driverName" value="${driver ? driver.name : ''}" placeholder="Full name">
                </div>
                <div class="form-group">
                    <label class="form-label">Personal ID</label>
                    <input class="form-input" id="driverPid" value="${driver ? driver.personal_id : ''}" placeholder="e.g., P12345">
                </div>
                <div class="form-group">
                    <label class="form-label">Assigned City</label>
                    <select class="form-select" id="driverCity">
                        ${cityOptions}
                    </select>
                </div>
                <div class="form-error" id="driverError"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="driverSaveBtn">Save</button>
            </div>
        `);

        document.getElementById('driverSaveBtn').addEventListener('click', async () => {
            const name = document.getElementById('driverName').value.trim();
            const pid = document.getElementById('driverPid').value.trim();
            const cityVal = document.getElementById('driverCity').value;
            const cityId = cityVal ? parseInt(cityVal) : null;
            const errEl = document.getElementById('driverError');

            if (!name || !pid) { errEl.textContent = 'Name and Personal ID are required.'; return; }

            try {
                if (driver) {
                    await App.api(`/api/drivers/${driver.id}`, { method: 'PUT', body: { name, personal_id: pid, city_id: cityId } });
                    App.toast('Driver updated.', 'success');
                } else {
                    await App.api('/api/drivers', { method: 'POST', body: { name, personal_id: pid, city_id: cityId } });
                    App.toast('Driver added.', 'success');
                }
                App.closeModal();
                await this.loadDrivers();
                if (this.selectedDriver) this.selectDriver(this.selectedDriver);
            } catch (e) {
                errEl.textContent = e.message;
            }
        });
    },

    deleteDriver(id, name) {
        App.confirmDialog(
            'Delete Driver?',
            `Delete <strong>${name}</strong>? This cannot be undone.`,
            async () => {
                try {
                    await App.api(`/api/drivers/${id}`, { method: 'DELETE' });
                    App.toast('Driver deleted.', 'success');
                    this.selectedDriver = null;
                    await this.loadDrivers();
                    document.getElementById('driverDetail').innerHTML = `
                        <div class="empty-state"><div class="empty-state-icon">👤</div><div class="empty-state-title">Select a Driver</div></div>
                    `;
                } catch (e) {
                    App.toast(e.message, 'error');
                }
            },
            { danger: true, confirmText: 'Delete' }
        );
    }
});
