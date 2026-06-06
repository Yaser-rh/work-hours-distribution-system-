import os
import sys
import shutil
import time
import calendar
import sqlite3

# Ensure project root is in the path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db.database import get_connection, DB_PATH
import db.models as models
import solver.sat_solver as sat_solver

def run_solve_on_timesheets(timesheet_ids, timeout):
    """
    Simulates the backend api_solve() logic in app.py to solve timesheets
    and save them directly to the database.
    """
    first_ts = models.get_timesheet_with_entries(timesheet_ids[0])
    if not first_ts:
        raise ValueError("Timesheet not found.")

    city_id = first_ts['city_id']
    year = first_ts['year']
    month = first_ts['month']
    _, num_days = calendar.monthrange(year, month)

    # Get city details
    cities = models.get_cities()
    city = next((c for c in cities if c['id'] == city_id), None)
    if not city:
        raise ValueError("City not found.")

    city_start = sat_solver.clock_to_units(city['start_time'])
    city_end = sat_solver.clock_to_units(city['end_time'])

    # Collect all timesheets for this city/month
    all_ts = models.get_timesheets(city_id=city_id, year=year, month=month)

    solve_ids = set(timesheet_ids)
    drivers = []
    locked_entries = {}

    for ts in all_ts:
        ts_detail = models.get_timesheet_with_entries(ts['id'])
        if not ts_detail:
            continue

        if ts['id'] in solve_ids:
            if ts['status'] == 'Finalized' or ts['is_distribution_locked']:
                locked_entries[ts['employee_id']] = ts_detail.get('entries', [])
            else:
                drivers.append(sat_solver.DriverSpec(
                    employee_id=ts['employee_id'],
                    target_units=sat_solver.hours_to_units(ts['target_hours']),
                    name=ts['employee_name']
                ))
        else:
            entries = ts_detail.get('entries', [])
            if entries:
                if ts['employee_id'] in locked_entries:
                    locked_entries[ts['employee_id']].extend(entries)
                else:
                    locked_entries[ts['employee_id']] = entries

    prev_month_boundary = {}
    cross_city_active = {}
    for d_spec in drivers:
        prev_month_boundary[d_spec.employee_id] = models.get_previous_month_boundary(
            d_spec.employee_id, year, month
        )
        cross_city_active[d_spec.employee_id] = models.get_cross_city_active_days(
            d_spec.employee_id, year, month, city_id
        )

    # Get existing coverage (from timesheets NOT in our solve set)
    existing_coverage = models.get_city_coverage(city_id, year, month, exclude_timesheet_ids=list(solve_ids))

    mode = 'batch' if len(drivers) > 1 else 'incremental'

    solver_input = sat_solver.SolverInput(
        drivers=drivers,
        city_start=city_start,
        city_end=city_end,
        num_days=num_days,
        prev_month_boundary=prev_month_boundary,
        cross_city_active=cross_city_active,
        existing_coverage=existing_coverage,
        locked_entries=locked_entries,
        mode=mode
    )

    print(f"  [Solver] Running solver in '{mode}' mode for {len(drivers)} active driver(s)")
    print(f"  [Solver] Locked drivers count: {len(locked_entries)}")
    
    start_t = time.perf_counter()
    result = sat_solver.solve(solver_input, timeout=timeout)
    solve_duration = time.perf_counter() - start_t

    if result.status == 'failed':
        print(f"  [Solver] Solve failed in {solve_duration:.2f}s")
        return result, solve_duration

    # Save results to database
    for ts in all_ts:
        if ts['employee_id'] in result.schedules:
            schedule = result.schedules[ts['employee_id']]
            if ts['id'] in solve_ids:
                entries = []
                for day_entry in schedule:
                    work_date = f"{year}-{month:02d}-{day_entry.day:02d}"
                    break_str = f"00:{day_entry.break_minutes:02d}" if day_entry.break_minutes > 0 else ""
                    entries.append({
                        'work_date': work_date,
                        'hours_worked': day_entry.hours,
                        'start_time': day_entry.start_time,
                        'end_time': day_entry.end_time,
                        'break_duration': break_str,
                        'remarks': ''
                    })
                models.save_daily_entries(ts['id'], entries)

    print(f"  [Solver] Solve successful ({result.status}) in {result.solve_time_seconds:.2f}s (python wall time: {solve_duration:.2f}s). Target deviation: {result.target_deviation} hours")
    return result, solve_duration

