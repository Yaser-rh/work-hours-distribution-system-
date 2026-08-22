/* ==============================================================================
   User Guide Page — Dienstplane Documentation & User Manual (EN / العربية)
   ============================================================================== */

App.registerPage('user-guide', {
    lang: 'en',

    setLang(l) {
        this.lang = l;
        const container = document.getElementById('pageContainer');
        if (container) this.render(container);
    },

    // Smooth-scrolls to a section WITHOUT touching location.hash — hash values
    // are consumed by the SPA router, so plain anchor links would navigate to
    // a non-existent page and blank the screen.
    scrollTo(id) {
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    render(container) {
        container.innerHTML = this.lang === 'ar' ? this.buildArabic() : this.buildEnglish();
    },

    tocLink(id, label) {
        const dir = this.lang === 'ar' ? 'rtl' : 'ltr';
        return `<a href="javascript:void(0)" onclick="App.pages['user-guide'].scrollTo('${id}')" dir="${dir}"
                   style="display:block;text-decoration:none;color:var(--text-secondary);padding:5px 8px;border-radius:4px;cursor:pointer"
                   onmouseover="this.style.background='var(--bg-surface)';this.style.color='var(--text-primary)'"
                   onmouseout="this.style.background='transparent';this.style.color='var(--text-secondary)'">${label}</a>`;
    },

    langButtons() {
        const en = this.lang === 'en';
        return `
            <div style="display:flex;gap:8px">
                <button onclick="App.pages['user-guide'].setLang('en')"
                    style="padding:6px 16px;border-radius:6px;border:1px solid var(--border);cursor:pointer;font-weight:600;font-size:0.85rem;
                           background:${en ? 'var(--accent-primary)' : 'transparent'};color:${en ? '#fff' : 'var(--text-secondary)'}">EN</button>
                <button onclick="App.pages['user-guide'].setLang('ar')"
                    style="padding:6px 16px;border-radius:6px;border:1px solid var(--border);cursor:pointer;font-weight:600;font-size:0.85rem;
                           background:${en ? 'transparent' : 'var(--accent-primary)'};color:${en ? 'var(--text-secondary)' : '#fff'}">عربي</button>
            </div>`;
    },

    // ==========================================================================
    //  English Version
    // ==========================================================================
    buildEnglish() {
        return `
            <div class="section-header mb-24" style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
                <div>
                    <h1 class="section-title">Dienstplane — User Guide</h1>
                    <p class="text-secondary text-sm mt-4">Everything you need to schedule drivers, distribute hours, and export timesheets.</p>
                </div>
                ${this.langButtons()}
            </div>

            <div style="display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:start">
                <!-- Table of Contents -->
                <div class="card p-16 sticky" style="top:20px">
                    <div style="font-weight:700;font-size:0.75rem;text-transform:uppercase;color:var(--text-secondary);letter-spacing:0.05em;margin-bottom:12px">Contents</div>
                    <nav style="display:flex;flex-direction:column;gap:2px;font-size:0.88rem">
                        ${this.tocLink('guide-quickstart', '1. Quick Start')}
                        ${this.tocLink('guide-overview', '2. System Overview')}
                        ${this.tocLink('guide-dashboard', '3. Dashboard')}
                        ${this.tocLink('guide-cities', '4. Cities')}
                        ${this.tocLink('guide-drivers', '5. Drivers')}
                        ${this.tocLink('guide-timesheets', '6. Timesheets & Solver')}
                        ${this.tocLink('guide-simple-gen', '7. Simple Generator')}
                        ${this.tocLink('guide-export', '8. Word & PDF Exports')}
                        ${this.tocLink('guide-analytics-logs', '9. Analytics & Logs')}
                    </nav>
                </div>

                <!-- Content -->
                <div style="display:flex;flex-direction:column;gap:24px">

                    <!-- 1. Quick Start -->
                    <div class="card p-24" id="guide-quickstart">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🚀</span>
                            <h2 class="heading-lg">1. Quick Start</h2>
                        </div>
                        <p class="text-secondary mb-12">New here? Follow these six steps in order — each one uses the tab listed on the left:</p>
                        <ol style="display:flex;flex-direction:column;gap:10px;color:var(--text-secondary);margin-left:20px">
                            <li><strong>Cities tab:</strong> create your city and set its delivery window (e.g. <code>08:00</code>–<code>22:00</code>).</li>
                            <li><strong>Drivers tab:</strong> add each driver with their name, personal ID, and home city.</li>
                            <li><strong>Timesheets tab → New:</strong> pick the city, month, and drivers, then set target hours (10–208h).</li>
                            <li><strong>Distribute:</strong> select the draft timesheets and click <strong>"Distribute Selected"</strong> — the solver fills in daily shifts automatically.</li>
                            <li><strong>Review &amp; edit:</strong> adjust any day manually if needed, then <strong>Finalize</strong> each timesheet to lock it.</li>
                            <li><strong>Export:</strong> download the finished timesheet as Word or PDF for payroll.</li>
                        </ol>
                    </div>

                    <!-- 2. Overview -->
                    <div class="card p-24" id="guide-overview">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🧭</span>
                            <h2 class="heading-lg">2. System Overview</h2>
                        </div>
                        <p class="text-secondary mb-12"><strong>Dienstplane</strong> builds monthly work schedules for delivery drivers. A Google OR-Tools (CP-SAT) optimizer distributes each driver's target hours across the month while balancing city coverage. When creating schedules, the solver automatically applies these rules:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20 mb-12" style="list-style-type:disc">
                            <li>Shift lengths between 2h and 8h in 30-minute steps.</li>
                            <li>An automatic 30-minute break on shifts of 6.5h or longer.</li>
                            <li>A maximum of 6 working days in any 7-day window — counting the previous month's last days and days worked in <em>other</em> cities too.</li>
                            <li>All shifts inside the city's delivery window, with staggered start times and even coverage across the day.</li>
                        </ul>
                        <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border-left:4px solid var(--accent-primary);font-size:0.9rem" class="text-secondary">
                            💡 <strong>Tip:</strong> the solver aims for an exact target-hours match; if the target is mathematically impossible (e.g. above the physical maximum for the month), it returns the closest feasible schedule and reports the deviation.
                        </div>
                    </div>

                    <!-- 3. Dashboard -->
                    <div class="card p-24" id="guide-dashboard">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📊</span>
                            <h2 class="heading-lg">3. Dashboard</h2>
                        </div>
                        <p class="text-secondary mb-12">Your at-a-glance overview:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Counts:</strong> cities, drivers, and timesheets split into Draft vs. Finalized.</li>
                            <li><strong>Recent Timesheets:</strong> click any entry to jump straight to it.</li>
                            <li><strong>Backup DB button</strong> (sidebar footer): saves a copy of the database into the app's <code>backups/</code> folder.</li>
                        </ul>
                    </div>

                    <!-- 4. Cities -->
                    <div class="card p-24" id="guide-cities">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🏙️</span>
                            <h2 class="heading-lg">4. Cities</h2>
                        </div>
                        <p class="text-secondary mb-12">Each city is a delivery hub with a daily operating window:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Add / Edit:</strong> city name plus opening and closing times in <code>HH:MM</code> format. The closing time must be <em>after</em> the opening time (overnight windows are not supported).</li>
                            <li><strong>Window preview:</strong> a 24h timeline bar shows the window before you save.</li>
                            <li><strong>Driver count:</strong> how many drivers are bound to the city (or have timesheets in it).</li>
                            <li>Cities with existing timesheets cannot be deleted — remove the timesheets first.</li>
                        </ul>
                    </div>

                    <!-- 5. Drivers -->
                    <div class="card p-24" id="guide-drivers">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">👤</span>
                            <h2 class="heading-lg">5. Drivers</h2>
                        </div>
                        <p class="text-secondary mb-12">Driver profiles and city assignments:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Details:</strong> full name, unique Personal ID (e.g. <code>DE-98765</code>), and home city.</li>
                            <li><strong>Search:</strong> filter the list instantly by name or ID.</li>
                            <li><strong>Auto-assign:</strong> proposes city assignments based on where each driver historically worked most — preview, then apply in bulk.</li>
                            <li>Monthly target hours are <em>not</em> set here — they are set per timesheet when you create it (see section 6).</li>
                        </ul>
                    </div>

                    <!-- 6. Timesheets & Solver -->
                    <div class="card p-24" id="guide-timesheets">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📋</span>
                            <h2 class="heading-lg">6. Timesheets &amp; Solver</h2>
                        </div>
                        <p class="text-secondary mb-12">The core workflow: create a monthly timesheet per driver, let the solver distribute the hours, then review and finalize.</p>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>🆕 Creating timesheets:</strong> pick city, month, and year; search/filter the driver list by name or ID; set one target for everyone or custom hours per driver. Targets must be <code>10–208h</code> in 0.5h steps. One timesheet per driver/city/month.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⚡ Distribute Selected:</strong> select one or more <em>draft</em> timesheets and distribute. Finalized or locked timesheets in the same city are treated as fixed — the solver schedules around them. A progress banner in the top bar shows the timer; you can switch tabs while it runs.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>✏️ Manual edits:</strong> edit a single day inline or the whole month as a table. Loose typing is fine — <code>900</code> becomes <code>09:00</code> and <code>9,30</code> becomes <code>09:30</code>. Hours must be 0–24 and the end time after the start time. On save you can <strong>lock this driver</strong> or <strong>save &amp; redistribute</strong> the others around it.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>🔒 Finalize / Lock:</strong> finalizing a timesheet locks its schedule and protects it from future batch distributions (manual remarks are preserved too). Revert to Draft to unlock it.
                            </div>
                        </div>
                    </div>

                    <!-- 7. Simple Generator -->
                    <div class="card p-24" id="guide-simple-gen">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">⚡</span>
                            <h2 class="heading-lg">7. Simple Generator</h2>
                        </div>
                        <p class="text-secondary mb-12">A quick standalone scheduler — no drivers or cities need to exist in the database. Perfect for one-off timesheets:</p>
                        <ul class="text-secondary flex flex-col gap-8 ml-20" style="list-style-type:disc">
                            <li><strong>Inputs:</strong> any driver name, personal ID, city window (<code>HH:MM</code>, end after start), month/year, and target hours (1–240h).</li>
                            <li><strong>Shift variety:</strong> choose which start categories are allowed — morning, afternoon, and evening blocks are offsets <em>relative to the city's opening time</em>, and start times are randomized within each block for a natural look.</li>
                            <li><strong>Preview:</strong> total scheduled hours, work-day count, and any deviation from the target before you export.</li>
                            <li><strong>Export:</strong> straight to Word or PDF in one click.</li>
                        </ul>
                    </div>

                    <!-- 8. Exports -->
                    <div class="card p-24" id="guide-export">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📄</span>
                            <h2 class="heading-lg">8. Word &amp; PDF Exports</h2>
                        </div>
                        <p class="text-secondary mb-12">Exports produce a formatted <em>Tätigkeitsnachweis</em> (German timesheet) ready for payroll:</p>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📄 Word (.docx):</strong> an editable document with the daily table, totals with German decimal format (e.g. <code>6,5</code>), and a signature line.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📕 PDF (.pdf):</strong> a print-ready PDF (converted via Microsoft Word when available, with a built-in fallback renderer otherwise).
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⬇️ Where files go:</strong> exported files are downloaded through your browser to its usual download folder (typically <code>Downloads</code>). Use your browser's download prompt if you want to pick a different folder. Batch export runs one download per selected timesheet.
                            </div>
                        </div>
                    </div>

                    <!-- 9. Analytics & Logs -->
                    <div class="card p-24" id="guide-analytics-logs">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📈</span>
                            <h2 class="heading-lg">9. Analytics &amp; Logs</h2>
                        </div>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div>
                                <strong>📊 Coverage heatmap:</strong> for any city and month, shows how many drivers are on shift for every half hour of every day — spot understaffed windows and overlaps at a glance.
                            </div>
                            <div>
                                <strong>📈 Driver analytics:</strong> target vs. actually scheduled hours per month for each driver.
                            </div>
                            <div>
                                <strong>📝 System logs:</strong> a live activity feed (add/edit/delete, solver runs, exports, errors) with severity filtering — refreshes automatically.
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;
    },

    // ==========================================================================
    //  Arabic Version (النسخة العربية) — keeps English UI terms as shown in the app
    // ==========================================================================
    buildArabic() {
        return `
            <div dir="rtl" lang="ar">
            <div class="section-header mb-24" style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
                <div>
                    <h1 class="section-title">Dienstplane — دليل المستخدم</h1>
                    <p class="text-secondary text-sm mt-4">كل ما تحتاجه لجدولة الورديات وتوزيع ساعات العمل وتصدير كشوف الحضور. أسماء الأقسام والأزرار مكتوبة بالإنجليزية كما تظهر في البرنامج.</p>
                </div>
                ${this.langButtons()}
            </div>

            <div style="display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:start">
                <!-- جدول المحتويات -->
                <div class="card p-16 sticky" style="top:20px">
                    <div style="font-weight:700;font-size:0.75rem;color:var(--text-secondary);letter-spacing:0.05em;margin-bottom:12px">المحتويات</div>
                    <nav style="display:flex;flex-direction:column;gap:2px;font-size:0.88rem">
                        ${this.tocLink('guide-quickstart', '١. البدء السريع')}
                        ${this.tocLink('guide-overview', '٢. نظرة عامة على النظام')}
                        ${this.tocLink('guide-dashboard', '٣. لوحة المعلومات (Dashboard)')}
                        ${this.tocLink('guide-cities', '٤. المدن (Cities)')}
                        ${this.tocLink('guide-drivers', '٥. السائقون (Drivers)')}
                        ${this.tocLink('guide-timesheets', '٦. الكشوف والمحسّن (Timesheets)')}
                        ${this.tocLink('guide-simple-gen', '٧. المولّد البسيط (Simple Generator)')}
                        ${this.tocLink('guide-export', '٨. التصدير (Word / PDF)')}
                        ${this.tocLink('guide-analytics-logs', '٩. التحليلات والسجلات (Analytics / Logs)')}
                    </nav>
                </div>

                <!-- المحتوى -->
                <div style="display:flex;flex-direction:column;gap:24px">

                    <!-- ١. البدء السريع -->
                    <div class="card p-24" id="guide-quickstart">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🚀</span>
                            <h2 class="heading-lg">١. البدء السريع</h2>
                        </div>
                        <p class="text-secondary mb-12">جديد على النظام؟ نفّذ هذه الخطوات الست بالترتيب، وستجد كل قسم في القائمة الجانبية بالاسم الإنجليزي المذكور:</p>
                        <ol style="display:flex;flex-direction:column;gap:10px;color:var(--text-secondary);margin-right:20px">
                            <li>اذهب إلى قسم المدن <strong>(Cities)</strong> وأنشئ مدينتك، وحدّد نافذة التوصيل اليومية (مثال: <code dir="ltr">08:00</code>–<code dir="ltr">22:00</code>).</li>
                            <li>اذهب إلى قسم السائقين <strong>(Drivers)</strong> وأضف كل سائق مع الاسم والرقم الشخصي <strong>(Personal ID)</strong> والمدينة التابع لها.</li>
                            <li>اذهب إلى قسم الكشوف <strong>(Timesheets)</strong> واضغط زر الإنشاء، ثم اختر المدينة والشهر والسائقين وحدّد الساعات المستهدفة (من 10 إلى 208 ساعات).</li>
                            <li>حدّد الكشوف بحالة <strong>(Draft)</strong> واضغط زر <strong>Distribute Selected</strong> — سيوزّع المحسّن الورديات اليومية تلقائياً.</li>
                            <li>راجع الجدول وعدّل ما يلزم يدوياً، ثم اضغط <strong>Finalize</strong> لتثبيت كل كشف وقفله.</li>
                            <li>اضغط <strong>Export</strong> ونزّل الكشف النهائي بصيغة Word أو PDF.</li>
                        </ol>
                    </div>

                    <!-- ٢. نظرة عامة -->
                    <div class="card p-24" id="guide-overview">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🧭</span>
                            <h2 class="heading-lg">٢. نظرة عامة على النظام</h2>
                        </div>
                        <p class="text-secondary mb-12"><strong>Dienstplane</strong> يبني جداول عمل شهرية لسائقي التوصيل. يقوم محسّن Google OR-Tools ‏(CP-SAT) بتوزيع الساعات المستهدفة لكل سائق على مدار الشهر مع موازنة التغطية داخل المدينة. عند التوزيع يطبّق النظام هذه القواعد تلقائياً:</p>
                        <ul class="text-secondary flex flex-col gap-8 mr-20 mb-12" style="list-style-type:disc">
                            <li>طول الوردية بين ساعتين و 8 ساعات بفواصل 30 دقيقة.</li>
                            <li>استراحة تلقائية 30 دقيقة للورديات من 6.5 ساعة فأكثر.</li>
                            <li>6 أيام عمل كحد أقصى في أي 7 أيام متتالية — شاملةً أيام نهاية الشهر السابق وأيام العمل في مدن أخرى.</li>
                            <li>كل الورديات داخل نافذة توصيل المدينة، مع توزيع أوقات البدء والتغطية بالتساوي على اليوم.</li>
                        </ul>
                        <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border-right:4px solid var(--accent-primary);font-size:0.9rem" class="text-secondary">
                            💡 <strong>ملاحظة:</strong> يسعى المحسّن إلى مطابقة الساعات المستهدفة بدقة؛ وإذا كان الهدف مستحيل الحساب (أعلى من الحد الأقصى الممكن للشهر) يعيد أقرب جدول ممكن مع بيان الفرق.
                        </div>
                    </div>

                    <!-- ٣. لوحة المعلومات -->
                    <div class="card p-24" id="guide-dashboard">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📊</span>
                            <h2 class="heading-lg">٣. لوحة المعلومات (Dashboard)</h2>
                        </div>
                        <p class="text-secondary mb-12">أول شاشة تراها عند فتح البرنامج، وتعطيك نظرة سريعة على كل شيء:</p>
                        <ul class="text-secondary flex flex-col gap-8 mr-20" style="list-style-type:disc">
                            <li><strong>العدّادات:</strong> عدد المدن والسائقين والكشوف، مفصولةً بين حالة <strong>Draft</strong> (مسودة) وحالة <strong>Finalized</strong> (منتهي).</li>
                            <li><strong>أحدث الكشوف (Recent):</strong> اضغط أي عنصر للانتقال إليه مباشرة.</li>
                            <li><strong>زر النسخ الاحتياطي (Backup DB):</strong> في أسفل القائمة الجانبية، يحفظ نسخة من قاعدة البيانات في مجلد <code dir="ltr">backups/</code>.</li>
                        </ul>
                    </div>

                    <!-- ٤. المدن -->
                    <div class="card p-24" id="guide-cities">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">🏙️</span>
                            <h2 class="heading-lg">٤. المدن (Cities)</h2>
                        </div>
                        <p class="text-secondary mb-12">كل مدينة هي مركز توصيل بنافذة تشغيل يومية:</p>
                        <ul class="text-secondary flex flex-col gap-8 mr-20" style="list-style-type:disc">
                            <li><strong>الإضافة والتعديل:</strong> اكتب اسم المدينة ووقت الفتح والإغلاق بصيغة <code dir="ltr">HH:MM</code>. يجب أن يكون وقت الإغلاق <em>بعد</em> وقت الفتح (النوافذ التي تعبر منتصف الليل غير مدعومة).</li>
                            <li><strong>معاينة النافذة:</strong> شريط زمني على 24 ساعة يوضح نافذة المدينة قبل الحفظ.</li>
                            <li><strong>عدد السائقين (Drivers):</strong> كم سائقاً مرتبطاً بالمدينة أو لديه كشوف فيها.</li>
                            <li>لا يمكن حذف مدينة لها كشوف قائمة — احذف كشوفها أولاً من قسم <strong>Timesheets</strong>.</li>
                        </ul>
                    </div>

                    <!-- ٥. السائقون -->
                    <div class="card p-24" id="guide-drivers">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">👤</span>
                            <h2 class="heading-lg">٥. السائقون (Drivers)</h2>
                        </div>
                        <p class="text-secondary mb-12">إدارة ملفات السائقين وربطهم بالمدن:</p>
                        <ul class="text-secondary flex flex-col gap-8 mr-20" style="list-style-type:disc">
                            <li><strong>البيانات:</strong> الاسم الكامل، رقم شخصي فريد <strong>(Personal ID)</strong> مثل <code dir="ltr">DE-98765</code>، والمدينة التابع لها.</li>
                            <li><strong>البحث (Search):</strong> تصفية القائمة فوراً بالاسم أو الرقم.</li>
                            <li><strong>الربط التلقائي (Auto-assign):</strong> يقترح مدينة لكل سائق بناءً على المدينة التي عمل فيها أكثر — راجع المقترحات ثم طبّقها للجميع بضغطة واحدة.</li>
                            <li>الساعات المستهدفة الشهرية <em>لا</em> تُحدَّد هنا، بل عند إنشاء كل كشف في قسم <strong>Timesheets</strong> (القسم ٦).</li>
                        </ul>
                    </div>

                    <!-- ٦. الكشوف والمحسّن -->
                    <div class="card p-24" id="guide-timesheets">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📋</span>
                            <h2 class="heading-lg">٦. الكشوف والمحسّن (Timesheets)</h2>
                        </div>
                        <p class="text-secondary mb-12">هذا هو سير العمل الأساسي: أنشئ كشفاً شهرياً لكل سائق، دع المحسّن يوزّع الساعات، ثم راجع وأنهِ الكشف.</p>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>🆕 إنشاء الكشوف:</strong> اختر المدينة والشهر والسنة، ثم ابحث في قائمة السائقين بالاسم أو الرقم، وحدّد هدفاً واحداً للجميع أو ساعات خاصة لكل سائق. يجب أن تكون الساعات بين 10 و 208 بخطوات 0.5. يُسمح بكشف واحد فقط لكل سائق/مدينة/شهر.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⚡ التوزيع (Distribute Selected):</strong> حدّد كشفاً أو أكثر بحالة Draft واضغط <strong>Distribute Selected</strong>. الكشوف المنتهية أو المقفلة في نفس المدينة تُعامل كثوابت ويجدول المحسّن حولها. يظهر شريط تقدم مع مؤقّت أعلى الشاشة، ويمكنك التنقل بين الأقسام أثناء التشغيل.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>✏️ التعديل اليدوي:</strong> عدّل يوماً واحداً بالنقر عليه، أو الشهر كله من وضع تحرير الجدول. الكتابة الحرة مقبولة — <code dir="ltr">900</code> تصبح <code dir="ltr">09:00</code> و <code dir="ltr">9,30</code> تصبح <code dir="ltr">09:30</code>. الساعات يجب أن تكون بين 0 و 24، ووقت النهاية بعد وقت البداية. عند الحفظ اختر <strong>Lock This Driver &amp; Save</strong> لقفل السائق، أو <strong>Save &amp; Redistribute Others</strong> لإعادة توزيع الباقين حوله.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>🔒 الإنهاء والقفل (Finalize):</strong> الضغط على <strong>Finalize</strong> يثبّت جدول الكشف ويحميه من أي توزيع جماعي لاحق (وتُحفظ الملاحظات اليدوية أيضاً). أعده إلى <strong>Draft</strong> لفك القفل.
                            </div>
                        </div>
                    </div>

                    <!-- ٧. المولّد البسيط -->
                    <div class="card p-24" id="guide-simple-gen">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">⚡</span>
                            <h2 class="heading-lg">٧. المولّد البسيط (Simple Generator)</h2>
                        </div>
                        <p class="text-secondary mb-12">مجدّول سريع ومستقل — لا يحتاج إلى تسجيل سائقين أو مدن مسبقاً. مناسب جداً لكشف واحد لمرة واحدة:</p>
                        <ul class="text-secondary flex flex-col gap-8 mr-20" style="list-style-type:disc">
                            <li><strong>المدخلات:</strong> أي اسم سائق ورقم شخصي ونافذة مدينة (<code dir="ltr">HH:MM</code>، النهاية بعد البداية) والشهر والسنة والساعات المستهدفة (من 1 إلى 240 ساعة).</li>
                            <li><strong>تنويع الورديات:</strong> فعّل فئات البدء المسموحة — <strong>Morning</strong> و <strong>Afternoon</strong> و <strong>Evening</strong> — وهي إزاحات نسبية إلى وقت فتح المدينة، وتُوزَّع أوقات البدء عشوائياً داخل كل فئة لتبدو الجداول طبيعية.</li>
                            <li><strong>المعاينة:</strong> إجمالي الساعات المجدولة وعدد أيام العمل والفرق عن الهدف — كل ذلك قبل التصدير.</li>
                            <li><strong>التصدير:</strong> مباشرة إلى Word أو PDF بنقرة واحدة.</li>
                        </ul>
                    </div>

                    <!-- ٨. التصدير -->
                    <div class="card p-24" id="guide-export">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📄</span>
                            <h2 class="heading-lg">٨. التصدير (Word / PDF)</h2>
                        </div>
                        <p class="text-secondary mb-12">ينتج التصدير كشف حضور بالصيغة الألمانية <em>(Tätigkeitsnachweis)</em> جاهزاً للرواتب:</p>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📄 ملف Word ‏(.docx):</strong> مستند قابل للتحرير فيه جدول الأيام والمجاميع بالتنسيق العشري الألماني (مثل <code dir="ltr">6,5</code>) وخانة التوقيع.
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>📕 ملف PDF ‏(.pdf):</strong> نسخة جاهزة للطباعة (تُحوَّل عبر Microsoft Word عند توفره، ومع محوّل بديل مدمج إذا لم يكن متوفراً).
                            </div>
                            <div style="background:var(--bg-surface);padding:12px 16px;border-radius:8px;border:1px solid var(--border)">
                                <strong>⬇️ مكان حفظ الملفات:</strong> تُنزَّل الملفات عبر المتصفح إلى مجلد التنزيلات المعتاد (عادةً <code dir="ltr">Downloads</code>). استخدم نافذة التنزيل في المتصفح لاختيار مجلد آخر. التصدير لعدة كشوف معاً ينزّل ملفاً لكل كشف.
                            </div>
                        </div>
                    </div>

                    <!-- ٩. التحليلات والسجلات -->
                    <div class="card p-24" id="guide-analytics-logs">
                        <div class="flex items-center gap-12 mb-12">
                            <span style="font-size:1.5rem">📈</span>
                            <h2 class="heading-lg">٩. التحليلات والسجلات (Analytics / System Logs)</h2>
                        </div>
                        <div style="display:flex;flex-direction:column;gap:12px" class="text-secondary">
                            <div>
                                <strong>📊 خريطة التغطية (Coverage Heatmap):</strong> في قسم <strong>Analytics</strong>، تعرض لكل مدينة وشهر عدد السائقين في الوردية عند كل نصف ساعة من كل يوم — لتلاحظ ساعات نقص التغطية أو التكدس بنظرة واحدة.
                            </div>
                            <div>
                                <strong>📈 إحصاءات السائق:</strong> مقارنة الساعات المستهدفة بالمجدولة فعلياً لكل شهر.
                            </div>
                            <div>
                                <strong>📝 سجلات النظام (System Logs):</strong> سجل مباشر لكل العمليات (إضافة/تعديل/حذف، تشغيل المحسّن، التصدير، الأخطاء) مع تصفية حسب النوع — يتحدّث تلقائياً.
                            </div>
                        </div>
                    </div>

                </div>
            </div>
            </div>
        `;
    }
});
