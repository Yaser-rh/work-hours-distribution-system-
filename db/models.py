import os
import shutil
import sqlite3
import calendar
from typing import List, Dict, Any, Optional
from db.database import get_connection
from utils.paths import DB_PATH

# ==============================================================================
# Helper functions
# ==============================================================================

def clock_to_units(time_str: str) -> int:
    """
    Converts a "HH:MM" clock time into half-hour units from midnight.
    e.g., "08:00" -> 16, "08:30" -> 17, "22:00" -> 44
    """
    if not time_str:
        return 0
    parts = time_str.split(':')
    if len(parts) != 2:
        return 0
    try:
        h, m = int(parts[0]), int(parts[1])
        return h * 2 + (1 if m >= 30 else 0)
    except ValueError:
        return 0


# ==============================================================================
# CITY CRUD Operations
# ==============================================================================

def add_city(name: str, start_time: str, end_time: str) -> int:
    """
    Adds a new city to the database.
    Returns the ID of the newly created city.
    Raises sqlite3.IntegrityError if name already exists.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO city (name, start_time, end_time) VALUES (?, ?, ?)",
            (name, start_time, end_time)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_cities() -> List[Dict[str, Any]]:
    """
    Retrieves all cities, ordered alphabetically by name.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, start_time, end_time FROM city ORDER BY name")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "start_time": r[2], "end_time": r[3]} for r in rows]
    finally:
        conn.close()

def update_city(city_id: int, name: str, start_time: str, end_time: str) -> None:
    """
    Updates a city's details.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE city SET name = ?, start_time = ?, end_time = ? WHERE id = ?",
            (name, start_time, end_time, city_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_city(city_id: int) -> None:
    """
    Deletes a city by its ID.
    Raises sqlite3.IntegrityError if timesheets reference this city.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM city WHERE id = ?", (city_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# EMPLOYEE CRUD Operations
# ==============================================================================

def add_employee(name: str, personal_id: str) -> int:
    """
    Adds a new employee to the database.
    Returns the ID of the newly created employee.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employee (name, personal_id) VALUES (?, ?)",
            (name, personal_id)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_employees() -> List[Dict[str, Any]]:
    """
    Retrieves all employees, ordered alphabetically by name.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, personal_id FROM employee ORDER BY name")
        rows = cursor.fetchall()
        return [{"id": r[0], "name": r[1], "personal_id": r[2]} for r in rows]
    finally:
        conn.close()

def update_employee(emp_id: int, name: str, personal_id: str) -> None:
    """
    Updates an employee's details.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE employee SET name = ?, personal_id = ? WHERE id = ?",
            (name, personal_id, emp_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_employee(emp_id: int) -> None:
    """
    Deletes an employee by their ID.
    Raises sqlite3.IntegrityError if timesheets reference this employee.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employee WHERE id = ?", (emp_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# TIMESHEET CRUD Operations
# ==============================================================================

