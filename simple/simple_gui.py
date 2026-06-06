import os
import calendar
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import customtkinter as ctk

from simple.simple_solver import (
    greedy_solve,
    units_to_clock,
    clock_to_units,
    units_to_hours,
    hours_to_units
)
from exporter.docx_exporter import generate_docx

class SimpleAppGUI:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Timesheet Generator - Simple Mode")
        self.root.geometry("1000x680")
        self.root.minsize(900, 600)
        
        # Style object for ttk widgets (Treeview)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Solver output storage
        self.solve_results = None
        
        # Configure layout grids
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Setup UI
        self.setup_ui()
        self.update_treeview_styles()
        
        # Apply current appearance mode
        self.theme_switch.select() if ctk.get_appearance_mode() == "Dark" else self.theme_switch.deselect()

    def setup_ui(self):
        # Main Container
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # --- Top Header ---
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 5))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Timesheet Distribution - Simple Mode",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        title_label.pack(side=tk.LEFT)
        
        self.theme_switch = ctk.CTkSwitch(
            header_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.theme_switch.pack(side=tk.RIGHT, padx=10)
        
        # --- Split Body Layout ---
        body_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 15))
        body_frame.columnconfigure(0, weight=4) # Left Form panel (40%)
        body_frame.columnconfigure(1, weight=6) # Right Preview panel (60%)
        body_frame.rowconfigure(0, weight=1)
        
        # ==========================================
        # LEFT PANEL: Input Form
        # ==========================================
        self.form_panel = ctk.CTkFrame(body_frame, corner_radius=12)
        self.form_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        form_title = ctk.CTkLabel(
            self.form_panel,
            text="Driver & Shift Parameters",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        )
        form_title.pack(anchor=tk.W, padx=20, pady=(15, 15))
        
        # Form scrollable frame to avoid overflow if window resized small
        form_scroll = ctk.CTkScrollableFrame(self.form_panel, fg_color="transparent")
        form_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 15))
        
        # 1. Driver Name
        self.lbl_name = ctk.CTkLabel(form_scroll, text="Employee Name:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.lbl_name.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.ent_name = ctk.CTkEntry(form_scroll, placeholder_text="e.g. Max Mustermann", height=32)
        self.ent_name.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 2. Personal ID
        self.lbl_id = ctk.CTkLabel(form_scroll, text="Personal ID / Number:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.lbl_id.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.ent_id = ctk.CTkEntry(form_scroll, placeholder_text="e.g. M12345", height=32)
        self.ent_id.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 3. City Name
        self.lbl_city = ctk.CTkLabel(form_scroll, text="City / Location Name:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.lbl_city.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.ent_city = ctk.CTkEntry(form_scroll, placeholder_text="e.g. Berlin", height=32)
        self.ent_city.insert(0, "Berlin")
        self.ent_city.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Time Grid Row for Opening and Closing Hours
        time_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        time_frame.pack(fill=tk.X, padx=0, pady=0)
        time_frame.columnconfigure(0, weight=1)
        time_frame.columnconfigure(1, weight=1)
        
        # Generate 30-min slots list
        time_slots = []
        for h in range(24):
            time_slots.append(f"{h:02d}:00")
            time_slots.append(f"{h:02d}:30")
            
        # 4. Opening Time
        lbl_opening = ctk.CTkLabel(time_frame, text="Opening Time:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        lbl_opening.grid(row=0, column=0, sticky=tk.W, padx=10, pady=(5, 2))
        self.cmb_opening = ctk.CTkComboBox(time_frame, values=time_slots, height=32)
        self.cmb_opening.set("08:00")
        self.cmb_opening.grid(row=1, column=0, sticky="ew", padx=(10, 5), pady=(0, 10))
        
        # 5. Closing Time
        lbl_closing = ctk.CTkLabel(time_frame, text="Closing Time:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        lbl_closing.grid(row=0, column=1, sticky=tk.W, padx=5, pady=(5, 2))
        self.cmb_closing = ctk.CTkComboBox(time_frame, values=time_slots, height=32)
        self.cmb_closing.set("22:00")
        self.cmb_closing.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=(0, 10))
        
        # Date Grid Row for Month and Year
        date_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        date_frame.pack(fill=tk.X, padx=0, pady=0)
        date_frame.columnconfigure(0, weight=1)
        date_frame.columnconfigure(1, weight=1)
        
        # 6. Month Selector
        lbl_month = ctk.CTkLabel(date_frame, text="Target Month:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        lbl_month.grid(row=0, column=0, sticky=tk.W, padx=10, pady=(5, 2))
        
        months_list = [
            "01 - January", "02 - February", "03 - March", "04 - April",
            "05 - May", "06 - June", "07 - July", "08 - August",
            "09 - September", "10 - October", "11 - November", "12 - December"
        ]
        self.cmb_month = ctk.CTkComboBox(date_frame, values=months_list, height=32)
        # Default to current month
        current_month_idx = datetime.now().month - 1
        self.cmb_month.set(months_list[current_month_idx])
        self.cmb_month.grid(row=1, column=0, sticky="ew", padx=(10, 5), pady=(0, 10))
        
        # 7. Year Selector
        lbl_year = ctk.CTkLabel(date_frame, text="Target Year:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        lbl_year.grid(row=0, column=1, sticky=tk.W, padx=5, pady=(5, 2))
        
        current_year = datetime.now().year
        years_list = [str(y) for y in range(current_year - 1, current_year + 3)]
        self.cmb_year = ctk.CTkComboBox(date_frame, values=years_list, height=32)
        self.cmb_year.set(str(current_year))
        self.cmb_year.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=(0, 10))
        
        # 8. Target Hours
        self.lbl_hours = ctk.CTkLabel(form_scroll, text="Target Hours:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.lbl_hours.pack(anchor=tk.W, padx=10, pady=(5, 2))
        self.ent_hours = ctk.CTkEntry(form_scroll, placeholder_text="e.g. 120", height=32)
        self.ent_hours.insert(0, "120")
        self.ent_hours.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        # 8.5 Start Time Options
        self.lbl_start_times = ctk.CTkLabel(form_scroll, text="Allowed Start Times:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
        self.lbl_start_times.pack(anchor=tk.W, padx=10, pady=(5, 2))
        
        checkbox_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        checkbox_frame.pack(fill=tk.X, padx=10, pady=(0, 15))
        
        self.chk_morning = ctk.CTkCheckBox(checkbox_frame, text="Morning (e.g. 08:00)", font=ctk.CTkFont(family="Segoe UI", size=11))
        self.chk_morning.pack(anchor=tk.W, pady=3)
        self.chk_morning.select()
        
        self.chk_afternoon = ctk.CTkCheckBox(checkbox_frame, text="Afternoon (e.g. 12:00)", font=ctk.CTkFont(family="Segoe UI", size=11))
        self.chk_afternoon.pack(anchor=tk.W, pady=3)
        self.chk_afternoon.select()
        
        self.chk_evening = ctk.CTkCheckBox(checkbox_frame, text="Evening (e.g. 16:00)", font=ctk.CTkFont(family="Segoe UI", size=11))
        self.chk_evening.pack(anchor=tk.W, pady=3)
        self.chk_evening.select()
        
        # 9. Solve Button
        self.btn_solve = ctk.CTkButton(
            form_scroll,
            text="⚡ Generate Shift Schedule",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#1a365d",
            hover_color="#2b6cb0",
            height=40,
            command=self.run_generation
        )
        self.btn_solve.pack(fill=tk.X, padx=10, pady=10)

        # ==========================================
        # RIGHT PANEL: Preview Table & Export
        # ==========================================
        self.preview_panel = ctk.CTkFrame(body_frame, corner_radius=12)
        self.preview_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        
        # Right Heading Frame
        self.preview_header = ctk.CTkFrame(self.preview_panel, fg_color="transparent")
        self.preview_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        self.preview_title = ctk.CTkLabel(
            self.preview_header,
            text="Schedule Preview",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        )
        self.preview_title.pack(side=tk.LEFT)
        
        self.status_lbl = ctk.CTkLabel(
            self.preview_header,
            text="Ready to generate",
            text_color="#718096",
            font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic")
        )
        self.status_lbl.pack(side=tk.RIGHT)
        
        # --- KPI Summary Bar ---
        self.kpi_container = ctk.CTkFrame(self.preview_panel, fg_color="transparent", height=70)
        self.kpi_container.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.kpi_container.columnconfigure((0, 1, 2, 3), weight=1)
        
        self.kpis = {}
        kpi_defs = [
            ("target", "Target Hours", "0.0h"),
            ("scheduled", "Scheduled Hours", "0.0h"),
            ("days", "Work Days", "0"),
            ("deviation", "Deviation", "0.0h")
        ]
        
        for idx, (key, label, val) in enumerate(kpi_defs):
            card = ctk.CTkFrame(self.kpi_container, corner_radius=8, border_width=1, border_color="#e2e8f0")
            card.grid(row=0, column=idx, padx=5, sticky="nsew")
            
            lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(family="Segoe UI", size=10), text_color="#718096")
            lbl.pack(pady=(6, 2))
            
            val_lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
            val_lbl.pack(pady=(0, 6))
            
            self.kpis[key] = (card, val_lbl)
            
        # --- Table Preview Window ---
        self.table_frame = ctk.CTkFrame(self.preview_panel, fg_color="transparent")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        cols = ("Date", "Start Time", "End Time", "Break", "Hours Worked", "Remarks")
        self.tree = ttk.Treeview(self.table_frame, columns=cols, show="headings", selectmode="none")
        
        for col in cols:
            self.tree.heading(col, text=col)
            
        self.tree.column("Date", width=100, anchor=tk.CENTER)
        self.tree.column("Start Time", width=90, anchor=tk.CENTER)
        self.tree.column("End Time", width=90, anchor=tk.CENTER)
        self.tree.column("Break", width=80, anchor=tk.CENTER)
        self.tree.column("Hours Worked", width=100, anchor=tk.CENTER)
        self.tree.column("Remarks", width=120)
        
        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Bottom Panel (Export Button) ---
        self.export_frame = ctk.CTkFrame(self.preview_panel, fg_color="transparent")
        self.export_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.btn_export = ctk.CTkButton(
            self.export_frame,
            text="💾 Export to Word (.docx)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#0f766e",
            hover_color="#0d9488",
            height=40,
            state=tk.DISABLED,
            command=self.run_export
        )
        self.btn_export.pack(fill=tk.X)

    def toggle_theme(self):
        """Toggles the light/dark appearance mode and updates Treeview styling."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
        self.update_treeview_styles()

    def update_treeview_styles(self):
        """Styles the TTK Treeview widget to match CustomTkinter theme."""
        is_dark = (ctk.get_appearance_mode() == "Dark")
        
        # Configure colors
        bg = "#2b2b2b" if is_dark else "#ffffff"
        fg = "#ffffff" if is_dark else "#000000"
        field_bg = "#2b2b2b" if is_dark else "#ffffff"
        selected_bg = "#1f538d" if is_dark else "#3a7ebf"
        heading_bg = "#212121" if is_dark else "#eaeaea"
        heading_fg = "#ffffff" if is_dark else "#000000"
        border_color = "#3d3d3d" if is_dark else "#cbd5e1"
        
        self.style.configure(
            "Treeview", 
            background=bg, 
            foreground=fg, 
            fieldbackground=field_bg, 
            rowheight=26,
            font=("Segoe UI", 10),
            borderwidth=0,
            relief="flat"
        )
        self.style.configure(
            "Treeview.Heading", 
            background=heading_bg, 
            foreground=heading_fg, 
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="flat"
        )
        self.style.map("Treeview", background=[("selected", selected_bg)])
        
        # Update KPI borders
        for key, (card, _) in self.kpis.items():
            card.configure(border_color=border_color)

    def format_hours_german(self, hours: float) -> str:
        """Formats hours with a German decimal comma (e.g. 6.5 -> 6,5)."""
        if hours == 0.0 or hours == 0:
            return ""
        if hours.is_integer():
            return str(int(hours))
        return f"{hours:.1f}".replace(".", ",")

    def run_generation(self):
        # Validate Inputs
        name = self.ent_name.get().strip()
        personal_id = self.ent_id.get().strip()
        city = self.ent_city.get().strip()
        target_hours_str = self.ent_hours.get().strip()
        
        if not name:
            messagebox.showwarning("Validation Error", "Please enter the employee's name.")
            return
        if not personal_id:
            messagebox.showwarning("Validation Error", "Please enter the employee's personal ID.")
            return
        if not city:
            messagebox.showwarning("Validation Error", "Please enter the city name.")
            return
            
        try:
            target_hours = float(target_hours_str)
            if target_hours <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Validation Error", "Target Hours must be a positive number.")
            return
            
        opening_time = self.cmb_opening.get()
        closing_time = self.cmb_closing.get()
        
        # Date parsing
        month_str = self.cmb_month.get().split(" - ")[0]
        month = int(month_str)
        year = int(self.cmb_year.get())
        
        # Checkbox validation & state
        allow_morning = self.chk_morning.get() == 1
        allow_afternoon = self.chk_afternoon.get() == 1
        allow_evening = self.chk_evening.get() == 1
        
        if not (allow_morning or allow_afternoon or allow_evening):
            messagebox.showwarning("Validation Warning", "At least one start time option must be selected. Reverting to Morning Starts.")
            self.chk_morning.select()
            allow_morning = True
            
        self.status_lbl.configure(text="Generating schedule...", text_color="#3182ce")
        self.btn_solve.configure(state=tk.DISABLED)
        
        # Execute solve
        try:
            results = greedy_solve(
                target_hours=target_hours,
                city_start_str=opening_time,
                city_end_str=closing_time,
                year=year,
                month=month,
                allow_morning=allow_morning,
                allow_afternoon=allow_afternoon,
                allow_evening=allow_evening
            )
            
            self.solve_results = results
            self.populate_preview(results, target_hours)
            self.btn_export.configure(state=tk.NORMAL)
            self.status_lbl.configure(text="Schedule generated successfully!", text_color="#38a169")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate schedule:\n{e}")
            self.status_lbl.configure(text="Generation failed", text_color="#e53e3e")
            self.btn_export.configure(state=tk.DISABLED)
            
        finally:
            self.btn_solve.configure(state=tk.NORMAL)

    def populate_preview(self, results: dict, target_hours: float):
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        
        # Format and insert entries
        for entry in results["daily_entries"]:
            date_str = entry["work_date"]
            # Convert ISO to German date format
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            german_date = dt.strftime("%d.%m.%Y")
            
            hours_val = entry["hours_worked"]
            hours_str = self.format_hours_german(hours_val)
            
            # Put together row data
            row_data = (
                german_date,
                entry["start_time"] if hours_val > 0 else "",
                entry["end_time"] if hours_val > 0 else "",
                entry["break_duration"] if hours_val > 0 else "",
                hours_str,
                entry["remarks"]
            )
            
            self.tree.insert("", tk.END, values=row_data)
        
        # Update KPI values
        scheduled = results["scheduled_hours"]
        deviation = results["deviation"]
        work_days = results["work_days_count"]
        
        self.kpis["target"][1].configure(text=f"{target_hours:.1f}h")
        self.kpis["scheduled"][1].configure(text=f"{scheduled:.1f}h")
        self.kpis["days"][1].configure(text=str(work_days))
        
        # Color deviation KPI based on status
        dev_text = f"{deviation:+.1f}h" if deviation != 0 else "0.0h"
        self.kpis["deviation"][1].configure(text=dev_text)
        
        if deviation == 0.0:
            self.kpis["deviation"][1].configure(text_color="#38a169") # green
        elif abs(deviation) <= 2.0:
            self.kpis["deviation"][1].configure(text_color="#d69e2e") # orange/yellow
        else:
            self.kpis["deviation"][1].configure(text_color="#e53e3e") # red

    def run_export(self):
        if not self.solve_results:
            return
            
        name = self.ent_name.get().strip()
        personal_id = self.ent_id.get().strip()
        city = self.ent_city.get().strip()
        target_hours_str = self.ent_hours.get().strip()
        target_hours = float(target_hours_str)
        
        month_str = self.cmb_month.get().split(" - ")[0]
        month = int(month_str)
        year = int(self.cmb_year.get())
        
        # Build clean output filename suggestion
        clean_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        default_file = f"timesheet_{clean_name}_{month:02d}_{year}.docx"
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
            initialfile=default_file,
            title="Save Timesheet"
        )
        
        if not output_path:
            return # Cancelled
            
        self.status_lbl.configure(text="Exporting to Word...", text_color="#3182ce")
        self.btn_export.configure(state=tk.DISABLED)
        
        try:
            # Generate docx using docx_exporter (it's fast and synchronous)
            generate_docx(
                employee_name=name,
                personal_id=personal_id,
                city_name=city,
                year=year,
                month=month,
                daily_entries=self.solve_results["daily_entries"],
                target_hours=target_hours,
                output_path=output_path
            )
            
            messagebox.showinfo("Export Success", f"Word document successfully exported to:\n{output_path}")
            self.status_lbl.configure(text="Export complete!", text_color="#38a169")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Word document:\n{e}")
            self.status_lbl.configure(text="Export failed", text_color="#e53e3e")
            
        finally:
            self.btn_export.configure(state=tk.NORMAL)
