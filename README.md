# Driver Shift & Timesheet Distribution System

A unified, high-performance scheduling and timesheet generator optimized for German labor laws (`Tätigkeitsnachweis`). The system balances shift coverage windows, respects consecutive-day limitations, and exports styled Word documents.

---

## 🚀 Application Modes

The application features a unified launcher (`main.py`) written in CustomTkinter. From here, you can launch two distinct interfaces:

### 1. Simple One-Function UI (Standalone)
A lightweight, zero-dependency desktop GUI designed for individual drivers.
* **Features**:
  * Input name, personal ID, target hours, city delivery window, month, and year.
  * Runs a **Pure Greedy Scheduling Algorithm** (Approach B) to space shifts naturally.
  * **Daily Variety**: Randomized daily start offsets (e.g. Morning `08:00`–`11:30`, Afternoon `12:00`–`15:30`) and randomized daily shift durations (e.g. some days 3.0h, others 7.0h), deterministically seeded for reproducible schedules.
  * Displays a live schedule preview in the GUI.
  * Exports directly to a styled **single-page Word document** (.docx) with German decimal formatting (e.g. `6,5` hours).
* **Dependencies**: None (pure standard Python libraries, works without `ortools` or SQLite).

### 2. Web UI (Flask Server + Optimization Solver)
A modern, responsive web dashboard built for multi-driver management.
* **Features**:
  * Powered by a **Flask REST API** backend serving a CSS/JS frontend interface.
  * Connects to a local SQLite database (`timesheets.db`) to persist drivers, cities, and timesheets.
  * Runs the **CP-SAT Mathematical Optimization Solver** (Google OR-Tools) to resolve complex, multi-agent shift allocations.
  * Staggers start times and balances delivery coverage (optimizing staggering penalties, daily distribution, and hourly smoothing).
* **Dependencies**: `flask`, `flask-cors`, `ortools`, `sqlite3`.

---

## 🛠️ Getting Started

### Prerequisites
Install the required packages in your Python environment:
```bash
pip install -r requirements.txt
```
*(If no requirements file is present, manually install `customtkinter`, `ortools`, `python-docx`, and `flask`.)*

### Running the Application
Launch the unified portal:
```bash
python main.py
```

### Compiling to Windows Executable
You can compile the entire application (including all web assets, CustomTkinter UI, and solver engines) into a standalone, single-file Windows executable:

**Using PowerShell:**
```powershell
./build.ps1
```

**Using Command Prompt / Batch:**
```cmd
build.bat
```

The standalone executable `ShiftPlan.exe` will be saved in the `dist/` directory. On execution, it runs without requiring Python to be installed and automatically initializes its local database `timesheets.db` in whichever folder it is run.

### Running Tests
Execute the automated test suite (including simple solver validations, database migrations, and Word exporter outputs) using pytest:
```bash
python -m pytest tests/
```

---

## 📂 File Structure

* **`main.py`** - Unified launcher application.
* **`build.ps1`** - PyInstaller Windows compilation script.
* **`simple/`** - Codebase for the Simple Mode (contains greedy solver and GUI classes).
* **`solver/`** - CP-SAT mathematical optimization solver engine.
* **`exporter/`** - Styles and tables formatter for `.docx` Word export.
* **`db/`** - Database connector, schemas, and models.
* **`web/`** - Static web frontend files (HTML/CSS/JS) served by Flask.
* **`tests/`** - Pytest unit test modules.
