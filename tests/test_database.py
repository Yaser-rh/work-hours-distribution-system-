import os
import tempfile
import sqlite3
import pytest

import utils.paths
import db.database
import db.models

@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Fixture to isolate database tests. Redirects DB_PATH to a temporary file
    and initializes it before each test, cleaning it up after.
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_fd)
    
    # Save original DB_PATHs
    orig_paths_db = utils.paths.DB_PATH
    orig_db_db = db.database.DB_PATH
    orig_models_db = db.models.DB_PATH
    
    # Override paths to redirect to the temp file
    utils.paths.DB_PATH = temp_path
    db.database.DB_PATH = temp_path
    db.models.DB_PATH = temp_path
    
    # Initialize the test database
    db.database.initialize_database()
    
    yield temp_path
    
    # Restore original paths
    utils.paths.DB_PATH = orig_paths_db
    db.database.DB_PATH = orig_db_db
    db.models.DB_PATH = orig_models_db
    
    # Clean up the temp file
    try:
        os.remove(temp_path)
    except OSError:
        pass


def test_city_crud():
    # 1. Add city
    city_id = db.models.add_city("Istanbul", "08:00", "22:00")
    assert city_id > 0

    # 2. Get cities
    cities = db.models.get_cities()
    assert len(cities) == 1
    assert cities[0]["name"] == "Istanbul"
    assert cities[0]["start_time"] == "08:00"
    assert cities[0]["end_time"] == "22:00"

    # 3. Duplicate city should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        db.models.add_city("Istanbul", "08:00", "22:00")

    # 4. Update city
    db.models.update_city(city_id, "Istanbul Updated", "09:00", "21:00")
    cities = db.models.get_cities()
    assert cities[0]["name"] == "Istanbul Updated"
    assert cities[0]["start_time"] == "09:00"
    assert cities[0]["end_time"] == "21:00"

    # 5. Delete city
    db.models.delete_city(city_id)
    cities = db.models.get_cities()
    assert len(cities) == 0


def test_employee_crud():
    # 1. Add employee
    emp_id = db.models.add_employee("Max Mustermann", "P12345")
    assert emp_id > 0

    # 2. Get employees
    employees = db.models.get_employees()
    assert len(employees) == 1
    assert employees[0]["name"] == "Max Mustermann"
    assert employees[0]["personal_id"] == "P12345"

    # 3. Update employee
    db.models.update_employee(emp_id, "Max Updated", "P54321")
    employees = db.models.get_employees()
    assert employees[0]["name"] == "Max Updated"
    assert employees[0]["personal_id"] == "P54321"

    # 4. Delete employee
    db.models.delete_employee(emp_id)
    employees = db.models.get_employees()
    assert len(employees) == 0


def test_timesheet_crud():
    city_id = db.models.add_city("Ankara", "08:00", "22:00")
    emp_id = db.models.add_employee("John Doe", "P999")

    # 1. Create timesheet
    ts_id = db.models.create_timesheet(emp_id, city_id, 2026, 6, 80.0)
    assert ts_id > 0

    # 2. Get timesheets
    sheets = db.models.get_timesheets()
    assert len(sheets) == 1
    assert sheets[0]["id"] == ts_id
    assert sheets[0]["employee_name"] == "John Doe"
    assert sheets[0]["city_name"] == "Ankara"
    assert sheets[0]["year"] == 2026
    assert sheets[0]["month"] == 6
    assert sheets[0]["target_hours"] == 80.0
    assert sheets[0]["status"] == "Draft"
    assert sheets[0]["is_distribution_locked"] is False

    # 3. Check uniqueness constraint
    with pytest.raises(sqlite3.IntegrityError):
        db.models.create_timesheet(emp_id, city_id, 2026, 6, 120.0)

    # 4. Status update
    db.models.update_timesheet_status(ts_id, "Finalized")
    sheets = db.models.get_timesheets()
    assert sheets[0]["status"] == "Finalized"

    with pytest.raises(ValueError):
        db.models.update_timesheet_status(ts_id, "InvalidStatus")

    # 5. Lock distribution update
    db.models.set_distribution_lock(ts_id, True)
    sheets = db.models.get_timesheets()
    assert sheets[0]["is_distribution_locked"] is True

    # 6. Delete timesheet
    db.models.delete_timesheet(ts_id)
    assert len(db.models.get_timesheets()) == 0


def test_referential_integrity():
    city_id = db.models.add_city("Izmir", "08:00", "22:00")
    emp_id = db.models.add_employee("Alice", "P001")
    db.models.create_timesheet(emp_id, city_id, 2026, 6, 60.0)

    # Deleting city must be blocked by RESTRICT constraint
    with pytest.raises(sqlite3.IntegrityError):
        db.models.delete_city(city_id)

    # Deleting employee must be blocked by RESTRICT constraint
    with pytest.raises(sqlite3.IntegrityError):
        db.models.delete_employee(emp_id)


