import sys
import argparse
import tkinter as tk
from db.database import initialize_database
from ui.main_gui import TimesheetAppGUI

def main():
    parser = argparse.ArgumentParser(
        description="Timesheet Generator & Driver Shift Distribution System"
    )
    parser.add_argument("--cli", action="store_true", help="Legacy CLI flag (ignored, launches GUI)")
    parser.add_argument("--name", help="Legacy Employee name flag (ignored)")
    parser.add_argument("--id", help="Legacy Personal ID flag (ignored)")
    parser.add_argument("--hours", type=float, help="Legacy Target hours flag (ignored)")
    parser.add_argument("--month", help="Legacy Target month flag (ignored)")
    parser.add_argument("--city", help="Legacy City name flag (ignored)")
    parser.add_argument("--output", help="Legacy Output path flag (ignored)")
    
    args = parser.parse_args()
    
    # Initialize SQLite database file and tables
    initialize_database()
    
    # Boot up CustomTkinter Desktop GUI
    import customtkinter as ctk
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = TimesheetAppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