def main():
    # 1. Back up database
    backup_path = DB_PATH + ".backup"
    print(f"[*] Backing up database {DB_PATH} to {backup_path}")
    shutil.copy2(DB_PATH, backup_path)

    # Configuration
    city_id = 2  # Istanbul
    year = 2026
    month = 6
    target_hours = 80.0
    timeout = 60.0

    try:
        # 2. Clean previous test data to prevent clashes/errors
        print("[*] Cleaning up any old stress-test drivers...")
        conn = get_connection()
        try:
            with conn:
                # Get employee IDs of test drivers
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM employee WHERE name LIKE 'Test Driver %'")
                test_emp_ids = [row[0] for row in cursor.fetchall()]
                
                if test_emp_ids:
                    placeholders = ",".join("?" for _ in test_emp_ids)
                    # Get timesheet IDs
                    cursor.execute(f"SELECT id FROM timesheet WHERE employee_id IN ({placeholders})", test_emp_ids)
                    ts_ids = [row[0] for row in cursor.fetchall()]
                    
                    if ts_ids:
                        ts_placeholders = ",".join("?" for _ in ts_ids)
                        cursor.execute(f"DELETE FROM daily_entry WHERE timesheet_id IN ({ts_placeholders})", ts_ids)
                        cursor.execute(f"DELETE FROM timesheet WHERE id IN ({ts_placeholders})", ts_ids)
                    
                    cursor.execute(f"DELETE FROM employee WHERE id IN ({placeholders})", test_emp_ids)
                    print(f"    Cleaned up {len(test_emp_ids)} old test employee(s) and their schedules.")
        finally:
            conn.close()

        # 3. Batch 1: Create 20 drivers and timesheets
        print("\n=== STEP 1: Running Solver on Batch 1 (20 new drivers) ===")
        batch1_ts_ids = []
        for i in range(1, 21):
            name = f"Test Driver {i:02d}"
            personal_id = f"TEST_{i:03d}"
            emp_id = models.add_employee(name, personal_id)
            ts_id = models.create_timesheet(emp_id, city_id, year, month, target_hours)
            batch1_ts_ids.append(ts_id)
        print(f"[*] Created 20 drivers (Test Driver 01 - 20) and timesheets.")

        # Solve Batch 1
        res1, dur1 = run_solve_on_timesheets(batch1_ts_ids, timeout)
        
        # Finalize Batch 1
        print("[*] Finalizing Batch 1 timesheets in database to lock their schedules...")
        for ts_id in batch1_ts_ids:
            models.update_timesheet_status(ts_id, 'Finalized')
            # The status 'Finalized' locks the distribution automatically, but we set it explicitly too
            models.set_distribution_lock(ts_id, True)

        # 4. Batch 2: Create 20 more drivers and timesheets
        print("\n=== STEP 2: Running Solver on Batch 2 (20 more drivers) ===")
        batch2_ts_ids = []
        for i in range(21, 41):
            name = f"Test Driver {i:02d}"
            personal_id = f"TEST_{i:03d}"
            emp_id = models.add_employee(name, personal_id)
            ts_id = models.create_timesheet(emp_id, city_id, year, month, target_hours)
            batch2_ts_ids.append(ts_id)
        print(f"[*] Created 20 more drivers (Test Driver 21 - 40) and timesheets.")

        # Solve Batch 2 (Batch 1 is finalized, so it acts as background constraints)
        res2, dur2 = run_solve_on_timesheets(batch2_ts_ids, timeout)

        # Print final summary report
        print("\n" + "="*50)
        print("                 STRESS TEST RESULTS")
        print("="*50)
        print(f"Batch 1 (20 active drivers):")
        print(f"  - Status:           {res1.status.upper()}")
        print(f"  - Solve Time (solv): {res1.solve_time_seconds:.2f}s")
        print(f"  - Solve Time (wall): {dur1:.2f}s")
        print(f"  - Target Deviation: {res1.target_deviation:.2f} hours")
        print()
        print(f"Batch 2 (20 active drivers + 20 finalized background constraints):")
        print(f"  - Status:           {res2.status.upper()}")
        print(f"  - Solve Time (solv): {res2.solve_time_seconds:.2f}s")
        print(f"  - Solve Time (wall): {dur2:.2f}s")
        print(f"  - Target Deviation: {res2.target_deviation:.2f} hours")
        print("="*50)
        
    except Exception as e:
        print(f"[!] Exception during run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
