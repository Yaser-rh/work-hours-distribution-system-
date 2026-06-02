import os
import sys

def get_base_directory() -> str:
    """
    Returns the base directory of the application.
    If running as a compiled .exe (via PyInstaller), it returns the folder
    where the executable is located.
    If running as a script, it returns the project root directory (the parent of this file's folder).
    """
    if getattr(sys, 'frozen', False):
        # Running as a compiled .exe; use the directory of the executable
        return os.path.dirname(sys.executable)
    else:
        # Running as a script; use the project root directory
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(get_base_directory(), "timesheets.db")
