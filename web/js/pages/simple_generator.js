/* ==============================================================================
   Simple Generator Page — Standalone Pure Greedy Scheduler
   ============================================================================== */

App.registerPage('simple-generator', {
    cities: [],
    lastResult: null,

    async render(container) {
        this.cities = await App.api('/api/cities');

        const cityOptions = this.cities.map(c => `<option value="${c.id}" data-start="${c.start_time}" data-end="${c.end_time}">${c.name} (${c.start_time}–${c.end_time})</option>`).join('');
        const now = new Date();
        const curMonth = now.getMonth() + 1;
        const curYear = now.getFullYear();

        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Simple One-Click Generator</h1>
            </div>
            <div class="ts-layout">
                <!-- Form Configuration Card -->
                <div class="card p-24" style="flex:0.4;min-width:320px">
                    <h3 class="heading-md mb-16">Driver & Shift Details</h3>
                    <div class="form-group">
                        <label class="form-label">Driver Name</label>
                        <input type="text" class="form-input" id="sgDriverName" placeholder="e.g. Max Mustermann" value="Max Mustermann">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Personal ID</label>
                        <input type="text" class="form-input" id="sgPersonalId" placeholder="e.g. DE-98765" value="DE-98765">
                    </div>
                    <div class="form-group">
                        <label class="form-label">City Preset</label>
                        <select class="form-select" id="sgCitySelect" onchange="App.pages['simple-generator'].onCitySelect()">
                            <option value="custom">Custom City Window...</option>
                            ${cityOptions}
                        </select>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">City Start Time</label>
                            <input type="time" class="form-input" id="sgStartTime" value="08:00">
                        </div>
                        <div class="form-group">
                            <label class="form-label">City End Time</label>
                            <input type="time" class="form-input" id="sgEndTime" value="22:00">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Target Hours</label>
                            <input type="number" step="0.5" min="10" max="208" class="form-input" id="sgTargetHours" value="120.0">
                        </div>
                        <div class="form-group" style="flex:0.5">
                            <label class="form-label">Month</label>
                            <select class="form-select" id="sgMonth">
                                ${Array.from({length:12}, (_,i) => `<option value="${i+1}" ${i+1===curMonth?'selected':''}>${String(i+1).padStart(2,'0')}</option>`).join('')}
                            </select>
                        </div>
                        <div class="form-group" style="flex:0.5">
                            <label class="form-label">Year</label>
                            <select class="form-select" id="sgYear">
                                <option value="${curYear}">${curYear}</option>
                                <option value="${curYear+1}">${curYear+1}</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Shift Start Variety</label>
                        <div class="flex flex-col gap-8 mt-4">
                            <label style="display:flex;align-items:center;gap:8px;font-size:0.88rem;cursor:pointer">
                                <input type="checkbox" id="sgAllowMorning" checked style="accent-color:var(--accent-primary)"> Morning Start (08:00 + offset)
                            </label>
                            <label style="display:flex;align-items:center;gap:8px;font-size:0.88rem;cursor:pointer">
                                <input type="checkbox" id="sgAllowAfternoon" checked style="accent-color:var(--accent-primary)"> Afternoon Start (12:00 + offset)
                            </label>
                            <label style="display:flex;align-items:center;gap:8px;font-size:0.88rem;cursor:pointer">
                                <input type="checkbox" id="sgAllowEvening" checked style="accent-color:var(--accent-primary)"> Evening Start (16:00 + offset)
                            </label>
                        </div>
                    </div>
                    <button class="btn btn-primary w-full mt-16" id="sgGenerateBtn" onclick="App.pages['simple-generator'].generate()">
                        ⚡ Generate Schedule
                    </button>
                </div>

                <!-- Preview & Summary Panel -->
                <div class="card ts-detail-panel" id="sgResultPanel">
                    <div class="empty-state">
                        <div class="empty-state-icon">⚡</div>
                        <div class="empty-state-title">No Schedule Generated Yet</div>
                        <div class="empty-state-text">Configure driver parameters on the left and click "Generate Schedule" to compute a randomized greedy schedule.</div>
                    </div>
                </div>
            </div>
        `;
    },

    onCitySelect() {
        const select = document.getElementById('sgCitySelect');
        const opt = select.options[select.selectedIndex];
        if (opt && opt.value !== 'custom') {
            document.getElementById('sgStartTime').value = opt.dataset.start || '08:00';
            document.getElementById('sgEndTime').value = opt.dataset.end || '22:00';
        }
    },

    async generate() {
        const btn = document.getElementById('sgGenerateBtn');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Generating...'; }

        try {
            const targetHours = parseFloat(document.getElementById('sgTargetHours').value) || 120.0;
            const startTime = document.getElementById('sgStartTime').value || '08:00';
            const endTime = document.getElementById('sgEndTime').value || '22:00';
            const year = parseInt(document.getElementById('sgYear').value);
            const month = parseInt(document.getElementById('sgMonth').value);
            const allowMorning = document.getElementById('sgAllowMorning').checked;
            const allowAfternoon = document.getElementById('sgAllowAfternoon').checked;
            const allowEvening = document.getElementById('sgAllowEvening').checked;

            const res = await App.api('/api/simple-generator/generate', {
                method: 'POST',
                body: {
                    target_hours: targetHours,
                    city_start_time: startTime,
                    city_end_time: endTime,
                    year: year,
                    month: month,
                    allow_morning: allowMorning,
                    allow_afternoon: allowAfternoon,
                    allow_evening: allowEvening
                }
            });

            this.lastResult = res;
            this.renderResult(res);
            App.toast(`Generated ${res.scheduled_hours} hours over ${res.work_days_count} work days.`, 'success');

        } catch (e) {
            App.toast('Generation failed: ' + e.message, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '⚡ Generate Schedule'; }
        }
    },

    renderResult(res) {
        const panel = document.getElementById('sgResultPanel');
        if (!panel) return;

        const driverName = document.getElementById('sgDriverName').value.trim() || 'Driver';
        const personalId = document.getElementById('sgPersonalId').value.trim() || 'DE-000';

        const citySelect = document.getElementById('sgCitySelect');
        const cityName = citySelect.options[citySelect.selectedIndex]?.text.split(' (')[0] || 'Custom City';

        const rows = res.daily_entries.map(e => `
            <tr>
                <td>${e.work_date}</td>
                <td>${e.start_time || '—'}</td>
                <td>${e.end_time || '—'}</td>
                <td>${e.break_duration || '—'}</td>
                <td style="font-weight:600">${e.hours_worked > 0 ? e.hours_worked.toFixed(1).replace('.', ',') : '—'}</td>
            </tr>
        `).join('');

        panel.innerHTML = `
            <div class="ts-detail-header mb-16">
                <div>
                    <h2 class="heading-lg">${driverName} (${personalId})</h2>
                    <div class="text-sm text-secondary">${cityName} • ${document.getElementById('sgMonth').value}/${document.getElementById('sgYear').value}</div>
                </div>
                <div class="flex gap-8">
                    <button class="btn btn-primary btn-sm" onclick="App.pages['simple-generator'].exportFile('docx')">📄 Export Word (.docx)</button>
                    <button class="btn btn-ghost btn-sm" onclick="App.pages['simple-generator'].exportFile('pdf')">📕 Export PDF (.pdf)</button>
                </div>
            </div>

            <div class="stats-grid mb-16" style="grid-template-columns: repeat(3, 1fr);">
                <div class="stat-card">
                    <div class="stat-label">Scheduled Hours</div>
                    <div class="stat-value" style="color:var(--accent-primary)">${res.scheduled_hours}h</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Work Days</div>
                    <div class="stat-value">${res.work_days_count}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Target Gap</div>
                    <div class="stat-value" style="color:${res.deviation===0 ? 'var(--accent-success)' : 'var(--accent-warning)'}">${res.deviation >= 0 ? '+' : ''}${res.deviation}h</div>
                </div>
            </div>

            <div class="table-container" style="max-height: 480px; overflow-y: auto;">
                <table class="table" style="font-size:0.88rem">
                    <thead>
                        <tr>
                            <th>Datum</th>
                            <th>Arbeitsbeginn</th>
                            <th>Arbeitsende</th>
                            <th>Pause</th>
                            <th>Arbeitszeit</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;
    },

    async exportFile(format) {
        if (!this.lastResult) {
            App.toast('Generate a schedule first.', 'warning');
            return;
        }

        const driverName = document.getElementById('sgDriverName').value.trim() || 'Driver';
        const personalId = document.getElementById('sgPersonalId').value.trim() || 'DE-000';
        const citySelect = document.getElementById('sgCitySelect');
        const cityName = citySelect.options[citySelect.selectedIndex]?.text.split(' (')[0] || 'Custom City';
        const year = parseInt(document.getElementById('sgYear').value);
        const month = parseInt(document.getElementById('sgMonth').value);
        const targetHours = parseFloat(document.getElementById('sgTargetHours').value) || 120.0;

        try {
            const cfg = App.getExportConfig();
            const res = await App.api('/api/simple-generator/export', {
                method: 'POST',
                body: {
                    employee_name: driverName,
                    personal_id: personalId,
                    city_name: cityName,
                    year: year,
                    month: month,
                    target_hours: targetHours,
                    daily_entries: this.lastResult.daily_entries,
                    format: format,
                    save_dir: cfg.dir
                }
            });

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const cleanName = driverName.replace(/[^a-zA-Z0-9]/g, '_');
            const ext = format === 'pdf' ? '.pdf' : '.docx';
            a.download = `timesheet_${cleanName}_${month.toString().padStart(2, '0')}_${year}${ext}`;
            a.click();
            URL.revokeObjectURL(url);
            App.toast(`Exported to ${format.toUpperCase()} document.`, 'success');

        } catch (e) {
            App.toast('Export failed: ' + e.message, 'error');
        }
    }
});
