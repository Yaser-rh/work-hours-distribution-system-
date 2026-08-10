/* ==============================================================================
   User Guide Page — Dienstplane Documentation & User Manual
   ============================================================================== */

App.registerPage('user-guide', {
    render(container) {
        container.innerHTML = `
            <div class="section-header mb-24">
                <div>
                    <h1 class="section-title">Dienstplane — User Guide & Documentation</h1>
                    <p class="text-secondary text-sm mt-4">Learn how to use every feature, solver option, and export tool in the Dienstplane system.</p>
                </div>
            </div>

            <div style="display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:start">
                <!-- Navigation Table of Contents -->
                <div class="card p-16 sticky" style="top:20px">
                    <div style="font-weight:700;font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);letter-spacing:0.05em;margin-bottom:12px">Table of Contents</div>
                    <nav class="flex flex-col gap-8" style="font-size:0.88rem">
                        <a href="#guide-overview" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">1. System Overview</a>
                        <a href="#guide-dashboard" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">2. Dashboard</a>
                        <a href="#guide-cities" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">3. Cities Management</a>
                        <a href="#guide-drivers" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">4. Drivers Management</a>
                        <a href="#guide-timesheets" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">5. Timesheets & Solver</a>
                        <a href="#guide-simple-gen" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">6. Simple Generator</a>
                        <a href="#guide-export" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">7. Word & PDF Exports</a>
                        <a href="#guide-save-settings" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">8. Directory & Slider Settings</a>
                        <a href="#guide-analytics-logs" class="link-muted" style="text-decoration:none;padding:4px 8px;border-radius:4px">9. Analytics & Logs</a>
                    </nav>
                </div>

                <!-- Main Documentation Content -->
                <div class="flex flex-col gap-24">
                    <!-- Section 1: Overview -->
                    <div class="card p-24" id="guide-overview">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🚀</span>
                            <h2 class="heading-lg">1. System Overview</h2>
                        </div>
                        <p class="text-secondary mb-12"><strong>Dienstplane</strong> is a professional driver shift scheduling and monthly timesheet distribution platform designed for delivery fleet managers. It combines constraint programming (OR-Tools CP-SAT) with a standalone greedy generator to create legally compliant, balanced monthly work schedules.</p>
                        <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border-left:4px solid var(--accent-primary);font-size:0.9rem">
                            💡 <strong>Key Benefit:</strong> Distribute hundreds of driver hours in seconds while automatically enforcing German labor laws (10h max daily shift, 11h mandatory rest between shifts, Sunday work restrictions, and break rules).
                        </div>
                    </div>

                    <!-- Section 2: Dashboard -->
                    <div class="card p-24" id="guide-dashboard">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📊</span>
                            <h2 class="heading-lg">2. Dashboard</h2>
                        </div>
                        <p class="text-secondary mb-12">The Dashboard provides high-level key performance indicators (KPIs) and real-time overview metrics:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20 mb-12" style="list-style-type:disc">
                            <li><strong>Active Cities Count:</strong> Total registered delivery hubs.</li>
                            <li><strong>Total Drivers:</strong> Registered fleet workforce size.</li>
                            <li><strong>Active Timesheets & Finalized Status:</strong> Count of draft vs locked/finalized monthly timesheets.</li>
                            <li><strong>Recent Activity List:</strong> Quick click-through access to recent timesheet files.</li>
                            <li><strong>Database Backup Button:</strong> Located in the sidebar footer to export safety backups of <code>timesheets.db</code>.</li>
                        </ul>
                    </div>

                    <!-- Section 3: Cities -->
                    <div class="card p-24" id="guide-cities">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🏙️</span>
                            <h2 class="heading-lg">3. Cities Management</h2>
                        </div>
                        <p class="text-secondary mb-12">Configure city delivery hubs and their operational windows:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Add / Edit Cities:</strong> Define city name, daily opening time (e.g. <code>08:00</code>), and closing time (e.g. <code>22:00</code>).</li>
                            <li><strong>Operating Window Visualizer:</strong> Displays a 24-hour visual timeline bar showing the city shift boundaries.</li>
                            <li><strong>Driver Count:</strong> Tracks how many drivers are assigned to each city hub.</li>
                        </ul>
                    </div>

                    <!-- Section 4: Drivers -->
                    <div class="card p-24" id="guide-drivers">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">👤</span>
                            <h2 class="heading-lg">4. Drivers Management</h2>
                        </div>
                        <p class="text-secondary mb-12">Manage driver profiles and monthly work contracts:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Personal Details:</strong> Driver Full Name, Personal ID number (e.g. <code>DE-98765</code>), and assigned home city.</li>
                            <li><strong>Contract Target Hours:</strong> Set standard target hours per month (e.g. <code>120.0h</code> or <code>160.0h</code>).</li>
                            <li><strong>Driver Search:</strong> Filter driver profiles instantly by name or ID.</li>
                        </ul>
                    </div>

                    <!-- Section 5: Timesheets & CP-SAT Solver -->
                    <div class="card p-24" id="guide-timesheets">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📋</span>
                            <h2 class="heading-lg">5. Timesheets & CP-SAT Solver</h2>
                        </div>
                        <p class="text-secondary mb-12">Create, optimize, and edit monthly driver timesheets:</p>
                        <div class="flex flex-col gap-12 text-secondary">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>🆕 Real-Time Driver Search in New Timesheet Modal:</strong><br>
                                When creating a new timesheet, use the search box at the top of the driver selection list to instantly filter drivers by name or ID without losing checkbox selections or target hour overrides.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⚡ CP-SAT Hours Distribution:</strong><br>
                                Select one or multiple draft timesheets and click <strong>"Distribute Selected"</strong>. Google OR-Tools CP-SAT engine will compute optimal daily shift start times, shift lengths, and legally required break durations.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⏱️ Persistent Topbar Loading Banner & Timer:</strong><br>
                                When solving starts, a live progress banner appears in the topbar header displaying an animated pulse dot, elapsed timer (<code>00:15 / 30s</code>), and progress bar. You can navigate away to any tab — the solver keeps running in the background and notifies you when finished!
                            </div>
                        </div>
                    </div>

                    <!-- Section 6: Simple Generator -->
                    <div class="card p-24" id="guide-simple-gen">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">⚡</span>
                            <h2 class="heading-lg">6. Simple One-Click Generator</h2>
                        </div>
                        <p class="text-secondary mb-12">The <strong>Simple Generator</strong> tab provides a fast, standalone greedy scheduler that generates schedules on the fly without needing to store drivers or cities in the database:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Custom Inputs:</strong> Enter any Driver Name, Personal ID, City operating window, and target hours.</li>
                            <li><strong>Shift Start Variety Checkboxes:</strong> Enable Morning (08:00+), Afternoon (12:00+), or Evening (16:00+) shift start preference offsets.</li>
                            <li><strong>Instant Schedule Preview & Stats:</strong> View calculated total scheduled hours, work days count, and target deviation gap.</li>
                            <li><strong>Direct Export:</strong> Export directly to Word (.docx) or PDF (.pdf) with a single click.</li>
                        </ul>
                    </div>

                    <!-- Section 7 & 8: Exporting & Directory Settings -->
                    <div class="card p-24" id="guide-export">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📄</span>
                            <h2 class="heading-lg">7. Word & PDF Exports</h2>
                        </div>
                        <p class="text-secondary mb-12">Dienstplane supports official document exports for payroll and record-keeping:</p>
                        <div class="flex flex-col gap-12 text-secondary mb-16">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📄 Microsoft Word (.docx):</strong> Generates standard formatted Word document tables matching German timesheet regulations.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📕 PDF Document (.pdf):</strong> Converts the timesheet into a clean printable PDF (using ReportLab / Microsoft Word COM).
                            </div>
                        </div>

                        <div id="guide-save-settings" style="border-top:1px solid var(--border);padding-top:16px">
                            <h3 class="heading-md mb-12">8. Save Location & Slider Toggle Settings</h3>
                            <p class="text-secondary mb-12">When clicking <strong>Export</strong>, the Export Options modal presents three actions and a toggle slider:</p>
                            <ul class="text-secondary flex flex-col gap-8 ml-20 mb-12" style="list-style-type:disc">
                                <li><strong>Option 1 (Word .docx):</strong> Export document as editable Word file.</li>
                                <li><strong>Option 2 (PDF .pdf):</strong> Export document as printable PDF file.</li>
                                <li><strong>Option 3 (📂 Change Save Location):</strong> Opens a prompt allowing you to specify any folder path on your computer (e.g. <code>C:\\Users\\Username\\Desktop\\Exports</code>).</li>
                                <li><strong>Remember Save Directory Toggle Slider:</strong>
                                    <ul style="list-style-type:circle;margin-left:20px;margin-top:6px" class="flex flex-col gap-4">
                                        <li><span class="chip chip-lime-keyword">Slid RIGHT (ON)</span>: Remembers the save folder and format in preferences. All future exports automatically save directly to this folder without asking!</li>
                                        <li><span style="background:var(--border-strong);padding:2px 8px;border-radius:4px;font-size:0.8rem">Slid LEFT (OFF)</span>: Asks for format and save directory every time.</li>
                                    </ul>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!-- Section 9: Analytics & Logs -->
                    <div class="card p-24" id="guide-analytics-logs">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📈</span>
                            <h2 class="heading-lg">9. Analytics & System Logs</h2>
                        </div>
                        <div class="text-secondary flex flex-col gap-12">
                            <div>
                                <strong>📊 Hourly Coverage Heatmap (Analytics):</strong> Visualizes city delivery coverage for every hour of the month to identify understaffed windows or peak shift overlaps.
                            </div>
                            <div>
                                <strong>📝 System Logs:</strong> Live diagnostic logs showing backend API execution, solver search iterations, database operations, and error traces with level filtering (INFO, WARNING, ERROR).
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
    }
});
