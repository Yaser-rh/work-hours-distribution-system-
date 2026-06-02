import calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import db.models as models
import solver.sat_solver as sat_solver

class AnalyticsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        
        # Grid layout: 1 row, 2 columns for the two analytics sections
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        # ----------------------------------------------------------------------
        # Left Panel: Driver Analytics
        # ----------------------------------------------------------------------
        self.driver_frame = ttk.LabelFrame(self, text=" Driver Monthly Hours ", padding=10)
        self.driver_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        driver_controls = ttk.Frame(self.driver_frame)
        driver_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(driver_controls, text="Select Driver:").pack(side=tk.LEFT, padx=5)
        self.driver_combo = ttk.Combobox(driver_controls, state="readonly", width=25)
        self.driver_combo.pack(side=tk.LEFT, padx=5)
        self.driver_combo.bind("<<ComboboxSelected>>", lambda e: self.update_driver_chart())
        
        # Canvas for Driver Chart
        self.driver_fig = Figure(figsize=(5, 4), dpi=100)
        self.driver_ax = self.driver_fig.add_subplot(111)
        self.driver_canvas = FigureCanvasTkAgg(self.driver_fig, master=self.driver_frame)
        self.driver_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # ----------------------------------------------------------------------
        # Right Panel: City Coverage Heatmap
        # ----------------------------------------------------------------------
        self.city_frame = ttk.LabelFrame(self, text=" City Hourly Coverage Heatmap ", padding=10)
        self.city_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        city_controls = ttk.Frame(self.city_frame)
        city_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(city_controls, text="City:").pack(side=tk.LEFT, padx=2)
        self.city_combo = ttk.Combobox(city_controls, state="readonly", width=12)
        self.city_combo.pack(side=tk.LEFT, padx=5)
        self.city_combo.bind("<<ComboboxSelected>>", lambda e: self.update_city_heatmap())
        
        ttk.Label(city_controls, text="Month:").pack(side=tk.LEFT, padx=2)
        self.month_combo = ttk.Combobox(city_controls, state="readonly", width=10)
        self.month_combo.pack(side=tk.LEFT, padx=5)
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.update_city_heatmap())
        
        # Canvas for Heatmap Chart
        self.city_fig = Figure(figsize=(5, 4), dpi=100)
        self.city_ax = self.city_fig.add_subplot(111)
        self.city_canvas = FigureCanvasTkAgg(self.city_fig, master=self.city_frame)
        self.city_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.refresh_selectors()

    def refresh_selectors(self):
        # 1. Driver selector
        drivers = models.get_employees()
        driver_names = [d["name"] for d in drivers]
        self.driver_combo["values"] = driver_names
        if driver_names and not self.driver_combo.get():
            self.driver_combo.set(driver_names[0])
            
        # 2. City Selector
        cities = models.get_cities()
        city_names = [c["name"] for c in cities]
        self.city_combo["values"] = city_names
        if city_names and not self.city_combo.get():
            self.city_combo.set(city_names[0])
            
        # 3. Month Selector
        months = ["01.2026", "02.2026", "03.2026", "04.2026", "05.2026", "06.2026", "07.2026", "08.2026", "09.2026", "10.2026", "11.2026", "12.2026"]
        self.month_combo["values"] = months
        if not self.month_combo.get():
            self.month_combo.set("06.2026")
            
        self.update_driver_chart()
        self.update_city_heatmap()

    def update_driver_chart(self):
        self.driver_ax.clear()
        driver_name = self.driver_combo.get()
        if not driver_name:
            self.driver_ax.text(0.5, 0.5, "Please add/select a driver", ha='center', va='center')
            self.driver_canvas.draw()
            return
            
        # Fetch driver ID
        drivers = models.get_employees()
        driver_id = None
        for d in drivers:
            if d["name"] == driver_name:
                driver_id = d["id"]
                break
                
        if driver_id is None:
            self.driver_canvas.draw()
            return
            
        # Get all timesheets for this driver
        timesheets = models.get_timesheets(employee_id=driver_id)
        if not timesheets:
            self.driver_ax.text(0.5, 0.5, "No timesheet data available", ha='center', va='center')
            self.driver_fig.tight_layout()
            self.driver_canvas.draw()
            return
            
        # Sort chronologically by year, month
        timesheets = sorted(timesheets, key=lambda t: (t["year"], t["month"]))
        
        labels = []
        actual_hours = []
        target_hours = []
        
        for ts in timesheets:
            labels.append(f"{ts['month']:02d}/{ts['year']}")
            target_hours.append(ts["target_hours"])
            
            # Fetch actual hours from entries
            ts_detail = models.get_timesheet_with_entries(ts["id"])
            total_actual = sum(e["hours_worked"] for e in ts_detail.get("entries", []))
            actual_hours.append(total_actual)
            
        # Plotting
        x = range(len(labels))
        width = 0.35
        
        self.driver_ax.bar([i - width/2 for i in x], target_hours, width, label='Target Hours', color='#90cdf4')
        self.driver_ax.bar([i + width/2 for i in x], actual_hours, width, label='Actual Worked', color='#2b6cb0')
        
        self.driver_ax.set_ylabel('Hours')
        self.driver_ax.set_title(f'Monthly Hours Summary - {driver_name}')
        self.driver_ax.set_xticks(x)
        self.driver_ax.set_xticklabels(labels, rotation=15)
        self.driver_ax.legend()
        self.driver_ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        
        self.driver_fig.tight_layout()
        self.driver_canvas.draw()

    def update_city_heatmap(self):
        self.city_ax.clear()
        city_name = self.city_combo.get()
        month_str = self.month_combo.get()
        
        if not city_name or not month_str:
            self.city_ax.text(0.5, 0.5, "Please select city & month", ha='center', va='center')
            self.city_canvas.draw()
            return
            
        # Fetch city details
        cities = models.get_cities()
        city_id = None
        city_start_time = "08:00"
        city_end_time = "22:00"
        for c in cities:
            if c["name"] == city_name:
                city_id = c["id"]
                city_start_time = c["start_time"]
                city_end_time = c["end_time"]
                break
                
        if city_id is None:
            self.city_canvas.draw()
            return
            
        try:
            parts = month_str.split('.')
            month, year = int(parts[0]), int(parts[1])
        except:
            self.city_ax.text(0.5, 0.5, "Invalid month format", ha='center', va='center')
            self.city_canvas.draw()
            return
            
        # Get city coverage map {day: {slot: count}}
        coverage = models.get_city_coverage(city_id, year, month)
        _, num_days = calendar.monthrange(year, month)
        
        # Convert start/end times to slots
        c_start = sat_solver.clock_to_units(city_start_time)
        c_end = sat_solver.clock_to_units(city_end_time)
        
        # Operational slots range
        slots_range = list(range(c_start, c_end))
        if not slots_range:
            self.city_ax.text(0.5, 0.5, "Invalid city operational window", ha='center', va='center')
            self.city_canvas.draw()
            return
            
        # Build 2D matrix (rows = days, cols = operational slots)
        matrix = []
        for d in range(1, num_days + 1):
            day_cov = coverage.get(d, {})
            day_row = [day_cov.get(slot, 0) for slot in slots_range]
            matrix.append(day_row)
            
        # Render Heatmap
        # x-axis labels: clock times
        # Y-axis labels: days (1 to num_days)
        im = self.city_ax.imshow(matrix, cmap="YlGnBu", aspect="auto", interpolation="nearest")
        
        # Configure X-axis ticks (e.g. show ticks every 4 slots / 2 hours)
        x_ticks = []
        x_labels = []
        for idx, slot in enumerate(slots_range):
            if slot % 4 == 0:
                x_ticks.append(idx)
                x_labels.append(sat_solver.units_to_clock(slot))
                
        self.city_ax.set_xticks(x_ticks)
        self.city_ax.set_xticklabels(x_labels)
        self.city_ax.set_xlabel("Time of Day")
        
        self.city_ax.set_yticks(range(0, num_days, 5))
        self.city_ax.set_yticklabels(range(1, num_days + 1, 5))
        self.city_ax.set_ylabel("Day of Month")
        
        self.city_ax.set_title(f"Driver Shift Coverage Profile - {city_name} ({month_str})")
        
        # Clear colorbar if it exists, or just recreate
        # To avoid multiple colorbars, we remove previous colorbar if exists
        if hasattr(self, 'colorbar'):
            try:
                self.colorbar.remove()
            except:
                pass
        self.colorbar = self.city_fig.colorbar(im, ax=self.city_ax, fraction=0.046, pad=0.04)
        self.colorbar.set_label("Number of Drivers Active")
        
        self.city_fig.tight_layout()
        self.city_canvas.draw()
