/* ==============================================================================
   Cities Page
   ============================================================================== */

App.registerPage('cities', {
    async render(container) {
        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Cities</h1>
                <button class="btn btn-primary" onclick="App.pages.cities.openAddModal()">
                    <span>+</span> Add City
                </button>
            </div>
            <div class="city-grid" id="cityGrid">
                <div class="empty-state"><div class="empty-state-text">Loading cities...</div></div>
            </div>
        `;
        this.loadCities();
    },

    async loadCities() {
        try {
            const cities = await App.api('/api/cities');
            const grid = document.getElementById('cityGrid');

            if (!cities || cities.length === 0) {
                grid.innerHTML = `
                    <div class="empty-state" style="grid-column:1/-1">
                        <div class="empty-state-icon">🏙️</div>
                        <div class="empty-state-title">No cities yet</div>
                        <div class="empty-state-text">Add your first delivery city to get started.</div>
                        <button class="btn btn-primary mt-16" onclick="App.pages.cities.openAddModal()">+ Add City</button>
                    </div>
                `;
                return;
            }

            grid.innerHTML = cities.map(city => {
                const startH = this.timeToHours(city.start_time);
                const endH = this.timeToHours(city.end_time);
                const windowH = endH - startH;
                const leftPct = (startH / 24) * 100;
                const widthPct = (windowH / 24) * 100;

                return `
                    <div class="card card-hover city-card">
                        <div class="city-card-name">${city.name}</div>
                        <div class="city-meta">
                            <span>${city.start_time}</span>
                            <span>${city.end_time}</span>
                        </div>
                        <div class="city-timeline">
                            <div class="city-timeline-fill" style="left:${leftPct}%;width:${widthPct}%"></div>
                        </div>
                        <div class="city-stats">
                            <div><span class="city-stat-value">${windowH.toFixed(1)}h</span> window</div>
                            <div><span class="city-stat-value">${city.driver_count || 0}</span> drivers</div>
                        </div>
                        <div class="city-actions" style="flex-wrap:wrap;gap:6px;margin-top:12px;">
                            <button class="btn btn-primary btn-sm" onclick="App.pages.cities.openAddDriverModal(${city.id}, '${city.name.replace(/'/g, "\\'")}')">
                                <span>+</span> Add Driver
                            </button>
                            <button class="btn btn-ghost btn-sm" onclick="App.pages.cities.openDriversModal(${city.id}, '${city.name.replace(/'/g, "\\'")}')">
                                👥 Drivers (${city.driver_count || 0})
                            </button>
                            <button class="btn btn-ghost btn-sm" onclick="App.pages.cities.openEditModal(${city.id}, '${city.name.replace(/'/g, "\\'")}', '${city.start_time}', '${city.end_time}')">Edit</button>
                            <button class="btn btn-ghost btn-sm" style="color:var(--accent-danger)" onclick="App.pages.cities.deleteCity(${city.id}, '${city.name.replace(/'/g, "\\'")}')">Delete</button>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (e) {
            App.toast('Failed to load cities: ' + e.message, 'error');
        }
    },

    timeToHours(timeStr) {
        const [h, m] = timeStr.split(':').map(Number);
        return h + m / 60;
    },

    openAddModal() {
        this.openCityModal('Add City', null);
    },

    openEditModal(id, name, start, end) {
        this.openCityModal('Edit City', { id, name, start_time: start, end_time: end });
    },

    openCityModal(title, city) {
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">${title}</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">City Name</label>
                    <input class="form-input" id="cityName" value="${city ? city.name : ''}" placeholder="e.g., Munich">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Start Time</label>
                        <input class="form-input" id="cityStart" value="${city ? city.start_time : '08:00'}" placeholder="HH:MM">
                    </div>
                    <div class="form-group">
                        <label class="form-label">End Time</label>
                        <input class="form-input" id="cityEnd" value="${city ? city.end_time : '22:00'}" placeholder="HH:MM">
                    </div>
                </div>
                <div id="cityTimelinePreview" style="margin-top:4px"></div>
                <div class="form-error" id="cityError"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="citySaveBtn">Save City</button>
            </div>
        `);

        // Timeline preview
        const updatePreview = () => {
            const s = document.getElementById('cityStart').value;
            const e = document.getElementById('cityEnd').value;
            const preview = document.getElementById('cityTimelinePreview');
            if (s && e) {
                const sH = this.timeToHours(s);
                const eH = this.timeToHours(e);
                if (eH > sH) {
                    const lPct = (sH / 24) * 100;
                    const wPct = ((eH - sH) / 24) * 100;
                    preview.innerHTML = `
                        <div class="city-timeline" style="margin:8px 0">
                            <div class="city-timeline-fill" style="left:${lPct}%;width:${wPct}%"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:var(--text-tertiary)">
                            <span>00:00</span><span>${(eH - sH).toFixed(1)}h operational window</span><span>24:00</span>
                        </div>
                    `;
                }
            }
        };

        document.getElementById('cityStart').addEventListener('input', updatePreview);
        document.getElementById('cityEnd').addEventListener('input', updatePreview);
        updatePreview();

        document.getElementById('citySaveBtn').addEventListener('click', async () => {
            const name = document.getElementById('cityName').value.trim();
            const start = document.getElementById('cityStart').value.trim();
            const end = document.getElementById('cityEnd').value.trim();
            const errEl = document.getElementById('cityError');

            if (!name || !start || !end) { errEl.textContent = 'All fields are required.'; return; }

            // Validate time format
            const timeRe = /^([01]\d|2[0-3]):([0-5]\d)$/;
            if (!timeRe.test(start) || !timeRe.test(end)) { errEl.textContent = 'Times must be in HH:MM format.'; return; }

            try {
                if (city) {
                    await App.api(`/api/cities/${city.id}`, { method: 'PUT', body: { name, start_time: start, end_time: end } });
                    App.toast('City updated.', 'success');
                } else {
                    await App.api('/api/cities', { method: 'POST', body: { name, start_time: start, end_time: end } });
                    App.toast('City added.', 'success');
                }
                App.closeModal();
                this.loadCities();
            } catch (e) {
                errEl.textContent = e.message;
            }
        });
    },

    deleteCity(id, name) {
        App.confirmDialog(
            'Delete City?',
            `Are you sure you want to delete <strong>${name}</strong>? This cannot be undone.`,
            async () => {
                try {
                    await App.api(`/api/cities/${id}`, { method: 'DELETE' });
                    App.toast('City deleted.', 'success');
                    this.loadCities();
                } catch (e) {
                    App.toast(e.message, 'error');
                }
            },
            { danger: true, confirmText: 'Delete' }
        );
    },

    openAddDriverModal(cityId, cityName) {
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Add Driver to ${cityName}</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div style="background:var(--bg-secondary);padding:10px 14px;border-radius:8px;margin-bottom:16px;font-size:0.85rem;color:var(--text-secondary)">
                    📍 Bound City: <strong style="color:var(--text-primary)">${cityName}</strong>
                </div>
                <div class="form-group">
                    <label class="form-label">Driver Name</label>
                    <input class="form-input" id="cityDriverName" placeholder="Full name">
                </div>
                <div class="form-group">
                    <label class="form-label">Personal ID</label>
                    <input class="form-input" id="cityDriverPid" placeholder="e.g., P12345">
                </div>
                <div class="form-error" id="cityDriverError"></div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-ghost" onclick="App.closeModal()">Cancel</button>
                <button class="btn btn-primary" id="cityDriverSaveBtn">Save Driver</button>
            </div>
        `);

        document.getElementById('cityDriverSaveBtn').addEventListener('click', async () => {
            const name = document.getElementById('cityDriverName').value.trim();
            const pid = document.getElementById('cityDriverPid').value.trim();
            const errEl = document.getElementById('cityDriverError');

            if (!name || !pid) { errEl.textContent = 'All fields are required.'; return; }

            try {
                await App.api('/api/drivers', {
                    method: 'POST',
                    body: { name, personal_id: pid, city_id: cityId }
                });
                App.toast(`Driver ${name} added to ${cityName}.`, 'success');
                App.closeModal();
                this.loadCities();
            } catch (e) {
                errEl.textContent = e.message;
            }
        });
    },

    async openDriversModal(cityId, cityName) {
        App.openModal(`
            <div class="modal-header">
                <span class="modal-title">Drivers in ${cityName}</span>
                <button class="modal-close" onclick="App.closeModal()">✕</button>
            </div>
            <div class="modal-body">
                <div id="cityDriversList">Loading drivers...</div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary btn-sm" onclick="App.closeModal(); App.pages.cities.openAddDriverModal(${cityId}, '${cityName.replace(/'/g, "\\'")}')">+ Add Driver to ${cityName}</button>
                <button class="btn btn-ghost btn-sm" onclick="App.closeModal()">Close</button>
            </div>
        `, { wide: true });

        try {
            const drivers = await App.api('/api/drivers', { params: { city_id: cityId } });
            const cityDrivers = drivers.filter(d => d.city_id === cityId);
            const container = document.getElementById('cityDriversList');

            if (!cityDrivers || cityDrivers.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="padding:20px">
                        <div class="empty-state-icon">👤</div>
                        <div class="empty-state-title">No drivers bound to ${cityName}</div>
                        <div class="empty-state-text">Add drivers specifically to ${cityName} using the button below.</div>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <table class="data-table">
                    <thead><tr><th>Name</th><th>Personal ID</th><th>Status</th></tr></thead>
                    <tbody>
                        ${cityDrivers.map(d => `
                            <tr>
                                <td><strong>${d.name}</strong></td>
                                <td>${d.personal_id}</td>
                                <td><span class="badge badge-draft">📍 ${cityName}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } catch (e) {
            document.getElementById('cityDriversList').innerHTML = `<div class="text-sm" style="color:var(--accent-danger)">Failed to load drivers: ${e.message}</div>`;
        }
    }
});
