import os
import calendar
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import customtkinter as ctk

import db.models as models
import db.database as database
import solver.sat_solver as sat_solver
import exporter.docx_exporter as docx_exporter

class TimesheetAppGUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Timesheet & Driver Shift Distribution System")
        self.root.geometry("1150x800")
        self.root.minsize(1050, 700)
        
        # Apply standard system style for Treeview styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Initialize Database connection
        database.initialize_database()
        
        # Build UI layout
        self.setup_header()
        self.setup_menu()
        self.setup_tabs()
        self.setup_log_panel()
        
        # Initialize Treeview styling based on the theme
        self.update_treeview_styles()
        
        self.write_log("[System] Initialized successfully. Ready.")

    def setup_header(self):
        """Creates a header bar with application title and dark/light mode toggle."""
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            header_frame, 
            text="Driver Shift & Timesheet Distribution", 
            font=("Segoe UI", 20, "bold")
        ).pack(side=tk.LEFT)
        
        self.theme_switch = ctk.CTkSwitch(
            header_frame, 
            text="Dark Mode", 
            command=self.toggle_theme,
            font=("Segoe UI", 11, "bold")
        )
        self.theme_switch.pack(side=tk.RIGHT, padx=10)
        
        # Default theme switch position based on system appearance
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

    def toggle_theme(self):
        """Toggles application appearance between Dark and Light mode."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
            
        self.update_treeview_styles()
        
        if hasattr(self, 'analytics_tab'):
            self.analytics_tab.refresh_selectors()

    def update_treeview_styles(self):
        """Styles the native TTK Treeview widgets dynamically to fit CustomTkinter theme."""
        is_dark = (ctk.get_appearance_mode() == "Dark")
        
        bg = "#2b2b2b" if is_dark else "#ffffff"
        fg = "#ffffff" if is_dark else "#000000"
        field_bg = "#2b2b2b" if is_dark else "#ffffff"
        selected_bg = "#1f538d" if is_dark else "#3a7ebf"
        heading_bg = "#212121" if is_dark else "#eaeaea"
        heading_fg = "#ffffff" if is_dark else "#000000"
        
        self.style.configure("Treeview", 
                             background=bg, 
                             foreground=fg, 
                             fieldbackground=field_bg, 
                             rowheight=26,
                             font=("Segoe UI", 10),
                             borderwidth=0,
                             relief="flat")
        self.style.configure("Treeview.Heading", 
                             background=heading_bg, 
                             foreground=heading_fg, 
                             font=("Segoe UI", 10, "bold"),
                             borderwidth=1,
                             relief="flat")
        self.style.map("Treeview", background=[("selected", selected_bg)])

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
        """Setup a collapsible log console at the bottom."""
        self.log_container = ctk.CTkFrame(self.root, corner_radius=12)
        self.log_container.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(0, 15))
        
        header = ctk.CTkFrame(self.log_container, fg_color="transparent", height=32)
        header.pack(fill=tk.X, padx=15, pady=6)
        
        ctk.CTkLabel(
            header, 
            text="Solver Calculation Logs", 
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.LEFT)
        
        self.btn_toggle_logs = ctk.CTkButton(
            header, 
            text="Collapse Logs", 
            width=110, 
            height=24, 
            fg_color="#4a5568", 
            hover_color="#2d3748", 
            font=("Segoe UI", 11),
            command=self.toggle_log_panel
        )
        self.btn_toggle_logs.pack(side=tk.RIGHT)
        
        self.log_inner_frame = ctk.CTkFrame(self.log_container, fg_color="transparent")
        self.log_inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.log_txt = ctk.CTkTextbox(
            self.log_inner_frame, 
            height=90, 
            font=("Courier New", 12)
        )
        self.log_txt.pack(fill=tk.BOTH, expand=True)
        self.log_txt.configure(state=tk.DISABLED)
        self.logs_collapsed = False

    def toggle_log_panel(self):
        """Collapses or expands the logs panel to save screen space."""
        if self.logs_collapsed:
            self.log_inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
            self.btn_toggle_logs.configure(text="Collapse Logs")
            self.logs_collapsed = False
        else:
            self.log_inner_frame.pack_forget()
            self.btn_toggle_logs.configure(text="Expand Logs")
            self.logs_collapsed = True

    def write_log(self, text: str):
        """Thread-safe logging into bottom console."""
        def append_log():
            self.log_txt.configure(state=tk.NORMAL)
            self.log_txt.insert(tk.END, text + "\n")
            self.log_txt.see(tk.END)
            self.log_txt.configure(state=tk.DISABLED)
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

    def on_tab_changed(self):
        try:
            selected_tab = self.tabview.get()
            if selected_tab == "Analytics" and hasattr(self, 'analytics_tab'):
                self.analytics_tab.refresh_selectors()
        except Exception as e:
            pass

    # ==============================================================================
    # Notebook Tabs Construction
    # ==============================================================================
    def setup_tabs(self):
        self.tabview = ctk.CTkTabview(self.root, command=self.on_tab_changed)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        
        self.tabview.add("Cities")
        self.tabview.add("Drivers")
        self.tabview.add("Timesheets")
        self.tabview.add("Analytics")
        
        self.setup_cities_tab()
        self.setup_drivers_tab()
        self.setup_timesheets_tab()
        
        # Setup Analytics tab
        from ui.analytics_tab import AnalyticsTab
        self.analytics_tab = AnalyticsTab(self.tabview.tab("Analytics"), self)
        self.analytics_tab.pack(fill=tk.BOTH, expand=True)

    # ==============================================================================
    # 1. Cities Tab
    # ==============================================================================
    def setup_cities_tab(self):
        cities_frame = self.tabview.tab("Cities")
        
        # Left Panel: Table
        tree_frame = ctk.CTkFrame(cities_frame, corner_radius=12)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        ctk.CTkLabel(
            tree_frame, 
            text="Configured Cities & Delivery Windows", 
            font=("Segoe UI", 15, "bold")
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        inner_tree_frame = ctk.CTkFrame(tree_frame, fg_color="transparent")
        inner_tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        cols = ("ID", "Name", "Start Time", "End Time")
        self.cities_tree = ttk.Treeview(inner_tree_frame, columns=cols, show="headings", selectmode="extended")
        for col in cols:
            self.cities_tree.heading(col, text=col)
        self.cities_tree.column("ID", width=60, stretch=False)
        self.cities_tree.column("Name", width=220)
        self.cities_tree.column("Start Time", width=120, anchor=tk.CENTER)
        self.cities_tree.column("End Time", width=120, anchor=tk.CENTER)
        
        scrollbar = ctk.CTkScrollbar(inner_tree_frame, command=self.cities_tree.yview)
        self.cities_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cities_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right Panel: Actions
        btn_frame = ctk.CTkFrame(cities_frame, width=220, corner_radius=12)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=10)
        
        ctk.CTkLabel(
            btn_frame, 
            text="Actions", 
            font=("Segoe UI", 15, "bold")
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="Add City...", 
            fg_color="#1a365d", 
            hover_color="#2b6cb0", 
            command=self.add_city_dialog
        ).pack(fill=tk.X, padx=15, pady=8)
        
        ctk.CTkButton(
            btn_frame, 
            text="Edit Selected...", 
            command=self.edit_city_dialog
        ).pack(fill=tk.X, padx=15, pady=8)
        
        ctk.CTkButton(
            btn_frame, 
            text="Delete City", 
            fg_color="#742a2a", 
            hover_color="#9b2c2c", 
            command=self.delete_city
        ).pack(fill=tk.X, padx=15, pady=8)
        
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
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_frame, text="City Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=values[1] if values else "")
        ctk.CTkEntry(main_frame, textvariable=name_var, width=180).grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="Start Time (HH:MM):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        start_var = tk.StringVar(value=values[2] if values else "08:00")
        ctk.CTkEntry(main_frame, textvariable=start_var, width=180).grid(row=1, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(main_frame, text="End Time (HH:MM):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        end_var = tk.StringVar(value=values[3] if values else "22:00")
        ctk.CTkEntry(main_frame, textvariable=end_var, width=180).grid(row=2, column=1, padx=10, pady=10)
        
        warning_lbl = ctk.CTkLabel(main_frame, text="", text_color="#e53e3e", font=("Segoe UI", 10))
        warning_lbl.grid(row=3, column=0, columnspan=2, pady=(0, 5))
        
        def save():
            name = name_var.get().strip()
            start = start_var.get().strip()
            end = end_var.get().strip()
            
            if not name or not start or not end:
                warning_lbl.configure(text="All fields are required.")
                return
            
            # Simple clock validation
            for clk in (start, end):
                try:
                    parts = clk.split(":")
                    if len(parts) != 2 or not (0 <= int(parts[0]) <= 23) or not (0 <= int(parts[1]) <= 59):
                        raise ValueError()
                except:
                    warning_lbl.configure(text="Times must be in HH:MM format.")
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
                warning_lbl.configure(text="A city with this name already exists.")

        ctk.CTkButton(main_frame, text="Save", command=save, width=140).grid(row=4, column=0, columnspan=2, pady=15)

    def delete_city(self):
        selected = self.cities_tree.selection()
        if not selected:
            messagebox.showwarning("Select City", "Please select one or more cities to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected)} selected city/cities?")
        if confirm:
            success = 0
            for item in selected:
                values = self.cities_tree.item(item, "values")
                city_id, name = int(values[0]), values[1]
                try:
                    models.delete_city(city_id)
                    self.write_log(f"[DB] Deleted city '{name}'")
                    success += 1
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", f"Cannot delete city '{name}'. There are timesheets referencing it.")
            if success > 0:
                self.refresh_all_views()

    # ==============================================================================
    # 2. Drivers Tab
    # ==============================================================================
    def setup_drivers_tab(self):
        drivers_frame = self.tabview.tab("Drivers")
        
        # Left Panel: Table
        tree_frame = ctk.CTkFrame(drivers_frame, corner_radius=12)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        ctk.CTkLabel(
            tree_frame, 
            text="Registered Delivery Drivers", 
            font=("Segoe UI", 15, "bold")
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        inner_tree_frame = ctk.CTkFrame(tree_frame, fg_color="transparent")
        inner_tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        cols = ("ID", "Name", "Personal ID")
        self.drivers_tree = ttk.Treeview(inner_tree_frame, columns=cols, show="headings", selectmode="extended")
        for col in cols:
            self.drivers_tree.heading(col, text=col)
        self.drivers_tree.column("ID", width=60, stretch=False)
        self.drivers_tree.column("Name", width=250)
        self.drivers_tree.column("Personal ID", width=180)
        
        scrollbar = ctk.CTkScrollbar(inner_tree_frame, command=self.drivers_tree.yview)
        self.drivers_tree.configure(yscrollcommand=scrollbar.set)
        
        self.drivers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right Panel: Actions
        btn_frame = ctk.CTkFrame(drivers_frame, width=220, corner_radius=12)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0), pady=10)
        
        ctk.CTkLabel(
            btn_frame, 
            text="Actions", 
            font=("Segoe UI", 15, "bold")
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="Add Driver...", 
            fg_color="#1a365d", 
            hover_color="#2b6cb0", 
            command=self.add_driver_dialog
        ).pack(fill=tk.X, padx=15, pady=8)
        
        ctk.CTkButton(
            btn_frame, 
            text="Edit Selected...", 
            command=self.edit_driver_dialog
        ).pack(fill=tk.X, padx=15, pady=8)
        
        ctk.CTkButton(
            btn_frame, 
            text="Delete Driver", 
            fg_color="#742a2a", 
            hover_color="#9b2c2c", 
            command=self.delete_driver
        ).pack(fill=tk.X, padx=15, pady=8)
        
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
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("380x240")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_frame, text="Driver Name:").grid(row=0, column=0, padx=10, pady=12, sticky=tk.W)
        name_var = tk.StringVar(value=values[1] if values else "")
        ctk.CTkEntry(main_frame, textvariable=name_var, width=180).grid(row=0, column=1, padx=10, pady=12)
        
        ctk.CTkLabel(main_frame, text="Personal ID:").grid(row=1, column=0, padx=10, pady=12, sticky=tk.W)
        id_var = tk.StringVar(value=values[2] if values else "")
        ctk.CTkEntry(main_frame, textvariable=id_var, width=180).grid(row=1, column=1, padx=10, pady=12)
        
        warning_lbl = ctk.CTkLabel(main_frame, text="", text_color="#e53e3e", font=("Segoe UI", 10))
        warning_lbl.grid(row=2, column=0, columnspan=2, pady=(0, 5))
        
        def save():
            name = name_var.get().strip()
            personal_id = id_var.get().strip()
            
            if not name or not personal_id:
                warning_lbl.configure(text="All fields are required.")
                return
            
            try:
                if values:  # Edit Mode
                    models.update_employee(int(values[0]), name, personal_id)
                    self.write_log(f"[DB] Updated employee {name} (ID: {personal_id})")
                else:  # Add Mode
                    models.add_employee(name, personal_id)
                    self.write_log(f"[DB] Added employee {name} (ID: {personal_id})")
                self.refresh_all_views()
                dialog.destroy()
            except sqlite3.IntegrityError:
                warning_lbl.configure(text="A driver with this Personal ID already exists.")

        ctk.CTkButton(main_frame, text="Save", command=save, width=140).grid(row=3, column=0, columnspan=2, pady=15)

    def delete_driver(self):
        selected = self.drivers_tree.selection()
        if not selected:
            messagebox.showwarning("Select Driver", "Please select one or more drivers to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected)} selected driver(s)?")
        if confirm:
            success = 0
            for item in selected:
                values = self.drivers_tree.item(item, "values")
                emp_id, name = int(values[0]), values[1]
                try:
                    models.delete_employee(emp_id)
                    self.write_log(f"[DB] Deleted driver '{name}'")
                    success += 1
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", f"Cannot delete driver '{name}'. There are timesheets referencing them.")
            if success > 0:
                self.refresh_all_views()

    # ==============================================================================
    # 3. Timesheets Tab & Solver Integration
    # ==============================================================================
    def setup_timesheets_tab(self):
        timesheets_frame = self.tabview.tab("Timesheets")
        
        # Grid weights to make side-by-side frames scale nicely
        timesheets_frame.columnconfigure(0, weight=4) # 40% width for left list
        timesheets_frame.columnconfigure(1, weight=5) # 60% width for right details
        timesheets_frame.rowconfigure(0, weight=1)
        
        # LEFT: List Panel Card
        self.left_panel = ctk.CTkFrame(timesheets_frame, corner_radius=12)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # Filters Header Bar
        filter_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        filter_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        ctk.CTkLabel(filter_frame, text="City:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_city_menu = ctk.CTkOptionMenu(
            filter_frame, 
            values=["All Cities"], 
            width=120,
            command=lambda val: self.load_timesheets()
        )
        self.filter_city_menu.pack(side=tk.LEFT, padx=(0, 10))
        
        ctk.CTkLabel(filter_frame, text="Month:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.filter_month_menu = ctk.CTkOptionMenu(
            filter_frame, 
            values=["All Months"], 
            width=110,
            command=lambda val: self.load_timesheets()
        )
        self.filter_month_menu.pack(side=tk.LEFT)
        
        # List Treeview Frame
        list_tree_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        list_tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        self.timesheets_tree = ttk.Treeview(
            list_tree_frame, 
            columns=("ID", "City", "Target Hours", "Status", "Locked"), 
            show="tree headings", 
            selectmode="extended"
        )
        self.timesheets_tree.heading("#0", text="Driver / Month")
        self.timesheets_tree.column("#0", width=180, stretch=True)
        self.timesheets_tree.heading("ID", text="ID")
        self.timesheets_tree.column("ID", width=40, stretch=False, anchor=tk.CENTER)
        self.timesheets_tree.heading("City", text="City")
        self.timesheets_tree.column("City", width=100, stretch=True)
        self.timesheets_tree.heading("Target Hours", text="Target Hours")
        self.timesheets_tree.column("Target Hours", width=90, stretch=False, anchor=tk.CENTER)
        self.timesheets_tree.heading("Status", text="Status")
        self.timesheets_tree.column("Status", width=80, stretch=False, anchor=tk.CENTER)
        self.timesheets_tree.heading("Locked", text="Locked")
        self.timesheets_tree.column("Locked", width=60, stretch=False, anchor=tk.CENTER)
        
        self.timesheets_tree.tag_configure("draft", foreground="#3182ce")
        self.timesheets_tree.tag_configure("finalized", foreground="#38a169")
        self.timesheets_tree.tag_configure("locked", foreground="#dd6b20")
        
        ts_scrollbar = ctk.CTkScrollbar(list_tree_frame, command=self.timesheets_tree.yview)
        self.timesheets_tree.configure(yscrollcommand=ts_scrollbar.set)
        self.timesheets_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.timesheets_tree.bind("<<TreeviewSelect>>", self.on_timesheet_select)
        
        # Left Actions Buttons Frame
        la_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        la_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        la_frame.columnconfigure(0, weight=1)
        la_frame.columnconfigure(1, weight=1)
        
        ctk.CTkButton(
            la_frame, 
            text="+ New Timesheet...", 
            fg_color="#1a365d", 
            hover_color="#2b6cb0",
            command=self.new_timesheet_dialog
        ).grid(row=0, column=0, padx=(0, 5), pady=(0, 5), sticky="ew")
        
        ctk.CTkButton(
            la_frame, 
            text="Delete Selected", 
            fg_color="#742a2a", 
            hover_color="#9b2c2c",
            command=self.delete_timesheet
        ).grid(row=0, column=1, padx=(5, 0), pady=(0, 5), sticky="ew")
        
        ctk.CTkButton(
            la_frame, 
            text="Distribute Selected", 
            fg_color="#3182ce", 
            hover_color="#2b6cb0",
            command=self.solve_selected_timesheets_batch
        ).grid(row=1, column=0, padx=(0, 5), pady=(5, 0), sticky="ew")
        
        ctk.CTkButton(
            la_frame, 
            text="Export Selected", 
            fg_color="#2c3e50", 
            hover_color="#34495e",
            command=lambda: self.export_timesheet()
        ).grid(row=1, column=1, padx=(5, 0), pady=(5, 0), sticky="ew")
        
        # RIGHT: Detail & Actions Panel Card
        self.right_panel = ctk.CTkFrame(timesheets_frame, corner_radius=12)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        
        # Placeholder view
        self.placeholder_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.placeholder_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            self.placeholder_frame, 
            text="No Timesheet Selected", 
            font=("Segoe UI", 16, "bold")
        ).pack(expand=True, pady=(120, 10))
        
        ctk.CTkLabel(
            self.placeholder_frame, 
            text="Select a timesheet from the list on the left to view daily shifts,\nrun shift distribution solvers, edit shifts manually, or export to Word.", 
            font=("Segoe UI", 11, "italic"),
            text_color="#718096"
        ).pack(expand=True, pady=(0, 120))
        
        # Details container (hidden by default)
        self.details_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        
        # Detail Header metadata label + Status Badge
        self.meta_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        self.meta_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        self.meta_lbl = ctk.CTkLabel(
            self.meta_frame, 
            text="No timesheet selected.", 
            font=("Segoe UI", 13, "bold")
        )
        self.meta_lbl.pack(side=tk.LEFT)
        
        self.status_badge = ctk.CTkLabel(
            self.meta_frame, 
            text="", 
            font=("Segoe UI", 11, "bold"), 
            corner_radius=6, 
            height=22
        )
        
        # Loading/Solving progress indicator
        self.progress_bar = ctk.CTkProgressBar(self.details_container, mode="indeterminate", height=6)
        
        # Daily Grid Frame
        grid_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        grid_cols = ("Date", "Start Time", "End Time", "Break", "Hours Worked", "Remarks")
        self.grid_tree = ttk.Treeview(grid_frame, columns=grid_cols, show="headings", selectmode="browse")
        for col in grid_cols:
            self.grid_tree.heading(col, text=col)
        self.grid_tree.column("Date", width=90, anchor=tk.CENTER)
        self.grid_tree.column("Start Time", width=80, anchor=tk.CENTER)
        self.grid_tree.column("End Time", width=80, anchor=tk.CENTER)
        self.grid_tree.column("Break", width=60, anchor=tk.CENTER)
        self.grid_tree.column("Hours Worked", width=100, anchor=tk.CENTER)
        self.grid_tree.column("Remarks", width=150)
        
        grid_scrollbar = ctk.CTkScrollbar(grid_frame, command=self.grid_tree.yview)
        self.grid_tree.configure(yscrollcommand=grid_scrollbar.set)
        self.grid_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.grid_tree.bind("<Double-1>", self.on_grid_double_click)
        
        # Detail Actions Frame
        self.da_frame = ctk.CTkFrame(self.details_container, fg_color="transparent")
        self.da_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        
        self.btn_single_solve = ctk.CTkButton(
            self.da_frame, 
            text="Distribute (Single)", 
            width=135,
            command=lambda: self.solve_single_timesheet()
        )
        self.btn_single_solve.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_batch_solve = ctk.CTkButton(
            self.da_frame, 
            text="Distribute All (City)", 
            width=140,
            command=lambda: self.solve_batch_timesheets()
        )
        self.btn_batch_solve.pack(side=tk.LEFT)
        
        self.btn_revert = ctk.CTkButton(
            self.da_frame, 
            text="Revert to Draft", 
            width=110,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=lambda: self.revert_timesheet()
        )
        self.btn_revert.pack(side=tk.RIGHT)
        
        self.btn_finalize = ctk.CTkButton(
            self.da_frame, 
            text="Finalize Schedule", 
            width=130,
            fg_color="#2f855a",
            hover_color="#22543d",
            command=lambda: self.finalize_timesheet()
        )
        self.btn_finalize.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.btn_export_word_detail = ctk.CTkButton(
            self.da_frame,
            text="Export Word",
            width=110,
            fg_color="#2c3e50",
            hover_color="#34495e",
            command=lambda: self.export_timesheet()
        )
        self.btn_export_word_detail.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Refresh combinations
        self.refresh_timesheet_combos()
        self.load_timesheets()

    def refresh_timesheet_combos(self):
        # 1. Cities
        cities = ["All Cities"] + [c["name"] for c in models.get_cities()]
        self.filter_city_menu.configure(values=cities)
        if self.filter_city_menu.get() not in cities:
            self.filter_city_menu.set("All Cities")
            
        # 2. Months
        months = ["All Months", "01.2026", "02.2026", "03.2026", "04.2026", "05.2026", "06.2026", "07.2026", "08.2026", "09.2026", "10.2026", "11.2026", "12.2026"]
        self.filter_month_menu.configure(values=months)
        if self.filter_month_menu.get() not in months:
            self.filter_month_menu.set("All Months")

    def load_timesheets(self):
        selected_city = self.filter_city_menu.get()
        selected_month_str = self.filter_month_menu.get()
        
        # Resolve IDs
        city_id = None
        if selected_city != "All Cities" and selected_city != "No cities":
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
                
        # Load sheets and group by driver
        self.timesheets_tree.delete(*self.timesheets_tree.get_children())
        
        from collections import defaultdict
        driver_timesheets = defaultdict(list)
        for ts in models.get_timesheets(city_id=city_id, year=year, month=month):
            driver_timesheets[(ts["employee_id"], ts["employee_name"], ts["personal_id"])].append(ts)
            
        for (emp_id, emp_name, personal_id), sheets in driver_timesheets.items():
            # Parent driver node
            parent_node = self.timesheets_tree.insert(
                "", tk.END, iid=f"driver_{emp_id}", 
                text=f"{emp_name} (ID: {personal_id})", 
                values=("", "", "", "", ""), 
                open=True
            )
            
            for ts in sheets:
                locked_str = "Yes" if ts["is_distribution_locked"] else "No"
                if ts["status"] == "Finalized":
                    tag = "finalized"
                elif ts["is_distribution_locked"]:
                    tag = "locked"
                else:
                    tag = "draft"
                    
                # Child timesheet row
                self.timesheets_tree.insert(
                    parent_node, tk.END, iid=f"ts_{ts['id']}",
                    text=f"  {ts['month']:02d}.{ts['year']}", 
                    values=(
                        ts["id"], ts["city_name"], ts["target_hours"], 
                        ts["status"], locked_str
                    ),
                    tags=(tag,)
                )
                
        # If there is a current selected timesheet, refresh its details and restore selection
        if hasattr(self, 'current_selected_ts_id') and self.current_selected_ts_id:
            node_id = f"ts_{self.current_selected_ts_id}"
            if self.timesheets_tree.exists(node_id):
                self.timesheets_tree.unbind("<<TreeviewSelect>>")
                self.timesheets_tree.selection_set(node_id)
                self.timesheets_tree.focus(node_id)
                self.timesheets_tree.see(node_id)
                self.timesheets_tree.bind("<<TreeviewSelect>>", self.on_timesheet_select)
            ts = models.get_timesheet_with_entries(self.current_selected_ts_id)
            if ts:
                self.show_details(self.current_selected_ts_id)
            else:
                self.show_placeholder()
        else:
            self.show_placeholder()

    def on_timesheet_select(self, event):
        selected = self.timesheets_tree.selection()
        if not selected:
            self.show_placeholder()
            return
            
        # Find if a child node (timesheet) is selected
        child_ts_id = None
        for item in selected:
            parent_id = self.timesheets_tree.parent(item)
            if parent_id != "": # it's a child row
                values = self.timesheets_tree.item(item, "values")
                if values and values[0]:
                    child_ts_id = int(values[0])
                    break
                    
        if child_ts_id:
            self.show_details(child_ts_id)
        else:
            self.show_placeholder()

    def get_selected_timesheet_ids(self) -> List[int]:
        selected_items = self.timesheets_tree.selection()
        ts_ids = []
        for item in selected_items:
            # Check if this is a parent (driver) or child (timesheet) row
            parent_id = self.timesheets_tree.parent(item)
            if parent_id == "": # It's a parent (driver) node
                # Add all children timesheets
                for child in self.timesheets_tree.get_children(item):
                    values = self.timesheets_tree.item(child, "values")
                    if values and values[0]:
                        ts_ids.append(int(values[0]))
            else: # It's a child node
                values = self.timesheets_tree.item(item, "values")
                if values and values[0]:
                    ts_ids.append(int(values[0]))
        return list(set(ts_ids))

    def solve_selected_timesheets_batch(self):
        ts_ids = self.get_selected_timesheet_ids()
        if not ts_ids:
            messagebox.showwarning("Select Timesheet", "Please select at least one timesheet to define the city and month context.")
            return
        self.solve_batch_timesheets(ts_ids[0])

    def show_placeholder(self):
        self.details_container.pack_forget()
        self.placeholder_frame.pack(fill=tk.BOTH, expand=True)
        self.current_selected_ts_id = None

    def show_details(self, ts_id: int):
        self.placeholder_frame.pack_forget()
        self.details_container.pack(fill=tk.BOTH, expand=True)
        self.current_selected_ts_id = ts_id
        
        ts = models.get_timesheet_with_entries(ts_id)
        if not ts:
            self.show_placeholder()
            return
            
        self.meta_lbl.configure(
            text=f"{ts['employee_name']} (ID: {ts['personal_id']}) - {ts['city_name']} ({ts['month']:02d}.{ts['year']}) | Target: {ts['target_hours']}h"
        )
        
        self.status_badge.pack_forget()
        is_dark = (ctk.get_appearance_mode() == "Dark")
        if ts["status"] == "Finalized":
            self.status_badge.configure(
                text=" FINALIZED ",
                fg_color="#1c4532" if is_dark else "#c6f6d5",
                text_color="#9ae6b4" if is_dark else "#22543d"
            )
        elif ts["is_distribution_locked"]:
            self.status_badge.configure(
                text=" LOCKED ",
                fg_color="#7b341e" if is_dark else "#feebc8",
                text_color="#fbd38d" if is_dark else "#744210"
            )
        else:
            self.status_badge.configure(
                text=" DRAFT ",
                fg_color="#1a365d" if is_dark else "#ebf8ff",
                text_color="#90cdf4" if is_dark else "#2b6cb0"
            )
        self.status_badge.pack(side=tk.LEFT, padx=10)
        
        if ts["status"] == "Finalized":
            self.btn_finalize.configure(state="disabled")
            self.btn_revert.configure(state="normal")
            self.btn_single_solve.configure(state="disabled")
            self.btn_batch_solve.configure(state="disabled")
        else:
            self.btn_finalize.configure(state="normal")
            self.btn_revert.configure(state="disabled")
            self.btn_single_solve.configure(state="normal")
            self.btn_batch_solve.configure(state="normal")
            
        self.grid_tree.delete(*self.grid_tree.get_children())
        for entry in ts["entries"]:
            work_date = entry["work_date"]
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

    def on_grid_double_click(self, event):
        if not hasattr(self, 'current_selected_ts_id') or not self.current_selected_ts_id:
            return
            
        ts = models.get_timesheet_with_entries(self.current_selected_ts_id)
        if ts.get("status") == "Finalized":
            messagebox.showwarning("Edit Blocked", "Finalized timesheets cannot be modified. Revert to Draft first.")
            return

        selected_grid_idx = self.grid_tree.selection()
        if not selected_grid_idx:
            return
        grid_values = self.grid_tree.item(selected_grid_idx[0], "values")
        
        date_str = grid_values[0]
        start_time = grid_values[1]
        end_time = grid_values[2]
        break_dur = grid_values[3]
        hours_str = grid_values[4]
        remarks = grid_values[5]
        
        self.manual_edit_dialog(ts, date_str, start_time, end_time, break_dur, hours_str, remarks)

    # ==============================================================================
    # Timesheet Creation Dialog
    # ==============================================================================
    def new_timesheet_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Generate Timesheets")
        dialog.geometry("540x620")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        drivers = models.get_employees()
        cities = models.get_cities()
        
        if not drivers or not cities:
            messagebox.showerror("Error", "You must add at least one driver and one city first.")
            dialog.destroy()
            return
            
        # Top Header
        header_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 5))
        ctk.CTkLabel(header_frame, text="Generate Timesheets in Batch", font=("Segoe UI", 16, "bold")).pack(anchor=tk.W)
        
        # Scrollable container for the form inputs
        scroll_container = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=5)
        
        # Grid frame inside scroll container
        form_frame = ctk.CTkFrame(scroll_container, fg_color="transparent")
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Select Driver(s):\n(Check to set hours)", font=("Segoe UI", 11, "bold"), justify=tk.LEFT).grid(row=0, column=0, padx=10, pady=10, sticky=tk.NW)
        
        # Scrollable list of driver checkboxes and target hour entry fields
        drivers_scroll = ctk.CTkScrollableFrame(form_frame, width=280, height=130)
        drivers_scroll.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        
        self.driver_entries = []
        for d in drivers:
            row_frame = ctk.CTkFrame(drivers_scroll, fg_color="transparent")
            row_frame.pack(fill=tk.X, pady=2)
            
            cb = ctk.CTkCheckBox(row_frame, text=f"{d['name']} (ID: {d['personal_id']})", width=200)
            cb.pack(side=tk.LEFT, padx=5)
            
            # Entry for target hours
            entry = ctk.CTkEntry(row_frame, width=50)
            entry.insert(0, "80.0")
            entry.pack(side=tk.RIGHT, padx=5)
            
            # Helper to enable/disable entry based on checkbox
            def make_toggle_callback(c_box=cb, e_box=entry):
                return lambda: e_box.configure(state="normal" if c_box.get() == 1 else "disabled")
            
            cb.configure(command=make_toggle_callback(cb, entry))
            entry.configure(state="disabled") # default disabled since checkbox is unchecked
            
            self.driver_entries.append((d["id"], d["name"], d["personal_id"], cb, entry))
            
        # Select All / Deselect All helpers
        helper_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        helper_frame.grid(row=1, column=1, padx=10, pady=(0, 10), sticky=tk.W)
        
        def select_all():
            for _, _, _, cb, entry in self.driver_entries:
                cb.select()
                entry.configure(state="normal")
                
        def deselect_all():
            for _, _, _, cb, entry in self.driver_entries:
                cb.deselect()
                entry.configure(state="disabled")
                
        ctk.CTkButton(helper_frame, text="Select All", width=80, height=22, fg_color="#3182ce", text_color="white", hover_color="#2b6cb0", command=select_all).pack(side=tk.LEFT, padx=(0, 10))
        ctk.CTkButton(helper_frame, text="Deselect All", width=90, height=22, fg_color="#4a5568", text_color="white", hover_color="#2d3748", command=deselect_all).pack(side=tk.LEFT)
        
        # Month Selector Checklist (next 12 months)
        ctk.CTkLabel(form_frame, text="Select Month(s):", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky=tk.NW)
        
        months_scroll = ctk.CTkScrollableFrame(form_frame, width=280, height=110)
        months_scroll.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        
        now_dt = datetime.now()
        months_list = []
        for i in range(12):
            m = (now_dt.month - 1 + i) % 12 + 1
            y = now_dt.year + (now_dt.month - 1 + i) // 12
            months_list.append(f"{m:02d}.{y}")
            
        self.month_checkboxes = []
        for m_str in months_list:
            cb = ctk.CTkCheckBox(months_scroll, text=m_str)
            # Default check the current month
            if m_str == now_dt.strftime("%m.%Y"):
                cb.select()
            cb.pack(anchor=tk.W, padx=5, pady=3)
            self.month_checkboxes.append((m_str, cb))
        
        ctk.CTkLabel(form_frame, text="Select City:", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        city_names = [c["name"] for c in cities]
        city_menu = ctk.CTkOptionMenu(form_frame, values=city_names, width=280)
        city_menu.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Bottom controls - Fixed outside scrollbox so it's always visible!
        bottom_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(10, 20))
        
        warning_lbl = ctk.CTkLabel(bottom_frame, text="", text_color="#e53e3e", font=("Segoe UI", 11))
        warning_lbl.pack(pady=(0, 10))
        
        def create():
            selected_drivers = []
            for emp_id, name, personal_id, cb, entry in self.driver_entries:
                if cb.get() == 1:
                    target_str = entry.get().strip()
                    if not target_str:
                        warning_lbl.configure(text=f"Please specify target hours for {name}.")
                        return
                    try:
                        target_hours = float(target_str.replace(",", "."))
                        if target_hours % 0.5 != 0:
                            raise ValueError()
                    except:
                        warning_lbl.configure(text=f"Hours for {name} must be a number and multiple of 0.5.")
                        return
                    selected_drivers.append((emp_id, name, target_hours))
            
            if not selected_drivers:
                warning_lbl.configure(text="Please select at least one driver.")
                return
                
            selected_months = []
            for m_str, cb in self.month_checkboxes:
                if cb.get() == 1:
                    selected_months.append(m_str)
                    
            if not selected_months:
                warning_lbl.configure(text="Please select at least one month.")
                return
                
            c_name = city_menu.get()
            if not c_name:
                warning_lbl.configure(text="Please select a city.")
                return
                
            city_id = next(c["id"] for c in cities if c["name"] == c_name)
            
            # Batch validation of limits per month
            for m_year in selected_months:
                try:
                    parts = m_year.split('.')
                    month, year = int(parts[0]), int(parts[1])
                except:
                    continue
                    
                _, num_days = calendar.monthrange(year, month)
                max_wd = (num_days // 7) * 6 + min(num_days % 7, 6)
                max_hours_allowed = max_wd * 8.0
                
                for emp_id, d_name, target_hours in selected_drivers:
                    if target_hours < 10.0 or target_hours > max_hours_allowed:
                        warning_lbl.configure(
                            text=f"Hours {target_hours} for {d_name} out of bounds for {m_year} [10.0, {max_hours_allowed}]."
                        )
                        return
                        
            # Execute database insertions
            success_count = 0
            fail_count = 0
            for m_year in selected_months:
                parts = m_year.split('.')
                month, year = int(parts[0]), int(parts[1])
                
                for emp_id, d_name, target_hours in selected_drivers:
                    try:
                        models.create_timesheet(emp_id, city_id, year, month, target_hours)
                        self.write_log(f"[DB] Created timesheet for {d_name} in {c_name} ({m_year}) with {target_hours}h")
                        success_count += 1
                    except sqlite3.IntegrityError:
                        self.write_log(f"[DB] Timesheet already exists for {d_name} in {c_name} ({m_year})")
                        fail_count += 1
                        
            self.load_timesheets()
            
            if fail_count > 0:
                messagebox.showinfo(
                    "Creation Summary", 
                    f"Generated {success_count} timesheets successfully.\n"
                    f"Skipped {fail_count} timesheets because they already exist."
                )
            else:
                self.write_log(f"[System] Successfully generated {success_count} timesheets.")
                
            dialog.destroy()
                
        ctk.CTkButton(bottom_frame, text="Generate Timesheets", command=create, width=180, height=35, font=("Segoe UI", 12, "bold")).pack()

    def delete_timesheet(self):
        ts_ids = self.get_selected_timesheet_ids()
        if not ts_ids:
            messagebox.showwarning("Select Timesheet", "Please select one or more timesheets to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(ts_ids)} selected timesheet(s)?")
        if confirm:
            for ts_id in ts_ids:
                models.delete_timesheet(ts_id)
                self.write_log(f"[DB] Deleted timesheet ID {ts_id}")
            if hasattr(self, 'current_selected_ts_id') and self.current_selected_ts_id in ts_ids:
                self.current_selected_ts_id = None
            self.load_timesheets()

    def finalize_timesheet(self, ts_ids: Optional[List[int]] = None):
        if ts_ids is None:
            ts_ids = self.get_selected_timesheet_ids()
        if not ts_ids:
            messagebox.showwarning("Select Timesheet", "Please select one or more timesheets to finalize.")
            return
        for ts_id in ts_ids:
            models.update_timesheet_status(ts_id, "Finalized")
            self.write_log(f"[DB] Finalized timesheet ID {ts_id}")
        self.load_timesheets()

    def revert_timesheet(self, ts_ids: Optional[List[int]] = None):
        if ts_ids is None:
            ts_ids = self.get_selected_timesheet_ids()
        if not ts_ids:
            messagebox.showwarning("Select Timesheet", "Please select one or more timesheets to revert.")
            return
        for ts_id in ts_ids:
            models.update_timesheet_status(ts_id, "Draft")
            self.write_log(f"[DB] Reverted timesheet ID {ts_id} to Draft")
        self.load_timesheets()

    def export_timesheet(self, ts_ids: Optional[List[int]] = None):
        if ts_ids is None:
            ts_ids = self.get_selected_timesheet_ids()
        if not ts_ids:
            messagebox.showwarning("Select Timesheet", "Please select one or more timesheets to export.")
            return
        
        if len(ts_ids) == 1:
            ts_id = ts_ids[0]
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
        else:
            dest_dir = filedialog.askdirectory(title="Select Directory to Save Exported Timesheets")
            if dest_dir:
                success_count = 0
                fail_count = 0
                for ts_id in ts_ids:
                    ts = models.get_timesheet_with_entries(ts_id)
                    if not ts:
                        continue
                    clean_name = "".join(c for c in ts["employee_name"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                    file_name = f"timesheet_{clean_name}_{ts['month']:02d}_{ts['year']}.docx"
                    dest_path = os.path.join(dest_dir, file_name)
                    try:
                        docx_exporter.generate_docx(
                            employee_name=ts["employee_name"],
                            personal_id=ts["personal_id"],
                            city_name=ts["city_name"],
                            year=ts["year"],
                            month=ts["month"],
                            daily_entries=ts["entries"],
                            target_hours=ts["target_hours"],
                            output_path=dest_path
                        )
                        success_count += 1
                    except Exception as e:
                        self.write_log(f"[Error] Failed to export timesheet ID {ts_id}: {e}")
                        fail_count += 1
                
                msg = f"Successfully exported {success_count} timesheet(s) to:\n{dest_dir}"
                if fail_count > 0:
                    msg += f"\nFailed to export {fail_count} timesheet(s)."
                messagebox.showinfo("Export Summary", msg)

    # ==============================================================================
    # Solver execution helper
    # ==============================================================================
    def run_solver_background(self, solver_input: sat_solver.SolverInput, callback_success, ts_id: int):
        """Runs the CP-SAT solver in a background thread and updates the UI progress indicators."""
        self.write_log(f"[Solver] Starting CP-SAT calculations ({solver_input.mode} mode)...")
        
        prog_bar = getattr(self, 'progress_bar', None)
        meta_lbl = getattr(self, 'meta_lbl', None)
        status_badge = getattr(self, 'status_badge', None)
        buttons = [
            getattr(self, 'btn_single_solve', None),
            getattr(self, 'btn_batch_solve', None),
            getattr(self, 'btn_finalize', None),
            getattr(self, 'btn_revert', None),
            getattr(self, 'btn_export_word_detail', None)
        ]
        
        if prog_bar:
            prog_bar.pack(fill=tk.X, pady=(0, 10), after=self.meta_frame)
            prog_bar.start()
        if meta_lbl:
            meta_lbl.configure(text="CP-SAT Solver calculating optimal shift distribution... please wait.")
        if status_badge:
            status_badge.pack_forget()
            
        for btn in buttons:
            if btn:
                btn.configure(state="disabled")
                
        def run():
            try:
                result = sat_solver.solve(solver_input)
                self.root.after(0, lambda: handle_done(result))
            except Exception as e:
                self.write_log(f"[Error] Solver runtime exception: {e}")
                self.root.after(0, lambda: handle_error(e))
                
        def handle_done(result):
            if prog_bar:
                prog_bar.stop()
                prog_bar.pack_forget()
            callback_success(result)
            
        def handle_error(e):
            if prog_bar:
                prog_bar.stop()
                prog_bar.pack_forget()
            messagebox.showerror("Solver Error", f"Solver encountered an exception:\n{e}")
            self.load_timesheets()
                
        threading.Thread(target=run, daemon=True).start()

    # ==============================================================================
    # 3.1 Single Driver Solver (Incremental Mode)
    # ==============================================================================
    def solve_single_timesheet(self, ts_id: Optional[int] = None):
        if ts_id is None:
            ts_ids = self.get_selected_timesheet_ids()
            if not ts_ids:
                return
            ts_id = ts_ids[0]
            
        ts = models.get_timesheet_with_entries(ts_id)
        if not ts:
            return
            
        # Overwrite confirmation
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
                self.load_timesheets()
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
                    self.load_timesheets()
                    return
            
            # Save results
            schedule = result.schedules[ts["employee_id"]]
            db_entries = []
            for entry in schedule:
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
            
        self.run_solver_background(solver_input, on_success, ts_id)

    # ==============================================================================
    # 3.2 Batch Solver (City Batch Mode)
    # ==============================================================================
    def solve_batch_timesheets(self, ts_id: Optional[int] = None):
        if ts_id is None:
            ts_ids = self.get_selected_timesheet_ids()
            if not ts_ids:
                messagebox.showwarning("Batch solve", "Please select a timesheet to define the city and month context.")
                return
            ts_id = ts_ids[0]
            
        selected_ts = models.get_timesheet_with_entries(ts_id)
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
                self.write_log(f"[DB] Saved distributed entries for timesheet ID {ts['id']}")
                
            self.load_timesheets()
                
        self.run_solver_background(solver_input, on_success, ts_id)

    # ==============================================================================
    # 4. Post-Solver Manual Edit Workflow
    # ==============================================================================

    def manual_edit_dialog(self, ts: dict, date_str: str, start: str, end: str, break_dur: str, hours_str: str, remarks_str: str):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Edit Shift - {date_str}")
        dialog.geometry("400x320")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_frame, text="Start Time (HH:MM):").grid(row=0, column=0, padx=10, pady=6, sticky=tk.W)
        start_var = tk.StringVar(value=start)
        ctk.CTkEntry(main_frame, textvariable=start_var, width=180).grid(row=0, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(main_frame, text="End Time (HH:MM):").grid(row=1, column=0, padx=10, pady=6, sticky=tk.W)
        end_var = tk.StringVar(value=end)
        ctk.CTkEntry(main_frame, textvariable=end_var, width=180).grid(row=1, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(main_frame, text="Break (HH:MM):").grid(row=2, column=0, padx=10, pady=6, sticky=tk.W)
        break_var = tk.StringVar(value=break_dur if break_dur else "00:00")
        ctk.CTkEntry(main_frame, textvariable=break_var, width=180).grid(row=2, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(main_frame, text="Hours Worked:").grid(row=3, column=0, padx=10, pady=6, sticky=tk.W)
        hours_var = tk.StringVar(value=hours_str.replace(",", "."))
        ctk.CTkEntry(main_frame, textvariable=hours_var, width=180).grid(row=3, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(main_frame, text="Remarks:").grid(row=4, column=0, padx=10, pady=6, sticky=tk.W)
        remarks_var = tk.StringVar(value=remarks_str)
        ctk.CTkEntry(main_frame, textvariable=remarks_var, width=180).grid(row=4, column=1, padx=10, pady=6)
        
        warning_lbl = ctk.CTkLabel(main_frame, text="", text_color="#e53e3e", font=("Segoe UI", 10))
        warning_lbl.grid(row=5, column=0, columnspan=2, pady=(5, 5))
        
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
                warning_lbl.configure(text="Hours worked must be a valid positive number.")
                return
                
            # If hours > 0, times must be HH:MM
            if hours_val > 0.0:
                for clk in (st, et, br):
                    try:
                        parts = clk.split(":")
                        if len(parts) != 2 or not (0 <= int(parts[0]) <= 23) or not (0 <= int(parts[1]) <= 59):
                            raise ValueError()
                    except:
                        warning_lbl.configure(text="Times must be in HH:MM format.")
                        return
            else:
                st = ""
                et = ""
                br = ""
                
            # Update local dict first for validation checks
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            iso_date = dt.strftime("%Y-%m-%d")
            
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
            # Lock vs Redistribute Dialog
            # ---------------------------------------------------------
            prompt_dialog = ctk.CTkToplevel(self.root)
            prompt_dialog.title("Save Action")
            prompt_dialog.geometry("400x180")
            prompt_dialog.resizable(False, False)
            prompt_dialog.transient(dialog)
            prompt_dialog.grab_set()
            
            ctk.CTkLabel(
                prompt_dialog,
                text="How would you like to save these edits?",
                font=("Segoe UI", 12, "bold")
            ).pack(pady=(15, 10))
            
            ctk.CTkLabel(
                prompt_dialog,
                text="Lock only edits this driver. Redistribute recalculates other schedules.",
                font=("Segoe UI", 10, "italic"),
                text_color="#a0aec0" if ctk.get_appearance_mode() == "Dark" else "#718096"
            ).pack(pady=(0, 15))
            
            def lock_only():
                models.save_daily_entries(ts["id"], new_entries)
                models.set_distribution_lock(ts["id"], True)
                self.write_log(f"[DB] Saved edits and locked timesheet ID {ts['id']}")
                self.load_timesheets()
                prompt_dialog.destroy()
                dialog.destroy()
                
            def apply_all():
                models.save_daily_entries(ts["id"], new_entries)
                self.write_log(f"[DB] Saved edits for timesheet ID {ts['id']}. Triggering redistribution...")
                prompt_dialog.destroy()
                dialog.destroy()
                
                # Re-run batch solver treating this driver as fixed constraint
                self.solve_batch_timesheets_with_fixed_driver(ts, new_entries)
                
            btn_frame = ctk.CTkFrame(prompt_dialog, fg_color="transparent")
            btn_frame.pack(pady=5)
            
            ctk.CTkButton(
                btn_frame, 
                text="Lock Driver Only", 
                fg_color="#4a5568", 
                hover_color="#2d3748",
                command=lock_only
            ).pack(side=tk.LEFT, padx=10)
            
            ctk.CTkButton(
                btn_frame, 
                text="Apply & Redistribute", 
                fg_color="#2b6cb0", 
                hover_color="#1f538d",
                command=apply_all
            ).pack(side=tk.LEFT, padx=10)
            
            ctk.CTkButton(
                btn_frame, 
                text="Cancel", 
                fg_color="transparent", 
                text_color="#e53e3e", 
                hover_color="#fed7d7" if ctk.get_appearance_mode() == "Light" else "#742a2a",
                command=prompt_dialog.destroy
            ).pack(side=tk.LEFT, padx=10)

        ctk.CTkButton(main_frame, text="Save", command=save, width=140).grid(row=6, column=0, columnspan=2, pady=15)

    def solve_batch_timesheets_with_fixed_driver(self, edited_ts: dict, edited_entries: list):
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
                self.write_log(f"[DB] Saved distributed entries for timesheet ID {ts['id']}")
                
            self.load_timesheets()
            
        self.run_solver_background(solver_input, on_success, edited_ts["id"])
