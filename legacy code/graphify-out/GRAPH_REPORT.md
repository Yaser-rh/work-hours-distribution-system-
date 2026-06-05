# Graph Report - excel  (2026-06-05)

## Corpus Check
- 41 files · ~43,337 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 511 nodes · 643 edges · 39 communities (33 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `949637f1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]

## God Nodes (most connected - your core abstractions)
1. `TimesheetAppGUI` - 46 edges
2. `get_connection()` - 22 edges
3. `Module 4: GUI Dashboard` - 11 edges
4. `TimesheetAppGUI` - 10 edges
5. `Phase 4: Implementation Roadmap` - 9 edges
6. `Module 2: CP-SAT Hour Distribution Solver` - 9 edges
7. `Timesheet & Driver Shift Distribution System - Plan` - 9 edges
8. `solve()` - 8 edges
9. `AnalyticsTab` - 8 edges
10. `Driver Shift & Timesheet Distribution System - User Guide` - 8 edges

## Surprising Connections (you probably didn't know these)
- `api_restore()` --calls--> `initialize_database()`  [INFERRED]
  app.py → db/database.py
- `main()` --calls--> `initialize_database()`  [INFERRED]
  generate_timesheet.py → db/database.py
- `TimesheetAppGUI` --uses--> `AnalyticsTab`  [INFERRED]
  ui/main_gui.py → ui/analytics_tab.py
- `In-Memory Array Calculation` --rationale_for--> `legacy code/gg22_improved.txt`  [INFERRED]
  legacy code/gg22_explanation.md → legacy code/gg22_improved.txt
- `Mathematical Feasibility Pre-Check` --rationale_for--> `legacy code/gg22_improved.txt`  [INFERRED]
  legacy code/gg22_explanation.md → legacy code/gg22_improved.txt

## Hyperedges (group relationships)
- **Database Layer** — db_database_py, db_models_py [EXTRACTED 0.95]
- **Scheduling Core and Evolution** — solver_sat_solver_py, legacy_gg22_improved_txt, future_improvements_md [INFERRED 0.85]
- **Tkinter Graphical User Interface** — ui_main_gui_py, ui_analytics_tab_py [EXTRACTED 0.95]

## Communities (39 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (8): Setup a collapsible log console at the bottom., Runs the CP-SAT solver in a background thread and updates the UI progress indica, Collapses or expands the logs panel to save screen space., Thread-safe logging into bottom console., Creates a header bar with application title and dark/light mode toggle., Toggles application appearance between Dark and Light mode., Styles the native TTK Treeview widgets dynamically to fit CustomTkinter theme., TimesheetAppGUI

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (51): get_connection(), initialize_database(), Initializes the SQLite database, creating the schema tables if they do not exist, Returns a sqlite3 connection with foreign keys enabled., add_city(), add_employee(), backup_database(), clock_to_units() (+43 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (25): check_6_day_rule(), distribute_monthly_hours(), format_hours_german(), generate_docx_timesheet(), main(), parse_month_year(), print_premium_banner(), process_single_month() (+17 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (27): legacy code/gg22_explanation.md, legacy code/gg22_improved.txt, Auto-Break Rule, Clustered Sequential Batching, 6-Consecutive-Day Limit, Ergonomic Scheduling Heuristics, In-Memory Array Calculation, Mathematical Feasibility Pre-Check (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.21
Nodes (6): format_hours_german(), generate_docx(), Generates the styled Tätigkeitsnachweis Word document.     Returns the absolute, Formats hours with German decimal comma (e.g. 6.0 -> 6, 4.5 -> 4,5).     If hour, AnalyticsTab, Helper to style the matplotlib figure colors to fit Light or Dark theme.

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (14): 📦 Building the Standalone Executable (`.exe`), code:text (├── db/                     # Database layer), code:bash (pip install ortools python-docx matplotlib), code:bash (python generate_timesheet.py), code:bash (# Install pytest if not already installed), code:powershell (./build.ps1), Driver Shift & Timesheet Distribution System, ✨ Features (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (39): code:mermaid (graph LR), Dependency Graph, Implementation Order Summary, ✅ Module 1 Checkpoint, Module 1: Database & CRUD Layer, ✅ Module 2 Checkpoint, Module 2: CP-SAT Hour Distribution Solver, ✅ Module 3 Checkpoint (+31 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (38): 1. Automated Tests, 1. Core Views & CRUD Operations, 1. Shift Durations, 2. Auto-Break Rule, 2. Manual Verification, 2. Post-Solver Manual Edit Workflow `[NEW]`, 3. Draft / Finalized Workflow `[NEW]`, 3. Workday Constraints (+30 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (32): 1. System Architecture, 2.1 Transaction Pattern, 2.2 Deletion Integrity, 2.3 Schema DDL, 2.4 Backup & Restore Protocol, 2. Database Safety Measures, 3.1 Integer Scaling Convention, 3.2 Decision Variables (+24 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (5): api_create_timesheets(), api_solve(), Flask REST API backend for the Driver Shift & Timesheet Distribution System. Wra, Create one or more timesheets. Accepts a list of {employee_id, city_id, year, mo, Solve for the given timesheet IDs.     Expects: { timesheet_ids: [int], redistri

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (19): cancelTableEdit(), createTimesheets(), distributeSelected(), exportSelected(), exportTimesheet(), loadTimesheets(), openNewModal(), render() (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.1
Nodes (19): 1. Identifying Potential Workdays (Pass 1), 1. In-Memory Array Calculation (VBA Speed Up), 2. Mathematical Feasibility Pre-Check (Zero-Freeze Guard), 2. Weighted Initial Hours Allocation (Pass 2), 3. Ergonomic Scheduling Heuristics (Clean Shifts), 3. Fine-Tuning Adjustment Loop (Pass 3), 4. Real-time Status Bar Progress Reports, code:block1 (Block 1 (Feb 2024)                  Block 2 (Mar 2024)) (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.1
Nodes (19): 5.1 `db/database.py`, 5.2 `db/models.py`, 5.3 `solver/sat_solver.py`, 5.4 `exporter/docx_exporter.py`, 5.5 `utils/paths.py`, 5. Module Interface Contracts, Backup, Cities (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.12
Nodes (17): 1. Cities Tab, 2. Drivers Tab, 3. Timesheets Tab & Actions, Action Buttons, 📊 Analytics Tab, code:powershell (python generate_timesheet.py), 🗃️ Database Tools (Top Menu Bar), Driver Shift & Timesheet Distribution System - User Guide (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (11): 1. Batch Mode (Globally Joint Optimization), 2. Incremental Mode (Consecutive 1-by-1 Optimization), Advantages of This Design, code:block1 ([All Active Drivers (e.g., 30)]), code:python (def solve(solver_input: SolverInput) -> SolverResult:), code:python (def _solve_clustered_batches(solver_input: SolverInput) -> S), 📈 Current Performance & Scaling Findings, 🧠 Future Improvement Blueprint: Clustered Sequential Batching (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.31
Nodes (7): filterList(), loadDrivers(), openAddModal(), openDriverModal(), openEditModal(), render(), renderList()

### Community 26 - "Community 26"
Cohesion: 0.36
Nodes (5): loadCities(), openAddModal(), openCityModal(), openEditModal(), render()

### Community 27 - "Community 27"
Cohesion: 0.57
Nodes (6): getChartColors(), loadDriverChart(), loadHeatmap(), onThemeChange(), render(), renderHeatmapCanvas()

### Community 28 - "Community 28"
Cohesion: 0.83
Nodes (3): animateCounter(), loadStats(), render()

## Knowledge Gaps
- **133 isolated node(s):** `DriverSpec`, `SolverInput`, `App`, `1. Batch Mode (Globally Joint Optimization)`, `2. Incremental Mode (Consecutive 1-by-1 Optimization)` (+128 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TimesheetAppGUI` connect `Community 0` to `Community 4`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `api_restore()` connect `Community 1` to `Community 19`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `get_connection()` (e.g. with `add_city()` and `get_cities()`) actually correct?**
  _`get_connection()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Flask REST API backend for the Driver Shift & Timesheet Distribution System. Wra`, `Create one or more timesheets. Accepts a list of {employee_id, city_id, year, mo`, `Solve for the given timesheet IDs.     Expects: { timesheet_ids: [int], redistri` to the rest of the system?**
  _200 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._