def create_timesheet(employee_id: int, city_id: int, year: int, month: int,
                     target_hours: float) -> int:
    """
    Creates a new timesheet.
    Returns the ID of the newly created timesheet.
    Raises sqlite3.IntegrityError if duplicate (violates UNIQUE constraint).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO timesheet (employee_id, city_id, year, month, target_hours, status, is_distribution_locked)
               VALUES (?, ?, ?, ?, ?, 'Draft', 0)""",
            (employee_id, city_id, year, month, target_hours)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_timesheets(city_id: Optional[int] = None,
                   employee_id: Optional[int] = None,
                   year: Optional[int] = None,
                   month: Optional[int] = None,
                   status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves timesheets with joined employee and city names, filtered by criteria.
    """
    query = """
        SELECT t.id, t.employee_id, e.name AS employee_name, e.personal_id,
               t.city_id, c.name AS city_name, t.year, t.month, t.target_hours,
               t.status, t.is_distribution_locked
        FROM timesheet t
        JOIN employee e ON t.employee_id = e.id
        JOIN city c ON t.city_id = c.id
        WHERE 1=1
    """
    params = []
    if city_id is not None:
        query += " AND t.city_id = ?"
        params.append(city_id)
    if employee_id is not None:
        query += " AND t.employee_id = ?"
        params.append(employee_id)
    if year is not None:
        query += " AND t.year = ?"
        params.append(year)
    if month is not None:
        query += " AND t.month = ?"
        params.append(month)
    if status is not None:
        query += " AND t.status = ?"
        params.append(status)

    query += " ORDER BY t.year DESC, t.month DESC, e.name ASC"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "employee_id": r[1],
                "employee_name": r[2],
                "personal_id": r[3],
                "city_id": r[4],
                "city_name": r[5],
                "year": r[6],
                "month": r[7],
                "target_hours": r[8],
                "status": r[9],
                "is_distribution_locked": bool(r[10]),
            }
            for r in rows
        ]
    finally:
        conn.close()

def get_timesheet_with_entries(timesheet_id: int) -> Dict[str, Any]:
    """
    Retrieves a timesheet by ID, including all its daily entries sorted by work_date.
    Returns empty dict if not found.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT t.id, t.employee_id, e.name AS employee_name, e.personal_id,
                      t.city_id, c.name AS city_name, t.year, t.month, t.target_hours,
                      t.status, t.is_distribution_locked
               FROM timesheet t
               JOIN employee e ON t.employee_id = e.id
               JOIN city c ON t.city_id = c.id
               WHERE t.id = ?""",
            (timesheet_id,)
        )
        t_row = cursor.fetchone()
        if not t_row:
            return {}

        timesheet = {
            "id": t_row[0],
            "employee_id": t_row[1],
            "employee_name": t_row[2],
            "personal_id": t_row[3],
            "city_id": t_row[4],
            "city_name": t_row[5],
            "year": t_row[6],
            "month": t_row[7],
            "target_hours": t_row[8],
            "status": t_row[9],
            "is_distribution_locked": bool(t_row[10]),
            "entries": []
        }

        cursor.execute(
            """SELECT id, work_date, hours_worked, start_time, end_time, break_duration, remarks
               FROM daily_entry
               WHERE timesheet_id = ?
               ORDER BY work_date ASC""",
            (timesheet_id,)
        )
        de_rows = cursor.fetchall()
        for de in de_rows:
            timesheet["entries"].append({
                "id": de[0],
                "work_date": de[1],
                "hours_worked": de[2],
                "start_time": de[3] if de[3] is not None else "",
                "end_time": de[4] if de[4] is not None else "",
                "break_duration": de[5] if de[5] is not None else "",
                "remarks": de[6] if de[6] is not None else "",
            })
        return timesheet
    finally:
        conn.close()

def save_daily_entries(timesheet_id: int, entries: List[Dict[str, Any]]) -> None:
    """
    Replaces all daily entries for a timesheet in a single transaction.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM daily_entry WHERE timesheet_id = ?", (timesheet_id,))
            conn.executemany(
                """INSERT INTO daily_entry (timesheet_id, work_date, hours_worked, start_time, end_time, break_duration, remarks)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        timesheet_id,
                        entry["work_date"],
                        entry["hours_worked"],
                        entry.get("start_time"),
                        entry.get("end_time"),
                        entry.get("break_duration"),
                        entry.get("remarks"),
                    )
                    for entry in entries
                ]
            )
    finally:
        conn.close()

def update_timesheet_status(timesheet_id: int, status: str) -> None:
    """
    Updates the status of a timesheet ('Draft' or 'Finalized').
    """
    if status not in ("Draft", "Finalized"):
        raise ValueError("Status must be 'Draft' or 'Finalized'")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE timesheet SET status = ? WHERE id = ?",
            (status, timesheet_id)
        )
        conn.commit()
    finally:
        conn.close()

def set_distribution_lock(timesheet_id: int, locked: bool) -> None:
    """
    Locks or unlocks a timesheet for manual redistribution updates.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE timesheet SET is_distribution_locked = ? WHERE id = ?",
            (1 if locked else 0, timesheet_id)
        )
        conn.commit()
    finally:
        conn.close()

def delete_timesheet(timesheet_id: int) -> None:
    """
    Deletes a timesheet by ID, cascading to delete all referencing daily entries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timesheet WHERE id = ?", (timesheet_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Solver Support Queries
# ==============================================================================

def get_previous_month_boundary(employee_id: int, year: int, month: int) -> List[int]:
    """
    Returns list of 6 values (0 or 1) representing active status for the
    last 6 days of the previous month. Returns [0,0,0,0,0,0] if no data.
    """
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    _, prev_num_days = calendar.monthrange(prev_year, prev_month)
    last_6_days = list(range(prev_num_days - 5, prev_num_days + 1))

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT de.work_date, de.hours_worked
            FROM daily_entry de
            JOIN timesheet t ON de.timesheet_id = t.id
            WHERE t.employee_id = ? AND t.year = ? AND t.month = ? AND de.hours_worked > 0.0
        """, (employee_id, prev_year, prev_month))
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return [0] * 6

    active_days = set()
    for work_date, hours in rows:
        day = None
        if '-' in work_date:
            day = int(work_date.split('-')[2])
        elif '.' in work_date:
            day = int(work_date.split('.')[0])
        if day is not None:
            active_days.add(day)

    return [1 if d in active_days else 0 for d in last_6_days]

