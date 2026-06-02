# Driver Shift & Timesheet Distribution System - User Guide

Welcome to the **Driver Shift & Timesheet Distribution System**. This system is a database-backed desktop application designed to schedule monthly working hours for multiple drivers, optimize shift staggering, and export styled, audit-ready Word documents (`.docx`).

---

## 🚀 Getting Started

### Launching the Application
You can run the application in one of two ways:
* **As a Standalone Executable**: Double-click the compiled binary [TimesheetSystem.exe](file:///c:/Users/rh22/Desktop/excel/dist/TimesheetSystem.exe) in the `dist/` directory. No Python installation is required.
* **From Source Script**: Run the entry point script using Python:
  ```powershell
  python generate_timesheet.py
  ```

Upon startup, the system checks for a local database named `timesheets.db` in the application directory. If it is missing, it initializes it automatically.

---

## 🗃️ Database Tools (Top Menu Bar)

Located at the top left of the application window, the **Tools** menu provides options to back up and restore your SQLite database:
* **Backup Database...**: Copies your current database to a custom backup file at a location of your choice.
* **Restore Database...**: Overwrites the active database with a selected backup file. The program validates the backup file's integrity using SQLite's verification checks and prompts you with a confirmation warning before replacing current data.

---

## 📁 Tabs Overview

The dashboard contains three primary management tabs: **Cities**, **Drivers**, and **Timesheets** (which includes the Daily Grid Preview and Solver panels).

---

### 1. Cities Tab
This tab lists all registered delivery hubs and their operational windows.
* **Add City...**: Opens a dialog to register a new city.
  * **Start Time & End Time**: Must be entered in `HH:MM` format (e.g., `08:00` to `22:00`). These times define the operational window in which all driver shifts must start and end.
* **Edit City...**: Modifies details for the selected city.
* **Delete City**: Removes the selected city. 
  * > [!IMPORTANT]
    > **Deletion Integrity:** To prevent data corruption, the system blocks city deletion if any timesheets (active or archived) reference it.

---

### 2. Drivers Tab
This tab manages delivery drivers.
* **Add Driver...**: Registers a new driver using their **Driver Name** and a unique **Personal ID** (e.g., `P12345`).
* **Edit Driver...**: Modifies details for the selected driver.
* **Delete Driver**: Removes the selected driver.
  * > [!IMPORTANT]
    > **Deletion Integrity:** Deletion is blocked if the driver has any timesheets saved in the database.

---

### 3. Timesheets Tab & Actions
This is the core workspace where monthly targets are set, solver calculations are run, schedules are edited, and Word reports are generated.

#### Filtering Timesheets
At the top left of the list, two dropdown filters allow you to narrow down the view:
* **City**: Shows only timesheets for the selected city.
* **Month**: Filter by target month (format: `MM.YYYY`).

#### Action Buttons
* **New Timesheet...**: Creates a blank timesheet for a selected driver, city, month, and target working hours.
  * **Validation Rules**:
    * **Current or Future Months Only**: You cannot create timesheets for past months.
    * **Target Hours**: Must be a multiple of `0.5` hours.
    * **Target Hours Bounds**: Must be between `10.0` hours (minimum) and a monthly maximum dynamically calculated based on the number of days in the month (e.g., max 208 hours for a 30-day month).
* **Delete Timesheet**: Permanently deletes the selected timesheet and cascades to delete all of its daily calendar entries.

---

## 🧠 Solver Panel (Distribute Hours)

Once a timesheet is created, click on it to show the daily preview grid on the right, and use the solver buttons to distribute shifts:

* **Distribute (Single)** (Incremental Mode):
  * Runs the solver for the selected driver *only*, staggering their shifts against any existing driver schedules already saved for that city and month.
  * Shows a warning advice popup recommending Batch execution first. Click **Yes** to proceed.
* **Distribute All (City Batch)** (Batch Mode):
  * Runs the solver for **all** unlocked `Draft` status timesheets in the selected city/month simultaneously. 
  * The solver coordinates their start times cooperatively, staggering schedules to optimize coverage across the city's operational hours.
* **Finalize**:
  * Changes the timesheet's status from `Draft` to `Finalized`.
  * **Finalized timesheets are locked**: the solver cannot modify them, protecting completed schedules from accidental batch re-runs.
* **Revert to Draft**:
  * Restores status to `Draft`, allowing solver re-runs or batch redistribution.
* **Export to Word**:
  * Exports the schedule to a beautifully formatted Word document (`.docx`).
  * Features page margins of 0.8 inches, Calibri 11pt typography, a centered header ("Tätigkeitsnachweis"), underlined employee details, column widths scaled to alignment, and German localized hours (decimal commas like `6,5`).
  * Off-days are left blank (no `"Wochenende"` or weekend labels are written).

---

## ✏️ Interactive Daily Grid & Manual Edit Workflow

The right-side preview panel shows a day-by-day table. Double-clicking any cell launches the **Manual Edit Dialog** for that date:
* You can change the **Start Time**, **End Time**, **Break Duration**, **Hours Worked**, and **Remarks**.
* If you set **Hours Worked** to `0`, the times and breaks are cleared automatically, representing a day off.

### Post-Solver Manual Edit Prompts
When you save manual changes, the application presents two options for how to save:
1. **Lock Driver Only**: Sets `is_distribution_locked = True` on this timesheet and saves your edits directly. This driver is now excluded from future batch solves.
2. **Apply & Redistribute Others**: Saves your edits, treats this driver's schedule as an absolute fixed constraint, and automatically re-runs the solver for all other unlocked Draft drivers in the city, staggering their shifts around your manual changes.

### Soft Validation Warnings
If your manual edits violate any scheduling rules, the program displays a summary warning popup (allowing you to click **Yes** to override and save anyway, or **No** to return to editing):
* **Target hours deviation**: Warns if the sum of actual shifts does not match the monthly target.
* **Shift duration limits**: Warns if any shift is below `2.0` hours or above `8.0` hours.
* **Operational window bounds**: Warns if start/end times fall outside the city's operational hours.
* **6-consecutive-day limit**: Warns if a driver works more than 6 consecutive days (calculated globally, including cross-city timesheets and previous month end-boundaries).

---

## 📊 Analytics Tab

The **Analytics** tab provides visual metrics to audit schedules and evaluate delivery coverage:

* **Driver Monthly Hours Panel (Left)**:
  * Select a driver to render a bar chart comparing their **Target Hours** (light blue) vs. **Actual Worked Hours** (dark blue) across all timesheets in chronological order.
  * Helps verify monthly completion rates at a glance.
* **City Hourly Coverage Heatmap (Right)**:
  * Select a city and month/year to render a 2D occupancy heatmap.
  * **X-Axis**: Time of day (across city operational hours).
  * **Y-Axis**: Days of the month (1 to 28/29/30/31).
  * **Color Profile**: Indicates how many drivers are active in each half-hour slot. Darker blocks mean high coverage, while light blocks highlight low coverage or empty slots. Useful for spotting delivery scheduling gaps.

---

## 📐 Scheduling Constraints Summary

For reference, the scheduling solver automatically enforces these rules:
* **Allowed Shift Lengths**: Only half-hour increments are allowed: `2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0` hours.
* **Auto-Break**: A shift of `6.5` hours or more automatically triggers a `0.5` hour unpaid break. The break duration is added to the shift duration (elapsed time) but is not counted toward the driver's paid working target hours.
* **6-Consecutive-Day Limit**: Drivers cannot work more than 6 consecutive days globally. This spans across months (the solver queries the last 6 days of the previous month) and across cities (cross-city active days are merged).
