/* ==============================================================================
   Analytics Page — Canvas Heatmap Only
   ============================================================================== */

App.registerPage('analytics', {
    heatmapChart: null,

    async render(container) {
        const cities = await App.api('/api/cities');
        const now = new Date();

        const cityOptions = cities.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

        container.innerHTML = `
            <div class="section-header">
                <h1 class="section-title">Analytics</h1>
            </div>
            <div class="analytics-grid">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">City Hourly Coverage Heatmap</span>
                        <div class="flex gap-12 items-center">
                            <select class="form-select" id="analyticsCitySelect" style="width:150px" onchange="App.pages.analytics.loadHeatmap()">
                                <option value="">Select city...</option>
                                ${cityOptions}
                            </select>
                            <input class="form-input" id="analyticsMonth" style="width:110px" placeholder="MM.YYYY" value="${String(now.getMonth()+1).padStart(2,'0')}.${now.getFullYear()}" onchange="App.pages.analytics.loadHeatmap()">
                        </div>
                    </div>
                    <div class="heatmap-wrapper" id="heatmapWrapper">
                        <div class="heatmap-canvas-container">
                            <canvas id="heatmapCanvas"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (cities.length > 0) {
            document.getElementById('analyticsCitySelect').value = cities[0].id;
            this.loadHeatmap();
        }
    },

    onThemeChange() {
        this.loadHeatmap();
    },

    async loadHeatmap() {
        const cityId = document.getElementById('analyticsCitySelect')?.value;
        const monthStr = document.getElementById('analyticsMonth')?.value;
        const canvas = document.getElementById('heatmapCanvas');
        const wrapper = document.getElementById('heatmapWrapper');
        if (!canvas || !cityId || !monthStr) return;

        const parts = monthStr.split('.');
        if (parts.length !== 2) return;
        const month = parseInt(parts[0]);
        const year = parseInt(parts[1]);

        try {
            const data = await App.api('/api/analytics/coverage', {
                params: { city_id: cityId, year, month }
            });

            this.renderHeatmapCanvas(canvas, wrapper, data);

        } catch (e) {
            console.error('Heatmap error:', e);
        }
    },

    renderHeatmapCanvas(canvas, wrapper, data) {
        const isDark = App.getTheme() === 'dark';
        const ctx = canvas.getContext('2d');
        const numDays = data.num_days;
        const numSlots = data.time_labels.length;

        // Sizing
        const cellW = 34;
        const cellH = 22;
        const labelW = 50;
        const labelH = 50;
        const totalW = labelW + numSlots * cellW + 60;
        const totalH = labelH + numDays * cellH + 20;

        // Set canvas size — ensure it scrolls properly
        const dpr = window.devicePixelRatio || 1;
        canvas.width = totalW * dpr;
        canvas.height = totalH * dpr;
        canvas.style.width = totalW + 'px';
        canvas.style.height = totalH + 'px';
        ctx.scale(dpr, dpr);

        // Background
        ctx.fillStyle = isDark ? '#1E293B' : '#FFFFFF';
        ctx.fillRect(0, 0, totalW, totalH);

        // Find max value for color scaling
        let maxVal = 1;
        data.matrix.forEach(row => row.forEach(v => { if (v > maxVal) maxVal = v; }));

        // Color function
        const getColor = (val) => {
            if (val === 0) return isDark ? '#1a2332' : '#F1F5F9';
            const t = val / maxVal;
            if (isDark) {
                const r = Math.round(30 + t * 99);
                const g = Math.round(41 + t * 120);
                const b = Math.round(59 + t * 189);
                return `rgb(${r},${g},${b})`;
            } else {
                const r = Math.round(241 - t * 142);
                const g = Math.round(245 - t * 56);
                const b = Math.round(249 - t * 8);
                return `rgb(${r},${g},${b})`;
            }
        };

        // Draw time labels (top)
        ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        for (let t = 0; t < numSlots; t++) {
            if (t % 4 === 0) {
                ctx.fillText(data.time_labels[t], labelW + t * cellW + cellW / 2, labelH - 8);
            }
        }

        // Draw cells
        for (let d = 0; d < numDays; d++) {
            // Day label
            ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
            ctx.font = '11px Inter, sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(String(d + 1), labelW - 8, labelH + d * cellH + cellH / 2 + 4);

            for (let t = 0; t < numSlots; t++) {
                const val = data.matrix[d][t];
                ctx.fillStyle = getColor(val);
                ctx.fillRect(labelW + t * cellW, labelH + d * cellH, cellW - 1, cellH - 1);

                // Show number if > 0
                if (val > 0) {
                    ctx.fillStyle = isDark ? '#F1F5F9' : '#0F172A';
                    ctx.font = '9px Inter, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(val, labelW + t * cellW + cellW / 2, labelH + d * cellH + cellH / 2 + 3);
                }
            }
        }

        // Legend
        const legendY = labelH + numDays * cellH + 10;
        ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Coverage: ', labelW, legendY);

        const legendColors = [0, 1, Math.ceil(maxVal / 2), maxVal];
        legendColors.forEach((v, i) => {
            const x = labelW + 60 + i * 50;
            ctx.fillStyle = getColor(v);
            ctx.fillRect(x, legendY - 10, 14, 14);
            ctx.fillStyle = isDark ? '#94A3B8' : '#64748B';
            ctx.fillText(v.toString(), x + 18, legendY);
        });
    }
});
