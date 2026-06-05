import sqlite3
from utils.paths import DB_PATH

def get_connection() -> sqlite3.Connection:
    """
    Returns a sqlite3 connection with foreign keys enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database() -> None:
    """
    Initializes the SQLite database, creating the schema tables if they do not exist.
    """
    conn = get_connection()
    try:
        with conn:
            # City table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS city (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL UNIQUE,
                    start_time  TEXT NOT NULL DEFAULT '08:00',
                    end_time    TEXT NOT NULL DEFAULT '22:00'
                )
            """)
            
            # Employee (Driver) table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS employee (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    personal_id TEXT NOT NULL UNIQUE
                )
            """)
            
            # Index to enforce UNIQUE constraint on existing databases
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_employee_personal_id ON employee(personal_id)")
            
            # Timesheet table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS timesheet (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id             INTEGER NOT NULL,
                    city_id                 INTEGER NOT NULL,
                    year                    INTEGER NOT NULL,
                    month                   INTEGER NOT NULL,
                    target_hours            REAL NOT NULL,
                    status                  TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft', 'Finalized')),
                    is_distribution_locked  INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE RESTRICT,
                    FOREIGN KEY (city_id) REFERENCES city(id) ON DELETE RESTRICT,
                    UNIQUE(employee_id, year, month, city_id)
                )
            """)
            
            # Daily Entry table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_entry (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    timesheet_id    INTEGER NOT NULL,
                    work_date       TEXT NOT NULL,
                    hours_worked    REAL NOT NULL DEFAULT 0.0,
                    start_time      TEXT,
                    end_time        TEXT,
                    break_duration  TEXT,
                    remarks         TEXT,
                    FOREIGN KEY (timesheet_id) REFERENCES timesheet(id) ON DELETE CASCADE
                )
            """)
    finally:
        conn.close()