def get_cross_city_active_days(employee_id: int, year: int, month: int,
                                exclude_city_id: int) -> Dict[int, int]:
    """
    Returns {day_of_month: 1/0} for active days in OTHER cities.
    Used for global consecutive-day enforcement.
    """
    _, num_days = calendar.monthrange(year, month)
    result = {d: 0 for d in range(1, num_days + 1)}

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT de.work_date, de.hours_worked
            FROM daily_entry de
            JOIN timesheet t ON de.timesheet_id = t.id
            WHERE t.employee_id = ? AND t.year = ? AND t.month = ? AND t.city_id != ? AND de.hours_worked > 0.0
        """, (employee_id, year, month, exclude_city_id))
        rows = cursor.fetchall()
    finally:
        conn.close()

    for work_date, hours in rows:
        day = None
        if '-' in work_date:
            day = int(work_date.split('-')[2])
        elif '.' in work_date:
            day = int(work_date.split('.')[0])
        if day is not None and day in result:
            result[day] = 1

    return result

def get_city_coverage(city_id: int, year: int, month: int,
                      exclude_timesheet_ids: List[int] = None) -> Dict[int, Dict[int, int]]:
    """
    Returns {day: {slot: count}} coverage map for staggering.
    Slot is the half-hour unit from midnight (0 to 47).
    Optionally excludes specific timesheets.
    """
    _, num_days = calendar.monthrange(year, month)
    coverage = {day: {slot: 0 for slot in range(48)} for day in range(1, num_days + 1)}

    query = """
        SELECT de.work_date, de.start_time, de.end_time
        FROM daily_entry de
        JOIN timesheet t ON de.timesheet_id = t.id
        WHERE t.city_id = ? AND t.year = ? AND t.month = ?
    """
    params = [city_id, year, month]
    if exclude_timesheet_ids:
        placeholders = ",".join("?" for _ in exclude_timesheet_ids)
        query += f" AND t.id NOT IN ({placeholders})"
        params.extend(exclude_timesheet_ids)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    for work_date, start_time, end_time in rows:
        if not start_time or not end_time:
            continue
        day = None
        if '-' in work_date:
            day = int(work_date.split('-')[2])
        elif '.' in work_date:
            day = int(work_date.split('.')[0])

        if day is not None and day in coverage:
            start_slot = clock_to_units(start_time)
            end_slot = clock_to_units(end_time)
            for slot in range(start_slot, end_slot):
                if 0 <= slot < 48:
                    coverage[day][slot] += 1

    return coverage


# ==============================================================================
# Backup & Restore
# ==============================================================================

def backup_database(destination_path: str) -> None:
    """
    Copies the SQLite database file to a destination path.
    Raises IOError on failure.
    """
    try:
        # Source file must exist
        if not os.path.exists(DB_PATH):
            # If the file hasn't been created yet, let's create a blank one or raise
            # Standard practice: create directory if it doesn't exist, and create database
            # but since DB_PATH is usually created by initialize_database, we can just check.
            conn = get_connection()
            conn.close()
        shutil.copy2(DB_PATH, destination_path)
    except Exception as e:
        raise IOError(f"Failed to backup database: {str(e)}")

def restore_database(backup_path: str) -> None:
    """
    Validates the backup file using SQLite integrity check,
    and replaces the current database file.
    Raises ValueError on invalid database, IOError on file copy failure.
    """
    # 1. Validate backup is a valid SQLite DB
    if not os.path.exists(backup_path):
        raise ValueError(f"Backup file does not exist: {backup_path}")
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        if not result or result[0] != "ok":
            raise ValueError("Integrity check failed: database file is corrupted or invalid.")
    except Exception as e:
        raise ValueError(f"Invalid database backup file: {str(e)}")

    # 2. Copy the backup file over current DB
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        shutil.copy2(backup_path, DB_PATH)
    except Exception as e:
        raise IOError(f"Failed to restore database: {str(e)}")
