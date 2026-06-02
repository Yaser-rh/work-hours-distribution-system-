import os
import calendar
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

import db.models as models
import db.database as database
import solver.sat_solver as sat_solver
import exporter.docx_exporter as docx_exporter

class TimesheetAppGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Timesheet & Driver Shift Distribution System")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 650)
        
        # Apply professional TTK theme and styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Color palette definition
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TLabel", foreground="#333333")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1a365d")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9, "italic"), foreground="#666666")
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#1a365d", foreground="white")
        self.style.map("Accent.TButton", background=[("active", "#2b6cb0")])
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        
        # Initialize Database connection
        database.initialize_database()
        
        # Top Menu Bar
        self.setup_menu()
        
        # Main Layout
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Build Tabs
        self.setup_cities_tab()
        self.setup_drivers_tab()
        self.setup_timesheets_tab()
        
        # Setup Analytics tab
        from ui.analytics_tab import AnalyticsTab
        self.analytics_tab = AnalyticsTab(self.notebook, self)
        self.notebook.add(self.analytics_tab, text="Analytics")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Logs Section (Collapsible ScrolledText at the bottom)
        self.setup_log_panel()
        
        self.write_log("[System] Initialized successfully. Ready.")

    # ==============================================================================
    # Top Menu & Logs Panel
    # ==============================================================================
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Backup Database...", command=self.menu_backup)
        tools_menu.add_command(label="Restore Database...", command=self.menu_restore)
        
        menubar.add_cascade(label="Tools", menu=tools_menu)
        self.root.config(menu=menubar)

    def setup_log_panel(self):
        # Collapsible Log Frame
        log_frame = ttk.LabelFrame(self.root, text=" Solver Calculations Logs ", padding=5)
        log_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))
        
        self.log_txt = ScrolledText(log_frame, height=5, bg="#fafafa", fg="#333333", font=("Courier New", 9))
        self.log_txt.pack(fill=tk.BOTH, expand=True)
        self.log_txt.config(state=tk.DISABLED)

    def write_log(self, text: str):
        """Thread-safe logging into bottom console."""
        def append_log():
            self.log_txt.config(state=tk.NORMAL)
            self.log_txt.insert(tk.END, text + "\n")
            self.log_txt.see(tk.END)
            self.log_txt.config(state=tk.DISABLED)
        self.root.after(0, append_log)

    def menu_backup(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Databases", "*.db"), ("All Files", "*.*")],
            initialfile="timesheets_backup.db",
            title="Backup Database"
        )
        if dest:
            try:
                models.backup_database(dest)
                messagebox.showinfo("Backup Success", f"Database backed up to:\n{dest}")
                self.write_log(f"[Backup] Database copy created at {dest}")
            except Exception as e:
                messagebox.showerror("Backup Error", f"Failed to backup database: {e}")
                self.write_log(f"[Error] Backup failed: {e}")

    def menu_restore(self):
        src = filedialog.askopenfilename(
            filetypes=[("SQLite Databases", "*.db"), ("All Files", "*.*")],
            title="Restore Database"
        )
        if src:
            confirm = messagebox.askyesno(
                "Confirm Restore",
                "Restoring the database will overwrite all current data. Continue?",
                icon="warning"
            )
            if confirm:
                try:
                    models.restore_database(src)
                    messagebox.showinfo("Restore Success", "Database restored successfully.")
                    self.write_log(f"[Restore] Database restored from {src}")
                    self.refresh_all_views()
                except Exception as e:
                    messagebox.showerror("Restore Error", f"Failed to restore database:\n{e}")
                    self.write_log(f"[Error] Restore failed: {e}")

    def refresh_all_views(self):
        self.load_cities()
        self.load_drivers()
        self.load_timesheets()
        self.refresh_timesheet_combos()
        if hasattr(self, 'analytics_tab'):
            self.analytics_tab.refresh_selectors()

    def on_tab_changed(self, event):
        try:
            selected_tab = self.notebook.index(self.notebook.select())
            if selected_tab == 3 and hasattr(self, 'analytics_tab'):
                self.analytics_tab.refresh_selectors()
        except:
            pass

    # ==============================================================================
    # 1. Cities Tab
    # ==============================================================================
    def setup_cities_tab(self):
        cities_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(cities_frame, text="Cities")
        
        # Left: Treeview
        tree_frame = ttk.Frame(cities_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        cols = ("ID", "Name", "Start Time", "End Time")
        self.cities_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.cities_tree.heading(col, text=col)
        self.cities_tree.column("ID", width=50, stretch=False)
        self.cities_tree.column("Name", width=180)
        self.cities_tree.column("Start Time", width=100, anchor=tk.CENTER)
        self.cities_tree.column("End Time", width=100, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.cities_tree.yview)
        self.cities_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cities_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: Actions
        btn_frame = ttk.Frame(cities_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Button(btn_frame, text="Add City...", command=self.add_city_dialog).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Edit City...", command=self.edit_city_dialog).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Delete City", command=self.delete_city).pack(fill=tk.X, pady=5)
        
        self.load_cities()

    def load_cities(self):
        self.cities_tree.delete(*self.cities_tree.get_children())
        for city in models.get_cities():
            self.cities_tree.insert("", tk.END, values=(city["id"], city["name"], city["start_time"], city["end_time"]))

    def add_city_dialog(self):
        self.city_form_dialog("Add City", None)

    def edit_city_dialog(self):
        selected = self.cities_tree.selection()
        if not selected:
            messagebox.showwarning("Select City", "Please select a city to edit.")
            return
        values = self.cities_tree.item(selected[0], "values")
        self.city_form_dialog("Edit City", values)

    def city_form_dialog(self, title: str, values: Optional[tuple]):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("320x220")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        ttk.Label(dialog, text="City Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=values[1] if values else "")
        ttk.Entry(dialog, textvariable=name_var, width=25).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Start Time (HH:MM):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        start_var = tk.StringVar(value=values[2] if values else "08:00")
        ttk.Entry(dialog, textvariable=start_var, width=25).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="End Time (HH:MM):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        end_var = tk.StringVar(value=values[3] if values else "22:00")
        ttk.Entry(dialog, textvariable=end_var, width=25).grid(row=2, column=1, padx=10, pady=10)
        
        def save():
            name = name_var.get().strip()
            start = start_var.get().strip()
            end = end_var.get().strip()
            
            if not name or not start or not end:
                messagebox.showerror("Error", "All fields are required.")
                return
            
            # Simple clock validation
            for clk in (start, end):
                try:
                    parts = clk.split(":")
                    if len(parts) != 2 or not (0 <= int(parts[0]) <= 23) or not (0 <= int(parts[1]) <= 59):
                        raise ValueError()
                except:
                    messagebox.showerror("Error", "Times must be in HH:MM format.")
                    return
            
            try:
                if values:  # Edit Mode
                    models.update_city(int(values[0]), name, start, end)
                    self.write_log(f"[DB] Updated city {name} ({start} - {end})")
                else:  # Add Mode
                    models.add_city(name, start, end)
                    self.write_log(f"[DB] Added city {name} ({start} - {end})")
                self.refresh_all_views()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "A city with this name already exists.")

        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=15)

    def delete_city(self):
        selected = self.cities_tree.selection()
        if not selected:
            messagebox.showwarning("Select City", "Please select a city to delete.")
            return
        values = self.cities_tree.item(selected[0], "values")
        city_id, name = int(values[0]), values[1]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete city '{name}'?")
        if confirm:
            try:
                models.delete_city(city_id)
                self.write_log(f"[DB] Deleted city '{name}'")
                self.refresh_all_views()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Cannot delete city. There are timesheets referencing it.")

    # ==============================================================================
    # 2. Drivers Tab
    # ==============================================================================
    def setup_drivers_tab(self):
        drivers_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(drivers_frame, text="Drivers")
        
        # Left: Treeview
        tree_frame = ttk.Frame(drivers_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        cols = ("ID", "Name", "Personal ID")
        self.drivers_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.drivers_tree.heading(col, text=col)
        self.drivers_tree.column("ID", width=50, stretch=False)
        self.drivers_tree.column("Name", width=200)
        self.drivers_tree.column("Personal ID", width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.drivers_tree.yview)
        self.drivers_tree.configure(yscrollcommand=scrollbar.set)
        
        self.drivers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: Actions
        btn_frame = ttk.Frame(drivers_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        ttk.Button(btn_frame, text="Add Driver...", command=self.add_driver_dialog).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Edit Driver...", command=self.edit_driver_dialog).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Delete Driver", command=self.delete_driver).pack(fill=tk.X, pady=5)
        
        self.load_drivers()

    def load_drivers(self):
        self.drivers_tree.delete(*self.drivers_tree.get_children())
        for emp in models.get_employees():
            self.drivers_tree.insert("", tk.END, values=(emp["id"], emp["name"], emp["personal_id"]))

    def add_driver_dialog(self):
        self.driver_form_dialog("Add Driver", None)

    def edit_driver_dialog(self):
        selected = self.drivers_tree.selection()
        if not selected:
            messagebox.showwarning("Select Driver", "Please select a driver to edit.")
            return
        values = self.drivers_tree.item(selected[0], "values")
        self.driver_form_dialog("Edit Driver", values)

    def driver_form_dialog(self, title: str, values: Optional[tuple]):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("320x180")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Driver Name:").grid(row=0, column=0, padx=10, pady=15, sticky=tk.W)
        name_var = tk.StringVar(value=values[1] if values else "")
        ttk.Entry(dialog, textvariable=name_var, width=25).grid(row=0, column=1, padx=10, pady=15)
        
        ttk.Label(dialog, text="Personal ID:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        id_var = tk.StringVar(value=values[2] if values else "")
        ttk.Entry(dialog, textvariable=id_var, width=25).grid(row=1, column=1, padx=10, pady=10)
        
        def save():
            name = name_var.get().strip()
            personal_id = id_var.get().strip()
            
            if not name or not personal_id:
                messagebox.showerror("Error", "All fields are required.")
                return
            
            if values:  # Edit Mode
                models.update_employee(int(values[0]), name, personal_id)
                self.write_log(f"[DB] Updated employee {name} (ID: {personal_id})")
            else:  # Add Mode
                models.add_employee(name, personal_id)
                self.write_log(f"[DB] Added employee {name} (ID: {personal_id})")
            self.refresh_all_views()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=2, column=0, columnspan=2, pady=15)

    def delete_driver(self):
        selected = self.drivers_tree.selection()
        if not selected:
            messagebox.showwarning("Select Driver", "Please select a driver to delete.")
            return
        values = self.drivers_tree.item(selected[0], "values")
        emp_id, name = int(values[0]), values[1]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete driver '{name}'?")
        if confirm:
            try:
                models.delete_employee(emp_id)
                self.write_log(f"[DB] Deleted driver '{name}'")
                self.refresh_all_views()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Cannot delete employee. There are timesheets referencing them.")

    # ==============================================================================
    # 3. Timesheets Tab & Solver Integration
    # ==============================================================================
    def setup_timesheets_tab(self):
        timesheets_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(timesheets_frame, text="Timesheets")
        
        # Horizontal Split: Left side lists, Right side preview/edit
        h_paned = ttk.PanedWindow(timesheets_frame, orient=tk.HORIZONTAL)
        h_paned.pack(fill=tk.BOTH, expand=True)
        
        # LEFT: List panel
        list_panel = ttk.Frame(h_paned)
        h_paned.add(list_panel, weight=1)
        
        # Filters Header
        filter_frame = ttk.Frame(list_panel)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_frame, text="City:").pack(side=tk.LEFT, padx=2)
        self.filter_city_combo = ttk.Combobox(filter_frame, width=12, state="readonly")
        self.filter_city_combo.pack(side=tk.LEFT, padx=5)
        self.filter_city_combo.bind("<<ComboboxSelected>>", lambda e: self.load_timesheets())
        
        ttk.Label(filter_frame, text="Month:").pack(side=tk.LEFT, padx=2)
        self.filter_month_combo = ttk.Combobox(filter_frame, width=10, state="readonly")
        self.filter_month_combo.pack(side=tk.LEFT, padx=5)
        self.filter_month_combo.bind("<<ComboboxSelected>>", lambda e: self.load_timesheets())
        
        # List Treeview
        ts_cols = ("ID", "Driver", "City", "Month/Year", "Target Hours", "Status", "Locked")
        self.timesheets_tree = ttk.Treeview(list_panel, columns=ts_cols, show="headings", selectmode="browse")
        for col in ts_cols:
            self.timesheets_tree.heading(col, text=col)
        self.timesheets_tree.column("ID", width=40, stretch=False)
        self.timesheets_tree.column("Driver", width=120)
        self.timesheets_tree.column("City", width=100)
        self.timesheets_tree.column("Month/Year", width=80, anchor=tk.CENTER)
        self.timesheets_tree.column("Target Hours", width=90, anchor=tk.CENTER)
        self.timesheets_tree.column("Status", width=80, anchor=tk.CENTER)
        self.timesheets_tree.column("Locked", width=60, anchor=tk.CENTER)
        
        ts_scrollbar = ttk.Scrollbar(list_panel, orient=tk.VERTICAL, command=self.timesheets_tree.yview)
        self.timesheets_tree.configure(yscrollcommand=ts_scrollbar.set)
        
        self.timesheets_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        ts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.timesheets_tree)
        self.timesheets_tree.bind("<<TreeviewSelect>>", self.on_timesheet_select)
        
        # Left Actions Buttons
        la_frame = ttk.Frame(list_panel, padding=5)
        la_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(la_frame, text="New Timesheet...", command=self.new_timesheet_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(la_frame, text="Delete Timesheet", command=self.delete_timesheet).pack(side=tk.LEFT, padx=5)
        ttk.Button(la_frame, text="Export to Word", command=self.export_timesheet).pack(side=tk.RIGHT, padx=5)
        
        # RIGHT: Detail & Grid Preview Panel
        self.detail_panel = ttk.LabelFrame(h_paned, text=" Daily Shift Schedule Preview (Double-click cell to manually edit) ", padding=10)
        h_paned.add(self.detail_panel, weight=1)
        
        # Detail Header metadata labels
        self.meta_frame = ttk.Frame(self.detail_panel)
        self.meta_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.meta_lbl = ttk.Label(self.meta_frame, text="No timesheet selected.", font=("Segoe UI", 11, "bold"), foreground="#1a365d")
        self.meta_lbl.pack(side=tk.LEFT)
        
        # Detail Actions
        self.da_frame = ttk.Frame(self.detail_panel)
        self.da_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        self.btn_single_solve = ttk.Button(self.da_frame, text="Distribute (Single)", command=self.solve_single_timesheet)
        self.btn_single_solve.pack(side=tk.LEFT, padx=5)
        
        self.btn_batch_solve = ttk.Button(self.da_frame, text="Distribute All (City Batch)", command=self.solve_batch_timesheets)
        self.btn_batch_solve.pack(side=tk.LEFT, padx=5)
        
        self.btn_finalize = ttk.Button(self.da_frame, text="Finalize", command=self.finalize_timesheet)
        self.btn_finalize.pack(side=tk.RIGHT, padx=5)
        
        self.btn_revert = ttk.Button(self.da_frame, text="Revert to Draft", command=self.revert_timesheet)
        self.btn_revert.pack(side=tk.RIGHT, padx=5)
        
        # Daily Grid
        grid_cols = ("Date", "Start Time", "End Time", "Break", "Hours Worked", "Remarks")
        self.grid_tree = ttk.Treeview(self.detail_panel, columns=grid_cols, show="headings", selectmode="browse")
        for col in grid_cols:
            self.grid_tree.heading(col, text=col)
        self.grid_tree.column("Date", width=90, anchor=tk.CENTER)
        self.grid_tree.column("Start Time", width=80, anchor=tk.CENTER)
        self.grid_tree.column("End Time", width=80, anchor=tk.CENTER)
        self.grid_tree.column("Break", width=60, anchor=tk.CENTER)
        self.grid_tree.column("Hours Worked", width=100, anchor=tk.CENTER)
        self.grid_tree.column("Remarks", width=150)
        
        grid_scrollbar = ttk.Scrollbar(self.detail_panel, orient=tk.VERTICAL, command=self.grid_tree.yview)
        self.grid_tree.configure(yscrollcommand=grid_scrollbar.set)
        self.grid_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.grid_tree)
        
        self.grid_tree.bind("<Double-1>", self.on_grid_double_click)

        # Refresh combinations
        self.refresh_timesheet_combos()
        self.load_timesheets()

    def refresh_timesheet_combos(self):
        # 1. Cities
        cities = ["All Cities"] + [c["name"] for c in models.get_cities()]
        self.filter_city_combo["values"] = cities
        if not self.filter_city_combo.get():
            self.filter_city_combo.set("All Cities")
            
        # 2. Months (standard query or hardcoded recent)
        months = ["All Months", "01.2026", "02.2026", "03.2026", "04.2026", "05.2026", "06.2026", "07.2026", "08.2026", "09.2026", "10.2026", "11.2026", "12.2026"]
        self.filter_month_combo["values"] = months
        if not self.filter_month_combo.get():
            self.filter_month_combo.set("All Months")

    def load_timesheets(self):
        selected_city = self.filter_city_combo.get()
        selected_month_str = self.filter_month_combo.get()
        
        # Resolve IDs
        city_id = None
        if selected_city != "All Cities":
            for c in models.get_cities():
                if c["name"] == selected_city:
                    city_id = c["id"]
                    break
        
        year, month = None, None
        if selected_month_str != "All Months":
            try:
                parts = selected_month_str.split('.')
                month, year = int(parts[0]), int(parts[1])
            except:
                pass
                
        # Load sheets
        self.timesheets_tree.delete(*self.timesheets_tree.get_children())
        for ts in models.get_timesheets(city_id=city_id, year=year, month=month):
            locked_str = "Yes" if ts["is_distribution_locked"] else "No"
            self.timesheets_tree.insert(
                "", tk.END, values=(
                    ts["id"], ts["employee_name"], ts["city_name"],
                    f"{ts['month']:02d}.{ts['year']}", ts["target_hours"],
                    ts["status"], locked_str
                )
            )
        self.clear_detail_panel()

    def clear_detail_panel(self):
        self.meta_lbl.config(text="No timesheet selected.")
        self.grid_tree.delete(*self.grid_tree.get_children())
        # Disable detail buttons
        self.btn_single_solve.state(["disabled"])
        self.btn_batch_solve.state(["disabled"])
        self.btn_finalize.state(["disabled"])
        self.btn_revert.state(["disabled"])

    def on_timesheet_select(self, event):
        selected = self.timesheets_tree.selection()
        if not selected:
            self.clear_detail_panel()
            return
            
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        
        # Load details
        ts = models.get_timesheet_with_entries(ts_id)
        if not ts:
            self.clear_detail_panel()
            return
            
        self.meta_lbl.config(
            text=f"{ts['employee_name']} - {ts['city_name']} ({ts['month']:02d}.{ts['year']}) | Target: {ts['target_hours']}h | Status: {ts['status']}"
        )
        
        # Enable action buttons appropriately
        self.btn_single_solve.state(["!disabled"])
        self.btn_batch_solve.state(["!disabled"])
        if ts["status"] == "Finalized":
            self.btn_finalize.state(["disabled"])
            self.btn_revert.state(["!disabled"])
            self.btn_single_solve.state(["disabled"])
            self.btn_batch_solve.state(["disabled"])
        else:
            self.btn_finalize.state(["!disabled"])
            self.btn_revert.state(["disabled"])
            self.btn_single_solve.state(["!disabled"])
            self.btn_batch_solve.state(["!disabled"])
            
        # Load daily entries grid
        self.grid_tree.delete(*self.grid_tree.get_children())
        for entry in ts["entries"]:
            work_date = entry["work_date"]
            # format to German date in treeview
            formatted_date = work_date
            if '-' in work_date:
                dt = datetime.strptime(work_date, "%Y-%m-%d")
                formatted_date = dt.strftime("%d.%m.%Y")
                
            hours_str = ""
            if entry["hours_worked"] > 0:
                hours_str = f"{entry['hours_worked']:.1f}".replace(".", ",")
                
            self.grid_tree.insert(
                "", tk.END, values=(
                    formatted_date, entry["start_time"], entry["end_time"],
                    entry["break_duration"], hours_str, entry["remarks"]
                )
            )

    # ==============================================================================
    # Timesheet Creation Dialog
    # ==============================================================================
    def new_timesheet_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Timesheet")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Fetch data for combos
        drivers = models.get_employees()
        cities = models.get_cities()
        
        if not drivers or not cities:
            messagebox.showerror("Error", "You must add at least one driver and one city first.")
            dialog.destroy()
            return
            
        ttk.Label(dialog, text="Select Driver:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        driver_combo = ttk.Combobox(dialog, values=[d["name"] for d in drivers], state="readonly", width=25)
        driver_combo.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Select City:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        city_combo = ttk.Combobox(dialog, values=[c["name"] for c in cities], state="readonly", width=25)
        city_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Month & Year (MM.YYYY):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        month_var = tk.StringVar(value=datetime.now().strftime("%m.%Y"))
        ttk.Entry(dialog, textvariable=month_var, width=27).grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Target Hours:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        target_var = tk.StringVar(value="80.0")
        ttk.Entry(dialog, textvariable=target_var, width=27).grid(row=3, column=1, padx=10, pady=10)
        
        def create():
            d_name = driver_combo.get()
            c_name = city_combo.get()
            m_year = month_var.get().strip()
            target_str = target_var.get().strip()
            
            if not d_name or not c_name or not m_year or not target_str:
                messagebox.showerror("Error", "All fields are required.")
                return
                
            try:
                parts = m_year.split('.')
                month, year = int(parts[0]), int(parts[1])
                if not (1 <= month <= 12) or year < 2000:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Invalid Month/Year format. Use MM.YYYY (e.g. 06.2026).")
                return
                
            # Current or future month restriction
            now = datetime.now()
            if year < now.year or (year == now.year and month < now.month):
                messagebox.showerror("Error", "Timesheets can only be created for the current or future months.")
                return
                
            try:
                target_hours = float(target_str.replace(",", "."))
                if target_hours % 0.5 != 0:
                    raise ValueError("Must be a multiple of 0.5")
            except:
                messagebox.showerror("Error", "Target hours must be a valid number and a multiple of 0.5.")
                return
                
            # Bounds checking
            _, num_days = calendar.monthrange(year, month)
            max_wd = (num_days // 7) * 6 + min(num_days % 7, 6)
            max_hours_allowed = max_wd * 8.0
            
            if target_hours < 10.0 or target_hours > max_hours_allowed:
                messagebox.showerror(
                    "Error",
                    f"Target hours must be within bounds: [10.0, {max_hours_allowed}].\n"
                    f"(For a {num_days}-day month, maximum workdays under 6-consecutive-day limit is {max_wd} days)"
                )
                return
                
            # Fetch IDs
            emp_id = next(d["id"] for d in drivers if d["name"] == d_name)
            city_id = next(c["id"] for c in cities if c["name"] == c_name)
            
            try:
                models.create_timesheet(emp_id, city_id, year, month, target_hours)
                self.write_log(f"[DB] Created timesheet for {d_name} in {c_name} ({m_year})")
                self.load_timesheets()
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Timesheet already exists for this driver, city, and month.")
                
        ttk.Button(dialog, text="Create", command=create).grid(row=4, column=0, columnspan=2, pady=15)

    def delete_timesheet(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            messagebox.showwarning("Select Timesheet", "Please select a timesheet to delete.")
            return
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete timesheet ID {ts_id}?")
        if confirm:
            models.delete_timesheet(ts_id)
            self.write_log(f"[DB] Deleted timesheet ID {ts_id}")
            self.load_timesheets()

    # ==============================================================================
    # Finalize, Revert, Export
    # ==============================================================================
    def finalize_timesheet(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            return
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        models.update_timesheet_status(ts_id, "Finalized")
        self.write_log(f"[DB] Finalized timesheet ID {ts_id}")
        self.load_timesheets()

    def revert_timesheet(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            return
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        models.update_timesheet_status(ts_id, "Draft")
        self.write_log(f"[DB] Reverted timesheet ID {ts_id} to Draft")
        self.load_timesheets()

    def export_timesheet(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            messagebox.showwarning("Select Timesheet", "Please select a timesheet to export.")
            return
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        
        ts = models.get_timesheet_with_entries(ts_id)
        if not ts:
            return
            
        clean_name = "".join(c for c in ts["employee_name"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        initial_name = f"timesheet_{clean_name}_{ts['month']:02d}_{ts['year']}.docx"
        
        dest = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
            initialfile=initial_name,
            title="Export Timesheet"
        )
        if dest:
            try:
                docx_exporter.generate_docx(
                    employee_name=ts["employee_name"],
                    personal_id=ts["personal_id"],
                    city_name=ts["city_name"],
                    year=ts["year"],
                    month=ts["month"],
                    daily_entries=ts["entries"],
                    target_hours=ts["target_hours"],
                    output_path=dest
                )
                messagebox.showinfo("Export Success", f"Word document exported to:\n{dest}")
                self.write_log(f"[Export] Document saved successfully to {dest}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export document:\n{e}")
                self.write_log(f"[Error] Export failed: {e}")

    # ==============================================================================
    # Solver execution helper
    # ==============================================================================
    def run_solver_background(self, solver_input: sat_solver.SolverInput, callback_success):
        """Runs the CP-SAT solver in a background thread to prevent UI freezing."""
        self.write_log(f"[Solver] Starting solve calculations ({solver_input.mode} mode)...")
        
        def run():
            try:
                result = sat_solver.solve(solver_input)
                self.root.after(0, lambda: callback_success(result))
            except Exception as e:
                self.write_log(f"[Error] Solver runtime exception: {e}")
                self.root.after(0, lambda: messagebox.showerror("Solver Error", f"Solver encountered an exception:\n{e}"))
                
        threading.Thread(target=run, daemon=True).start()

    # ==============================================================================
    # 3.1 Single Driver Solver (Incremental Mode)
    # ==============================================================================
    def solve_single_timesheet(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            return
        values = self.timesheets_tree.item(selected[0], "values")
        ts_id = int(values[0])
        
        # Load timesheet
        ts = models.get_timesheet_with_entries(ts_id)
        if not ts:
            return
            
        # Re-run overwrite confirmation
        if ts["entries"]:
            confirm_overwrite = messagebox.askyesno(
                "Overwrite Confirmation",
                "This timesheet already has daily entries. Overwrite existing schedule?",
                icon="warning"
            )
            if not confirm_overwrite:
                return

        # Incremental warning
        confirm_inc = messagebox.askyesno(
            "Incremental warning",
            "Single driver distribution mode is not optimal. Batch execution for all drivers in a city is preferred.\n\nDo you want to proceed anyway?",
            icon="warning"
        )
        if not confirm_inc:
            return
            
        # Load city details
        city_rows = [c for c in models.get_cities() if c["name"] == ts["city_name"]]
        if not city_rows:
            return
        city = city_rows[0]
        
        # Prepare Solver Input
        driver_spec = sat_solver.DriverSpec(
            employee_id=ts["employee_id"],
            target_units=sat_solver.hours_to_units(ts["target_hours"]),
            name=ts["employee_name"]
        )
        
        prev_month = models.get_previous_month_boundary(ts["employee_id"], ts["year"], ts["month"])
        cross_city = models.get_cross_city_active_days(ts["employee_id"], ts["year"], ts["month"], ts["city_id"])
        
        # Stagger against all other timesheets in the same city/month
        existing_cov = models.get_city_coverage(ts["city_id"], ts["year"], ts["month"], exclude_timesheet_ids=[ts_id])
        
        # Locked entries of other drivers in the same city
        locked_entries = {}
        for other_ts in models.get_timesheets(city_id=ts["city_id"], year=ts["year"], month=ts["month"]):
            if other_ts["id"] != ts_id and other_ts["is_distribution_locked"]:
                other_entries = models.get_timesheet_with_entries(other_ts["id"])["entries"]
                locked_entries[other_ts["employee_id"]] = other_entries
                
        _, num_days = calendar.monthrange(ts["year"], ts["month"])
        
        solver_input = sat_solver.SolverInput(
            drivers=[driver_spec],
            city_start=sat_solver.clock_to_units(city["start_time"]),
            city_end=sat_solver.clock_to_units(city["end_time"]),
            num_days=num_days,
            prev_month_boundary={ts["employee_id"]: prev_month},
            cross_city_active={ts["employee_id"]: cross_city},
            existing_coverage=existing_cov,
            locked_entries=locked_entries,
            mode='incremental'
        )
        
        def on_success(result: sat_solver.SolverResult):
            self.write_log(f"[Solver] Complete. Status: {result.status}. Dev: {result.target_deviation}h. Solve Time: {result.solve_time_seconds:.2f}s")
            
            if result.status == 'failed':
                messagebox.showerror("Solver Failed", "Could not find a feasible shift schedule satisfying constraints.")
                return
                
            if result.status == 'nearest':
                # Accept nearest feasible prompt
                accept = messagebox.askyesno(
                    "Nearest Feasible Result",
                    f"Exact target of {ts['target_hours']} hours could not be achieved.\n"
                    f"Nearest feasible: {ts['target_hours'] - result.target_deviation:.1f} hours.\n\n"
                    f"Do you want to accept this schedule?",
                    icon="question"
                )
                if not accept:
                    return
            
            # Save results
            schedule = result.schedules[ts["employee_id"]]
            db_entries = []
            for entry in schedule:
                # convert DayEntry to dict
                work_date = f"{ts['year']}-{ts['month']:02d}-{entry.day:02d}"
                break_str = "00:30" if entry.break_minutes == 30 else "00:00"
                db_entries.append({
                    "work_date": work_date,
                    "hours_worked": entry.hours,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "break_duration": break_str,
                    "remarks": ""
                })
            models.save_daily_entries(ts_id, db_entries)
            self.write_log(f"[DB] Saved distributed entries for timesheet ID {ts_id}")
            self.load_timesheets()
            
        self.run_solver_background(solver_input, on_success)

    # ==============================================================================
    # 3.2 Batch Solver (City Batch Mode)
    # ==============================================================================
    def solve_batch_timesheets(self):
        selected = self.timesheets_tree.selection()
        if not selected:
            messagebox.showwarning("Batch solve", "Please select a timesheet to define the city and month context.")
            return
            
        values = self.timesheets_tree.item(selected[0], "values")
        selected_ts = models.get_timesheet_with_entries(int(values[0]))
        if not selected_ts:
            return
            
        city_id = selected_ts["city_id"]
        year = selected_ts["year"]
        month = selected_ts["month"]
        
        # Load city
        city_rows = [c for c in models.get_cities() if c["id"] == city_id]
        if not city_rows:
            return
        city = city_rows[0]
        
        # Fetch all Draft timesheets in this city/month
        all_timesheets = models.get_timesheets(city_id=city_id, year=year, month=month, status="Draft")
        
        # Partition into Active (unlocked) and Locked
        active_sheets = [ts for ts in all_timesheets if not ts["is_distribution_locked"]]
        locked_sheets = [ts for ts in all_timesheets if ts["is_distribution_locked"]]
        
        if not active_sheets:
            messagebox.showwarning("Batch Solve", "There are no unlocked Draft timesheets in this city/month to distribute.")
            return
            
        # Re-run overwrite check
        has_existing = any(len(models.get_timesheet_with_entries(ts["id"])["entries"]) > 0 for ts in active_sheets)
        if has_existing:
            confirm_overwrite = messagebox.askyesno(
                "Overwrite Confirmation",
                "Some active timesheets already contain daily entries. Replace existing schedules?",
                icon="warning"
            )
            if not confirm_overwrite:
                return
                
        # Build solver drivers list
        drivers = []
        prev_month_boundary = {}
        cross_city_active = {}
        
        for ts in active_sheets:
            drivers.append(sat_solver.DriverSpec(
                employee_id=ts["employee_id"],
                target_units=sat_solver.hours_to_units(ts["target_hours"]),
                name=ts["employee_name"]
            ))
            prev_month_boundary[ts["employee_id"]] = models.get_previous_month_boundary(ts["employee_id"], year, month)
            cross_city_active[ts["employee_id"]] = models.get_cross_city_active_days(ts["employee_id"], year, month, city_id)
            
        # Build locked entries
        locked_entries = {}
        for ts in locked_sheets:
            ts_detail = models.get_timesheet_with_entries(ts["id"])
            locked_entries[ts["employee_id"]] = ts_detail["entries"]
            
        _, num_days = calendar.monthrange(year, month)
        
        solver_input = sat_solver.SolverInput(
            drivers=drivers,
            city_start=sat_solver.clock_to_units(city["start_time"]),
            city_end=sat_solver.clock_to_units(city["end_time"]),
            num_days=num_days,
            prev_month_boundary=prev_month_boundary,
            cross_city_active=cross_city_active,
            existing_coverage={},
            locked_entries=locked_entries,
            mode='batch'
        )
        
        def on_success(result: sat_solver.SolverResult):
            self.write_log(f"[Solver] Batch Complete. Status: {result.status}. Dev: {result.target_deviation}h. Solve Time: {result.solve_time_seconds:.2f}s")
            
            if result.status == 'failed':
                messagebox.showerror("Solver Failed", "Could not find a feasible distribution satisfying constraints.")
                return
                
            if result.status == 'nearest':
                accept = messagebox.askyesno(
                    "Nearest Feasible Result",
                    f"Exact targets could not be achieved.\n"
                    f"Total deviation: {result.target_deviation:.1f} hours.\n\n"
                    f"Do you want to accept this schedule?",
                    icon="question"
                )
                if not accept:
                    return
                    
            # Save results for all active drivers
            for ts in active_sheets:
                schedule = result.schedules[ts["employee_id"]]
                db_entries = []
                for entry in schedule:
                    work_date = f"{year}-{month:02d}-{entry.day:02d}"
                    break_str = "00:30" if entry.break_minutes == 30 else "00:00"
                    db_entries.append({
                        "work_date": work_date,
                        "hours_worked": entry.hours,
                        "start_time": entry.start_time,
                        "end_time": entry.end_time,
                        "break_duration": break_str,
                        "remarks": ""
                    })
                models.save_daily_entries(ts["id"], db_entries)
                self.write_log(f"[DB] Saved distributed entries for timesheet ID {ts['id']}")
                
            self.load_timesheets()
            
        self.run_solver_background(solver_input, on_success)

    # ==============================================================================
    # 4. Post-Solver Manual Edit Workflow
    # ==============================================================================
    def on_grid_double_click(self, event):
        # Prevent editing if timesheet is Finalized
        selected_ts_idx = self.timesheets_tree.selection()
        if not selected_ts_idx:
            return
        ts_values = self.timesheets_tree.item(selected_ts_idx[0], "values")
        ts_id = int(ts_values[0])
        ts = models.get_timesheet_with_entries(ts_id)
        if ts.get("status") == "Finalized":
            messagebox.showwarning("Edit Blocked", "Finalized timesheets cannot be modified. Revert to Draft first.")
            return

        selected_grid_idx = self.grid_tree.selection()
        if not selected_grid_idx:
            return
        grid_values = self.grid_tree.item(selected_grid_idx[0], "values")
        
        # grid_values contains: Date, Start Time, End Time, Break, Hours Worked, Remarks
        date_str = grid_values[0]
        start_time = grid_values[1]
        end_time = grid_values[2]
        break_dur = grid_values[3]
        hours_str = grid_values[4]
        remarks = grid_values[5]
        
        self.manual_edit_dialog(ts, date_str, start_time, end_time, break_dur, hours_str, remarks)

    def manual_edit_dialog(self, ts: dict, date_str: str, start: str, end: str, break_dur: str, hours_str: str, remarks_str: str):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Shift - {date_str}")
        dialog.geometry("340x260")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Start Time (HH:MM):").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        start_var = tk.StringVar(value=start)
        ttk.Entry(dialog, textvariable=start_var, width=25).grid(row=0, column=1, padx=10, pady=8)
        
        ttk.Label(dialog, text="End Time (HH:MM):").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        end_var = tk.StringVar(value=end)
        ttk.Entry(dialog, textvariable=end_var, width=25).grid(row=1, column=1, padx=10, pady=8)
        
        ttk.Label(dialog, text="Break (HH:MM):").grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
        break_var = tk.StringVar(value=break_dur if break_dur else "00:00")
        ttk.Entry(dialog, textvariable=break_var, width=25).grid(row=2, column=1, padx=10, pady=8)
        
        ttk.Label(dialog, text="Hours Worked:").grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
        hours_var = tk.StringVar(value=hours_str.replace(",", "."))
        ttk.Entry(dialog, textvariable=hours_var, width=25).grid(row=3, column=1, padx=10, pady=8)
        
        ttk.Label(dialog, text="Remarks:").grid(row=4, column=0, padx=10, pady=8, sticky=tk.W)
        remarks_var = tk.StringVar(value=remarks_str)
        ttk.Entry(dialog, textvariable=remarks_var, width=25).grid(row=4, column=1, padx=10, pady=8)
        
        def save():
            h_str = hours_var.get().strip()
            st = start_var.get().strip()
            et = end_var.get().strip()
            br = break_var.get().strip()
            rem = remarks_var.get().strip()
            
            # Validation
            try:
                hours_val = 0.0
                if h_str:
                    hours_val = float(h_str.replace(",", "."))
                if hours_val < 0.0:
                    raise ValueError()
            except:
                messagebox.showerror("Error", "Hours worked must be a valid positive number.")
                return
                
            # If hours > 0, times must be HH:MM
            if hours_val > 0.0:
                for clk in (st, et, br):
                    try:
                        parts = clk.split(":")
                        if len(parts) != 2 or not (0 <= int(parts[0]) <= 23) or not (0 <= int(parts[1]) <= 59):
                            raise ValueError()
                    except:
                        messagebox.showerror("Error", "Times must be in HH:MM format.")
                        return
            else:
                st = ""
                et = ""
                br = ""
                
            # Update local dict first for validation checks
            # convert date back to ISO format
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            day_num = dt.day
            
            new_entries = []
            for entry in ts["entries"]:
                if entry["work_date"] == iso_date:
                    new_entries.append({
                        "work_date": iso_date,
                        "hours_worked": hours_val,
                        "start_time": st,
                        "end_time": et,
                        "break_duration": br,
                        "remarks": rem
                    })
                else:
                    new_entries.append(entry)
                    
            # ---------------------------------------------------------
            # Soft Validation Warnings (Triggered before prompt)
            # ---------------------------------------------------------
            warnings = []
            
            # 1. Total hours validation
            total_sum = sum(e["hours_worked"] for e in new_entries)
            if abs(total_sum - ts["target_hours"]) > 0.01:
                warnings.append(f"- Total hours ({total_sum:.1f}) differ from target ({ts['target_hours']:.1f}).")
                
            # 2. Shift bounds
            if hours_val > 0.0 and (hours_val < 2.0 or hours_val > 8.0):
                warnings.append(f"- Shift on {date_str} ({hours_val:.1f}h) falls outside [2.0, 8.0] range.")
                
            # 3. City window bounds
            city_rows = [c for c in models.get_cities() if c["id"] == ts["city_id"]]
            if city_rows and hours_val > 0.0:
                city = city_rows[0]
                c_st = sat_solver.clock_to_units(city["start_time"])
                c_et = sat_solver.clock_to_units(city["end_time"])
                st_slot = sat_solver.clock_to_units(st)
                et_slot = sat_solver.clock_to_units(et)
                if st_slot < c_st or et_slot > c_et:
                    warnings.append(f"- Shift on {date_str} falls outside city operational hours ({city['start_time']} - {city['end_time']}).")
                    
            # 4. 6-consecutive-day limit check globally
            prev_month = models.get_previous_month_boundary(ts["employee_id"], ts["year"], ts["month"])
            cross_city = models.get_cross_city_active_days(ts["employee_id"], ts["year"], ts["month"], ts["city_id"])
            
            combined_active = []
            for prev_val in prev_month:
                combined_active.append(prev_val)
                
            _, num_days = calendar.monthrange(ts["year"], ts["month"])
            for d in range(1, num_days + 1):
                cross_city_active_day = cross_city.get(d, 0)
                if cross_city_active_day == 1:
                    combined_active.append(1)
                else:
                    # check new entries
                    is_active = 0
                    for e in new_entries:
                        e_day = int(e["work_date"].split('-')[2])
                        if e_day == d and e["hours_worked"] > 0.0:
                            is_active = 1
                            break
                    combined_active.append(is_active)
                    
            violation = False
            for i in range(len(combined_active) - 6):
                if sum(combined_active[i:i+7]) > 6:
                    violation = True
                    break
            if violation:
                warnings.append("- Driver schedule violates the limit of max 6 consecutive workdays globally.")
                
            if warnings:
                warning_msg = "Soft validation warnings:\n" + "\n".join(warnings) + "\n\nDo you want to save anyway?"
                save_anyway = messagebox.askyesno("Soft Validation Warnings", warning_msg, icon="warning")
                if not save_anyway:
                    return

            # ---------------------------------------------------------
            # Lock vs Redistribute Prompt
            # ---------------------------------------------------------
            prompt_dialog = tk.Toplevel(self.root)
            prompt_dialog.title("Save Action")
            prompt_dialog.geometry("380x160")
            prompt_dialog.resizable(False, False)
            prompt_dialog.grab_set()
            
            ttk.Label(
                prompt_dialog,
                text="How would you like to save these edits?",
                font=("Segoe UI", 10, "bold")
            ).pack(pady=10)
            
            def lock_only():
                # Lock timesheet and save directly
                models.save_daily_entries(ts["id"], new_entries)
                models.set_distribution_lock(ts["id"], True)
                self.write_log(f"[DB] Saved edits and locked timesheet ID {ts['id']}")
                self.load_timesheets()
                prompt_dialog.destroy()
                dialog.destroy()
                
            def apply_all():
                # Save edits, treat driver as a fixed constraint, and solve for all other Draft, non-locked timesheets
                models.save_daily_entries(ts["id"], new_entries)
                self.write_log(f"[DB] Saved edits for timesheet ID {ts['id']}. Triggering redistribution...")
                prompt_dialog.destroy()
                dialog.destroy()
                
                # Re-run batch solver (will automatically treat this driver as locked or load their schedule as fixed constraint)
                self.solve_batch_timesheets_with_fixed_driver(ts, new_entries)
                
            btn_frame = ttk.Frame(prompt_dialog)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="Lock Driver Only", command=lock_only).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="Apply & Redistribute Others", command=apply_all).pack(side=tk.LEFT, padx=10)
            ttk.Button(btn_frame, text="Cancel", command=prompt_dialog.destroy).pack(side=tk.LEFT, padx=10)

        ttk.Button(dialog, text="Save", command=save).grid(row=5, column=0, columnspan=2, pady=15)

    def solve_batch_timesheets_with_fixed_driver(self, edited_ts: dict, edited_entries: list):
        """
        Runs batch redistribution for all Draft, non-locked timesheets in the city,
        treating the edited driver's timesheet as a locked (read-only) constraint.
        """
        city_id = edited_ts["city_id"]
        year = edited_ts["year"]
        month = edited_ts["month"]
        
        # Load city
        city_rows = [c for c in models.get_cities() if c["id"] == city_id]
        if not city_rows:
            return
        city = city_rows[0]
        
        # Fetch all Draft timesheets in this city/month
        all_timesheets = models.get_timesheets(city_id=city_id, year=year, month=month, status="Draft")
        
        # Treat the edited driver as LOCKED for the solver run, even if database lock flag is False
        # (This is the "Apply to all workers" behavior)
        active_sheets = [ts for ts in all_timesheets if not ts["is_distribution_locked"] and ts["id"] != edited_ts["id"]]
        locked_sheets = [ts for ts in all_timesheets if ts["is_distribution_locked"] or ts["id"] == edited_ts["id"]]
        
        if not active_sheets:
            self.write_log("[System] No other unlocked timesheets to redistribute. Edits saved.")
            self.load_timesheets()
            return
            
        # Build solver drivers list
        drivers = []
        prev_month_boundary = {}
        cross_city_active = {}
        
        for ts in active_sheets:
            drivers.append(sat_solver.DriverSpec(
                employee_id=ts["employee_id"],
                target_units=sat_solver.hours_to_units(ts["target_hours"]),
                name=ts["employee_name"]
            ))
            prev_month_boundary[ts["employee_id"]] = models.get_previous_month_boundary(ts["employee_id"], year, month)
            cross_city_active[ts["employee_id"]] = models.get_cross_city_active_days(ts["employee_id"], year, month, city_id)
            
        # Build locked entries
        locked_entries = {}
        for ts in locked_sheets:
            if ts["id"] == edited_ts["id"]:
                locked_entries[ts["employee_id"]] = edited_entries
            else:
                ts_detail = models.get_timesheet_with_entries(ts["id"])
                locked_entries[ts["employee_id"]] = ts_detail["entries"]
                
        _, num_days = calendar.monthrange(year, month)
        
        solver_input = sat_solver.SolverInput(
            drivers=drivers,
            city_start=sat_solver.clock_to_units(city["start_time"]),
            city_end=sat_solver.clock_to_units(city["end_time"]),
            num_days=num_days,
            prev_month_boundary=prev_month_boundary,
            cross_city_active=cross_city_active,
            existing_coverage={},
            locked_entries=locked_entries,
            mode='batch'
        )
        
        def on_success(result: sat_solver.SolverResult):
            self.write_log(f"[Solver] Batch Complete (Redistribution). Status: {result.status}. Dev: {result.target_deviation}h. Solve time: {result.solve_time_seconds:.2f}s")
            
            if result.status == 'failed':
                messagebox.showerror("Solver Failed", "Redistribution could not find a feasible schedule. Try locking or editing manually.")
                self.load_timesheets()
                return
                
            if result.status == 'nearest':
                accept = messagebox.askyesno(
                    "Nearest Feasible Result",
                    f"Redistribution exact targets could not be achieved.\n"
                    f"Total deviation: {result.target_deviation:.1f} hours.\n\n"
                    f"Do you want to accept this schedule?",
                    icon="question"
                )
                if not accept:
                    self.load_timesheets()
                    return
                    
            # Save results for all active drivers
            for ts in active_sheets:
                schedule = result.schedules[ts["employee_id"]]
                db_entries = []
                for entry in schedule:
                    work_date = f"{year}-{month:02d}-{entry.day:02d}"
                    break_str = "00:30" if entry.break_minutes == 30 else "00:00"
                    db_entries.append({
                        "work_date": work_date,
                        "hours_worked": entry.hours,
                        "start_time": entry.start_time,
                        "end_time": entry.end_time,
                        "break_duration": break_str,
                        "remarks": ""
                    })
                models.save_daily_entries(ts["id"], db_entries)
                self.write_log(f"[DB] Saved redistributed entries for timesheet ID {ts['id']}")
                
            self.load_timesheets()
            
        self.run_solver_background(solver_input, on_success)
