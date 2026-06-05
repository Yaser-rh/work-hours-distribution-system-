# Driver Shift & Timesheet Distribution System

A professional, database-backed desktop application for managing, planning, and optimizing monthly schedules for delivery drivers. The system utilizes constraint programming (Google OR-Tools CP-SAT) to dynamically stagger shifts across operational hours, includes a beautiful Tkinter GUI with visual analytics (Matplotlib), and exports polished, audit-ready Word documents.

---

## ✨ Features

- **🧠 CP-SAT Optimization Solver**: Automatically schedules and distributes driver hours based on monthly targets, city operational hours, break rules, and shift staggering. Supports both single-driver incremental runs and city-wide batch solving.
- **🗃️ Robust SQLite Database**: Tracks cities, drivers, timesheets, and daily entries. Leverages relational constraints (foreign keys, cascading deletes, unique indexes) to prevent data corruption.
- **📊 Visual Analytics**: View real-time reports with interactive charts:
  - *Driver Monthly Hours*: Compares target vs. scheduled hours per driver.
  - *City Hourly Coverage*: Displays a coverage heatmap showing the number of scheduled drivers per hour of the day.
- **📝 Word Document Exporter (`.docx`)**: Exports schedules to professional German-locale formatted documents. Automatically localizes decimals (e.g., `6,5` instead of `6.5`), underlines employee details, and leaves off-days blank.
- **🛠️ Database Administration**: Easy database backup and validation-aware restoration features directly accessible from the GUI top menu bar.
- **🔏 Manual Editing**: Allows managers to double-click any date in the preview grid to manually adjust shifts, which locks those entries from being altered by future solver runs.
- **📦 Executable Compilation**: Contains a pre-configured PowerShell build script to compile the application into a standalone Windows binary (`.exe`) via PyInstaller.

---

## 📁 Repository Structure

```text
├── db/                     # Database layer
│   ├── database.py         # SQLite connection & initialization
│   └── models.py           # CRUD operations & relational integrity queries
├── solver/                 # Scheduler engine
│   └── sat_solver.py       # OR-Tools CP-SAT scheduler implementation
├── exporter/               # Export engine
│   └── docx_exporter.py    # python-docx template styling & generation
├── ui/                     # Graphical interface
│   ├── main_gui.py         # Tkinter layout, forms, grid preview, & threaded controllers
│   └── analytics_tab.py    # Matplotlib data visualizations
├── utils/                  # Core helpers
│   └── paths.py            # Relative path resolution for scripts vs. frozen binaries
├── tests/                  # Unit test suite
│   ├── test_database.py    # Tests for CRUD operations
│   ├── test_solver.py      # Tests for solver constraints & fallback logic
│   └── test_exporter.py    # Tests for Word formatting & locale generation
├── generate_timesheet.py   # Main application entry point script
├── build.ps1               # PyInstaller compilation script
├── user_guide.md           # Comprehensive user-facing operation guide
└── legacy code/            # Archive containing prior scripts, drafts, and mockups
```

---

## 🚀 Getting Started

### 📋 Prerequisites
- **Python**: Version `3.10` or higher.
- **Dependencies**: Install the required Python packages:
  ```bash
  pip install ortools python-docx matplotlib
  ```

### 💻 Running the Application
To launch the application from the source code, run the entry point script in the workspace root:
```bash
python generate_timesheet.py
```
*Note: If the application doesn't find `timesheets.db` in its directory on startup, it will automatically initialize a new database.*

---

## 🧪 Running Unit Tests

The test suite validates database integrity, solver constraints, and document exporting rules. Run them using `pytest`:
```bash
# Install pytest if not already installed
pip install pytest

# Execute all tests
pytest
```

---

## 📦 Building the Standalone Executable (`.exe`)

You can compile the application into a standalone Windows executable that runs on machines without Python installed. 

Run the compilation script in a PowerShell terminal:
```powershell
./build.ps1
```
Once finished, the standalone executable will be located in the `dist/` directory:
👉 **[TimesheetSystem.exe](file:///c:/Users/rh22/Desktop/excel/dist/TimesheetSystem.exe)**

---

## 📖 User Guide

For detailed operating instructions, menu guides, validation limits, and step-by-step scheduling workflows, please refer to the **[User Guide](file:///c:/Users/rh22/Desktop/excel/user_guide.md)**.