def test_daily_entries():
    city_id = db.models.add_city("Istanbul", "08:00", "22:00")
    emp_id = db.models.add_employee("Bob", "P002")
    ts_id = db.models.create_timesheet(emp_id, city_id, 2026, 6, 40.0)

    entries = [
        {"work_date": "2026-06-01", "hours_worked": 6.0, "start_time": "08:00", "end_time": "14:00", "break_duration": "00:00", "remarks": "Shift 1"},
        {"work_date": "2026-06-02", "hours_worked": 0.0, "start_time": "", "end_time": "", "break_duration": "", "remarks": "Off"},
    ]

    # Save entries
    db.models.save_daily_entries(ts_id, entries)

    # Retrieve and check
    ts = db.models.get_timesheet_with_entries(ts_id)
    assert ts["employee_name"] == "Bob"
    assert len(ts["entries"]) == 2
    assert ts["entries"][0]["work_date"] == "2026-06-01"
    assert ts["entries"][0]["hours_worked"] == 6.0
    assert ts["entries"][0]["start_time"] == "08:00"
    assert ts["entries"][0]["remarks"] == "Shift 1"

    # Delete timesheet and verify cascade delete of daily entries
    db.models.delete_timesheet(ts_id)
    conn = db.database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM daily_entry WHERE timesheet_id = ?", (ts_id,))
        count = cursor.fetchone()[0]
        assert count == 0
    finally:
        conn.close()


def test_solver_support_queries():
    city_id_1 = db.models.add_city("Istanbul", "08:00", "22:00")
    city_id_2 = db.models.add_city("Ankara", "08:00", "22:00")
    emp_id = db.models.add_employee("Charlie", "P003")

    # 1. test get_previous_month_boundary when no previous month data exists
    boundary = db.models.get_previous_month_boundary(emp_id, 2026, 6)
    assert boundary == [0, 0, 0, 0, 0, 0]

    # 2. Add previous month (May 2026) data
    # May has 31 days. Last 6 days are 26, 27, 28, 29, 30, 31
    ts_may = db.models.create_timesheet(emp_id, city_id_1, 2026, 5, 50.0)
    # Let's make employee active on May 29 (active) and May 31 (active)
    entries_may = [
        {"work_date": "2026-05-29", "hours_worked": 8.0, "start_time": "08:00", "end_time": "16:30", "break_duration": "00:30", "remarks": ""},
        {"work_date": "2026-05-31", "hours_worked": 4.0, "start_time": "08:00", "end_time": "12:00", "break_duration": "00:00", "remarks": ""}
    ]
    db.models.save_daily_entries(ts_may, entries_may)

    boundary = db.models.get_previous_month_boundary(emp_id, 2026, 6)
    # Expected boundary for last 6 days of May:
    # 26: 0, 27: 0, 28: 0, 29: 1, 30: 0, 31: 1
    assert boundary == [0, 0, 0, 1, 0, 1]

    # 3. test get_cross_city_active_days
    # Create timesheets in both Istanbul and Ankara for June 2026
    ts_june_istanbul = db.models.create_timesheet(emp_id, city_id_1, 2026, 6, 40.0)
    ts_june_ankara = db.models.create_timesheet(emp_id, city_id_2, 2026, 6, 20.0)

    # Save active days in Ankara for Charlie: June 5 (active)
    db.models.save_daily_entries(ts_june_ankara, [
        {"work_date": "2026-06-05", "hours_worked": 4.0, "start_time": "12:00", "end_time": "16:00", "break_duration": "00:00", "remarks": ""}
    ])

    cross_city = db.models.get_cross_city_active_days(emp_id, 2026, 6, exclude_city_id=city_id_1)
    # Ankara active days should be marked as 1
    assert cross_city[5] == 1
    assert cross_city[1] == 0
    assert cross_city[30] == 0

    # 4. test get_city_coverage
    # Charlie covers slots in Ankara on June 5: 12:00 to 16:00
    # 12:00 is slot 24. 16:00 is slot 32. Charlie covers slots 24, 25, 26, 27, 28, 29, 30, 31 (8 slots)
    coverage = db.models.get_city_coverage(city_id_2, 2026, 6)
    day_5_cov = coverage[5]
    for slot in range(48):
        if 24 <= slot < 32:
            assert day_5_cov[slot] == 1
        else:
            assert day_5_cov[slot] == 0


def test_backup_restore(setup_test_db):
    temp_db_path = setup_test_db
    
    # Populate original database
    city_id = db.models.add_city("Antalya", "08:00", "22:00")
    emp_id = db.models.add_employee("Alice", "P100")
    db.models.create_timesheet(emp_id, city_id, 2026, 6, 120.0)

    # Perform backup
    backup_fd, backup_path = tempfile.mkstemp(suffix=".db")
    os.close(backup_fd)
    try:
        db.models.backup_database(backup_path)
        assert os.path.exists(backup_path)

        # Destroy current database (delete rows)
        for ts in db.models.get_timesheets():
            db.models.delete_timesheet(ts["id"])
        db.models.delete_city(city_id)
        db.models.delete_employee(emp_id)
        assert len(db.models.get_cities()) == 0
        assert len(db.models.get_employees()) == 0

        # Perform restore
        db.models.restore_database(backup_path)

        # Verify data is back
        cities = db.models.get_cities()
        employees = db.models.get_employees()
        timesheets = db.models.get_timesheets()
        assert len(cities) == 1
        assert cities[0]["name"] == "Antalya"
        assert len(employees) == 1
        assert employees[0]["name"] == "Alice"
        assert len(timesheets) == 1
        assert timesheets[0]["target_hours"] == 120.0
    finally:
        # Clean up backup file
        try:
            os.remove(backup_path)
        except OSError:
            pass

    # Verify restore of invalid database raises ValueError
    invalid_fd, invalid_path = tempfile.mkstemp(suffix=".txt")
    os.close(invalid_fd)
    with open(invalid_path, "w") as f:
        f.write("this is not a database")
    try:
        with pytest.raises(ValueError):
            db.models.restore_database(invalid_path)
    finally:
        try:
            os.remove(invalid_path)
        except OSError:
            pass
