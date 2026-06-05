import calendar
from datetime import datetime
import tkinter as tk
import customtkinter as ctk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import db.models as models
import solver.sat_solver as sat_solver

class AnalyticsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        # Initialize as a transparent CTkFrame to blend with parent notebook
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        # Grid layout: 1 row, 2 columns for the two analytics sections
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        # ----------------------------------------------------------------------
        # Left Panel: Driver Analytics
        # ----------------------------------------------------------------------
        self.driver_frame = ctk.CTkFrame(self, corner_radius=12)
        self.driver_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)
        
        self.driver_title = ctk.CTkLabel(self.driver_frame, text="Driver Monthly Hours", font=("Segoe UI", 15, "bold"))
        self.driver_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        driver_controls = ctk.CTkFrame(self.driver_frame, fg_color="transparent")
        driver_controls.pack(fill=tk.X, padx=15, pady=5)
        
        ctk.CTkLabel(driver_controls, text="Select Driver:").pack(side=tk.LEFT, padx=(0, 5))
        self.driver_menu = ctk.CTkOptionMenu(
            driver_controls, 
            values=["No drivers"], 
            width=160,
            command=lambda val: self.update_driver_chart()
        )
        self.driver_menu.pack(side=tk.LEFT, padx=5)
        
        # Canvas for Driver Chart
        self.driver_fig = Figure(figsize=(5, 4), dpi=100)
        self.driver_ax = self.driver_fig.add_subplot(111)
        self.driver_canvas = FigureCanvasTkAgg(self.driver_fig, master=self.driver_frame)
        self.driver_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        
        # ----------------------------------------------------------------------
        # Right Panel: City Coverage Heatmap
        # ----------------------------------------------------------------------
        self.city_frame = ctk.CTkFrame(self, corner_radius=12)
        self.city_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)
        
        self.city_title = ctk.CTkLabel(self.city_frame, text="City Hourly Coverage Heatmap", font=("Segoe UI", 15, "bold"))
        self.city_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        city_controls = ctk.CTkFrame(self.city_frame, fg_color="transparent")
        city_controls.pack(fill=tk.X, padx=15, pady=5)
        
        ctk.CTkLabel(city_controls, text="City:").pack(side=tk.LEFT, padx=2)
        self.city_menu = ctk.CTkOptionMenu(
            city_controls, 
            values=["No cities"], 
            width=120,
            command=lambda val: self.update_city_heatmap()
        )
        self.city_menu.pack(side=tk.LEFT, padx=5)
        
        ctk.CTkLabel(city_controls, text="Month:").pack(side=tk.LEFT, padx=(10, 2))
        self.month_menu = ctk.CTkOptionMenu(
            city_controls, 
            values=[], 
            width=110,
            command=lambda val: self.update_city_heatmap()
        )
        self.month_menu.pack(side=tk.LEFT, padx=5)
        
        # Canvas for Heatmap Chart
        self.city_fig = Figure(figsize=(5, 4), dpi=100)
        self.city_ax = self.city_fig.add_subplot(111)
        self.city_canvas = FigureCanvasTkAgg(self.city_fig, master=self.city_frame)
        self.city_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        self.refresh_selectors()

    def style_chart(self, fig, ax):
        """Helper to style the matplotlib figure colors to fit Light or Dark theme."""
        is_dark = (ctk.get_appearance_mode() == "Dark")
        
        # Select background and foreground colors matching CTk themes
        bg_color = "#2b2b2b" if is_dark else "#dbdbdb"
        inner_bg = "#1e1e1e" if is_dark else "#f5f5f5"
        text_color = "#ffffff" if is_dark else "#000000"
        grid_color = "#444444" if is_dark else "#cccccc"
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(inner_bg)
        
        # Color the spines (axes borders)
        for spine in ax.spines.values():
            spine.set_color(grid_color)
            
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        ax.tick_params(colors=text_color, which='both')
        
        # Style the legend if it exists
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(bg_color)
            legend.get_frame().set_edgecolor(grid_color)
            for text in legend.get_texts():
                text.set_color(text_color)

    def refresh_selectors(self):
        # 1. Driver selector
        drivers = models.get_employees()
        driver_names = [d["name"] for d in drivers] if drivers else ["No drivers"]
        self.driver_menu.configure(values=driver_names)
        if driver_names:
            current = self.driver_menu.get()
            if current not in driver_names:
                self.driver_menu.set(driver_names[0])
            
        # 2. City Selector
        cities = models.get_cities()
        city_names = [c["name"] for c in cities] if cities else ["No cities"]
        self.city_menu.configure(values=city_names)
        if city_names:
            current = self.city_menu.get()
            if current not in city_names:
                self.city_menu.set(city_names[0])
            
        # 3. Month Selector
        months = ["01.2026", "02.2026", "03.2026", "04.2026", "05.2026", "06.2026", "07.2026", "08.2026", "09.2026", "10.2026", "11.2026", "12.2026"]
        self.month_menu.configure(values=months)
        if not self.month_menu.get():
            self.month_menu.set("06.2026")
            
        self.update_driver_chart()
        self.update_city_heatmap()

    def update_driver_chart(self):
        self.driver_ax.clear()
        driver_name = self.driver_menu.get()
        if not driver_name or driver_name == "No drivers":
            self.driver_ax.text(0.5, 0.5, "Please add/select a driver", ha='center', va='center')
            self.style_chart(self.driver_fig, self.driver_ax)
            self.driver_fig.tight_layout()
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
            self.driver_ax.text(0.5, 0.5, "Driver not found", ha='center', va='center')
            self.style_chart(self.driver_fig, self.driver_ax)
            self.driver_fig.tight_layout()
            self.driver_canvas.draw()
            return
            
        # Get all timesheets for this driver
        timesheets = models.get_timesheets(employee_id=driver_id)
        if not timesheets:
            self.driver_ax.text(0.5, 0.5, "No timesheet data available", ha='center', va='center')
            self.style_chart(self.driver_fig, self.driver_ax)
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
        
        is_dark = (ctk.get_appearance_mode() == "Dark")
        target_color = '#1f77b4' if is_dark else '#3182ce'
        actual_color = '#2ca02c' if is_dark else '#38a169'
        
        self.driver_ax.bar([i - width/2 for i in x], target_hours, width, label='Target Hours', color=target_color)
        self.driver_ax.bar([i + width/2 for i in x], actual_hours, width, label='Actual Worked', color=actual_color)
        
        self.driver_ax.set_ylabel('Hours')
        self.driver_ax.set_title(f'Monthly Hours Summary - {driver_name}')
        self.driver_ax.set_xticks(x)
        self.driver_ax.set_xticklabels(labels, rotation=15)
        self.driver_ax.legend()
        self.driver_ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        
        self.style_chart(self.driver_fig, self.driver_ax)
        self.driver_fig.tight_layout()
        self.driver_canvas.draw()

    def update_city_heatmap(self):
        self.city_ax.clear()
        city_name = self.city_menu.get()
        month_str = self.month_menu.get()
        
        if not city_name or city_name == "No cities" or not month_str:
            self.city_ax.text(0.5, 0.5, "Please select city & month", ha='center', va='center')
            self.style_chart(self.city_fig, self.city_ax)
            self.city_fig.tight_layout()
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
            self.city_ax.text(0.5, 0.5, "City not found", ha='center', va='center')
            self.style_chart(self.city_fig, self.city_ax)
            self.city_fig.tight_layout()
            self.city_canvas.draw()
            return
            
        try:
            parts = month_str.split('.')
            month, year = int(parts[0]), int(parts[1])
        except:
            self.city_ax.text(0.5, 0.5, "Invalid month format", ha='center', va='center')
            self.style_chart(self.city_fig, self.city_ax)
            self.city_fig.tight_layout()
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
            self.style_chart(self.city_fig, self.city_ax)
            self.city_fig.tight_layout()
            self.city_canvas.draw()
            return
            
        # Build 2D matrix (rows = days, cols = operational slots)
        matrix = []
        for d in range(1, num_days + 1):
            day_cov = coverage.get(d, {})
            day_row = [day_cov.get(slot, 0) for slot in slots_range]
            matrix.append(day_row)
            
        # Render Heatmap
        is_dark = (ctk.get_appearance_mode() == "Dark")
        cmap = "viridis" if is_dark else "YlGnBu"
        im = self.city_ax.imshow(matrix, cmap=cmap, aspect="auto", interpolation="nearest")
        
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
        
        self.style_chart(self.city_fig, self.city_ax)
        
        # Style colorbar
        if hasattr(self, 'colorbar'):
            try:
                self.colorbar.remove()
            except:
                pass
        
        fg_color = "#ffffff" if is_dark else "#000000"
        self.colorbar = self.city_fig.colorbar(im, ax=self.city_ax, fraction=0.046, pad=0.04)
        self.colorbar.set_label("Number of Drivers Active", color=fg_color)
        self.colorbar.ax.yaxis.set_tick_params(color=fg_color)
        for label in self.colorbar.ax.get_yticklabels():
            label.set_color(fg_color)
            
        self.city_fig.tight_layout()
        self.city_canvas.draw()
