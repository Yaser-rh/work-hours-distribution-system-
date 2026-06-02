import os
import sys
import math
import random
import calendar
import argparse
import threading
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL

# Tkinter standard-library GUI imports
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

# ==============================================================================
# OPTIMIZED HOUR DISTRIBUTION SOLVER (VBA V6 Translation)
# ==============================================================================

# Hour definition arrays
GROUP1 = [2.0, 3.0, 4.0, 5.0, 6.0]
GROUP2 = [3.1, 3.2, 3.5, 4.1, 4.2, 4.5, 5.1, 5.2, 5.5]
GROUP3 = [2.1, 2.2, 2.5, 6.1, 6.2, 6.5]
ALL_HOURS = sorted(list(set(GROUP1 + GROUP2 + GROUP3)))

def check_6_day_rule(hours_list, check_index):
    """
    Checks if setting the day at check_index as an active workday
    would violate the rule of working at most 6 consecutive days.
    """
    consecutive = 0
    num_days = len(hours_list)
    
    # Count backward from check_index - 1
    for i in range(check_index - 1, -1, -1):
        if hours_list[i] > 0.0:
            consecutive += 1
        else:
            break
            
    # Count forward from check_index + 1
    for i in range(check_index + 1, num_days):
        if hours_list[i] > 0.0:
            consecutive += 1
        else:
            break
            
    return (consecutive + 1) <= 6

def process_single_month(num_days, target_hours):
    """
    Tries to distribute the target hours over a month of num_days
    using a randomized weighted assignment followed by an adjustment loop.
    Returns a list of daily hours if successful, otherwise None.
    """
    day_hours = [0.0] * num_days
    is_potential = [False] * num_days
    potential_indices = []
    
    # Pass 1: Identify Potential Workdays (6/7 probability, max 6 consecutive days)
    consecutive_potential = 0
    for i in range(num_days):
        is_forced_off = consecutive_potential >= 6
        if not is_forced_off:
            if random.random() < (6.0 / 7.0):
                is_potential[i] = True
                potential_indices.append(i)
                consecutive_potential += 1
            else:
                is_potential[i] = False
                consecutive_potential = 0
        else:
            is_potential[i] = False
            consecutive_potential = 0
            
    if not potential_indices:
        if abs(target_hours) < 0.01:
            return day_hours
        return None
        
    # Shuffle potential days to naturally distribute off-days
    random.shuffle(potential_indices)
    
    # Pass 2: Weighted Initial Assignment
    current_total = 0.0
    for idx in potential_indices:
        r = random.random()
        if r < 0.50:
            val = random.choice(GROUP1)
        elif r < 0.80:
            val = random.choice(GROUP2)
        else:
            val = random.choice(GROUP3)
        day_hours[idx] = val
        current_total += val
        
    # Pass 3: Fine-Tuning Adjustment Loop
    delta = round(target_hours - current_total, 1)
    
    MAX_ADJUSTMENT_ATTEMPTS = 500
    for adj_attempt in range(1, MAX_ADJUSTMENT_ATTEMPTS + 1):
        if abs(delta) < 0.01:
            break
            
        adj_made = False
        
        if delta > 0:  # Need to ADD hours
            # Strategy 1: Add exact delta to an OFF day
            delta_val = None
            for h in ALL_HOURS:
                if abs(h - delta) < 0.01:
                    delta_val = h
                    break
                    
            if delta_val is not None:
                for k in range(num_days):
                    if day_hours[k] == 0.0:
                        if check_6_day_rule(day_hours, k):
                            day_hours[k] = delta_val
                            current_total += delta_val
                            delta = round(target_hours - current_total, 1)
                            adj_made = True
                            break
                            
            # Strategy 2: Swap existing hours for LARGER allowed hours
            if not adj_made:
                assigned_indices = [i for i in range(num_days) if day_hours[i] > 0.0]
                if assigned_indices:
                    swap_day_idx = random.choice(assigned_indices)
                    h_old = day_hours[swap_day_idx]
                    
                    # Try Group 1 (Integers) first for ergonomic shift patterns
                    for h_new in GROUP1:
                        if h_new > h_old and round(h_new - h_old, 1) <= delta + 0.01:
                            day_hours[swap_day_idx] = h_new
                            current_total += (h_new - h_old)
                            delta = round(target_hours - current_total, 1)
                            adj_made = True
                            break
                            
                    # Fallback to ALL_HOURS
                    if not adj_made:
                        for h_new in ALL_HOURS:
                            if h_new > h_old and round(h_new - h_old, 1) <= delta + 0.01:
                                day_hours[swap_day_idx] = h_new
                                current_total += (h_new - h_old)
                                delta = round(target_hours - current_total, 1)
                                adj_made = True
                                break
                                
        elif delta < 0:  # Need to SUBTRACT hours
            assigned_indices = [i for i in range(num_days) if day_hours[i] > 0.0]
            if assigned_indices:
                swap_day_idx = random.choice(assigned_indices)
                h_old = day_hours[swap_day_idx]
                abs_delta = abs(delta)
                
                # Option 1: Turn off (Swap to 0)
                if round(h_old, 1) <= abs_delta + 0.01:
                    day_hours[swap_day_idx] = 0.0
                    current_total -= h_old
                    delta = round(target_hours - current_total, 1)
                    adj_made = True
                    
                # Option 2: Swap to smaller allowed value
                if not adj_made:
                    # Try Group 1 (Integers) first (descending)
                    for h_new in reversed(GROUP1):
                        if h_new < h_old and round(h_old - h_new, 1) <= abs_delta + 0.01:
                            day_hours[swap_day_idx] = h_new
                            current_total += (h_new - h_old)
                            delta = round(target_hours - current_total, 1)
                            adj_made = True
                            break
                            
                    # Fallback to ALL_HOURS (descending)
                    if not adj_made:
                        for h_new in reversed(ALL_HOURS):
                            if h_new < h_old and round(h_old - h_new, 1) <= abs_delta + 0.01:
                                day_hours[swap_day_idx] = h_new
                                current_total += (h_new - h_old)
                                delta = round(target_hours - current_total, 1)
                                adj_made = True
                                break
                                
        # Exit adjustment loop early if stuck
        if not adj_made and adj_attempt > (MAX_ADJUSTMENT_ATTEMPTS // 2):
            break
            
    if abs(delta) < 0.01:
        return day_hours
    return None

def distribute_monthly_hours(num_days, target_hours, verbose=False, log_callback=None):
    """
    Main driver for the hours distribution. Pre-checks feasibility
    and calls the month solver repeatedly with a retry budget.
    """
    if target_hours == 0.0:
        return [0.0] * num_days
        
    # Pre-check feasibility boundary
    max_workdays = num_days - (num_days // 7)
    max_possible_hours = round(max_workdays * 6.5, 1)
    min_possible_hours = 2.0
    
    if target_hours < min_possible_hours or target_hours > max_possible_hours:
        msg = (
            f"Target of {target_hours} hours in a {num_days}-day month is mathematically impossible.\n"
            f"- Under the 6-consecutive-day rule, the maximum workdays is {max_workdays}.\n"
            f"- Maximum possible hours: {max_possible_hours} hrs (at 6.5 hrs max shift).\n"
            f"- Minimum single shift: {min_possible_hours} hrs."
        )
        if log_callback:
            log_callback(f"[Error] {msg}\n")
        raise ValueError(msg)
        
    MAX_OVERALL_ATTEMPTS = 100
    for attempt in range(1, MAX_OVERALL_ATTEMPTS + 1):
        msg = f"[Solver] Attempt {attempt}/{MAX_OVERALL_ATTEMPTS}..."
        if log_callback:
            log_callback(msg + "\n")
        elif verbose:
            print(f"  {msg}", end="\r")
            
        result = process_single_month(num_days, target_hours)
        if result is not None:
            msg_succ = f"[Success] Attempt {attempt}/{MAX_OVERALL_ATTEMPTS}... Success!"
            if log_callback:
                log_callback(msg_succ + "\n")
            elif verbose:
                print(f"  {msg_succ}  ")
            return result
            
    msg_fail = f"Failed to satisfy exact target of {target_hours} hours after {MAX_OVERALL_ATTEMPTS} attempts."
    if log_callback:
        log_callback(f"[Error] {msg_fail}\n")
    raise RuntimeError(msg_fail)

# ==============================================================================
# HELPER FORMATTING FUNCTIONS
# ==============================================================================

def format_hours_german(hours):
    """
    Formats hours with German decimal comma (e.g. 6.0 -> 6, 4.5 -> 4,5).
    If hours is 0, returns an empty string.
    """
    if hours == 0.0 or hours == 0:
        return ""
    if hours.is_integer():
        return str(int(hours))
    return f"{hours:.1f}".replace(".", ",")

def parse_month_year(month_year_str):
    """
    Parses common month-year formats and returns (year, month).
    """
    formats = ["%m.%Y", "%Y-%m", "%B %Y", "%b %Y", "%m/%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(month_year_str.strip(), fmt)
            return dt.year, dt.month
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse '{month_year_str}'. "
        "Please use standard formats like 'MM.YYYY' (e.g. '02.2026') or 'Month YYYY' (e.g. 'February 2026')."
    )

# ==============================================================================
# WORD DOCUMENT GENERATION
# ==============================================================================

def generate_docx_timesheet(name, personal_id, year, month, distributed_hours, city="Istanbul", output_path=None):
    """
    Constructs the Word document timesheet using layout and styles from gg.py.
    """
    if output_path is None:
        clean_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        output_path = f"timesheet_{clean_name}_{month:02d}_{year}.docx"
        
    doc = Document()
    
    # 1. Page Setup (Margins: 0.8 inches all around)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # 2. Configure Base Styles (Calibri 11pt)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # 3. Add Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(18)
    title_run = title_p.add_run("Tätigkeitsnachweis")
    title_run.font.size = Pt(22)
    title_run.font.bold = True
    
    # 4. Add Metadata Block
    metadata = [
        ("Name Mitarbeiter /-in:", name),
        ("Personal Nummer:", personal_id),
        ("Stadt:", city)
    ]
    for label, val in metadata:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        
        label_run = p.add_run(f"{label} ")
        label_run.bold = True
        
        value_run = p.add_run(val)
        value_run.underline = True
        
    # Spacing before table
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(12)
    
    # 5. Create Daily Table
    headers = ["Datum", "Arbeitsbeginn", "Arbeitsende", "Pause", "Arbeitszeit", "Sonstiges"]
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    
    # Header styling
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.bold = True
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
    col_widths = [Inches(1.2), Inches(1.1), Inches(1.1), Inches(0.9), Inches(1.1), Inches(1.5)]
    
    # Populate daily rows
    num_days = len(distributed_hours)
    total_hours_sum = sum(distributed_hours)
    
    for day in range(1, num_days + 1):
        row_cells = table.add_row().cells
        date_obj = datetime(year, month, day)
        date_str = date_obj.strftime("%d.%m.%Y")
        
        hours_val = distributed_hours[day - 1]
        hours_str = format_hours_german(hours_val)
        
        # Check if the day is a Saturday or Sunday to mark as "Wochenende" in Sonstiges
        is_weekend = date_obj.weekday() >= 5
        
        # Populate columns (Arbeitsbeginn, Arbeitsende, Pause are empty placeholders)
        row_data = [date_str, "", "", "", hours_str, ""]
        if is_weekend and hours_val == 0.0:
            row_data[5] = "Wochenende"
            
        for i, text in enumerate(row_data):
            row_cells[i].text = text
            p = row_cells[i].paragraphs[0]
            if i < 5:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            row_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
    # Set explicit column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            
    # 6. Total Summary Block
    summary_p = doc.add_paragraph()
    summary_p.paragraph_format.space_before = Pt(16)
    summary_p.paragraph_format.space_after = Pt(40)
    
    summary_run_label = summary_p.add_run("Summe der Arbeitsstunden im Monat: ")
    summary_run_label.bold = True
    
    total_hours_formatted = f"{total_hours_sum:.1f}".replace(".", ",")
    summary_run_val = summary_p.add_run(f"{total_hours_formatted} Stunden")
    summary_run_val.underline = True
    
    # 7. Footer Sign-off Section
    footer_p = doc.add_paragraph()
    footer_p.paragraph_format.space_before = Pt(24)
    footer_p.add_run("Datum: ______________________")
    footer_p.add_run("\t\t\t\t")
    footer_p.add_run("Unterschrift: ______________________")
    
    caption_p = doc.add_paragraph()
    caption_p.paragraph_format.space_before = Pt(2)
    caption_run = caption_p.add_run("Datum, Unterschrift")
    caption_run.font.size = Pt(9)
    caption_run.font.italic = True
    
    doc.save(output_path)
    return os.path.abspath(output_path)

# ==============================================================================
# DESKTOP GRAPHICAL USER INTERFACE (Tkinter TTK)
# ==============================================================================

class TimesheetAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Timesheet Generator System - V6")
        self.root.geometry("580x680")
        self.root.minsize(520, 620)
        
        # Configure overall layout frames using TTK theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Define clean, professional color palettes
        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TLabel", foreground="#333333")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1a365d")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 9, "italic"), foreground="#666666")
        self.style.configure("Generate.TButton", font=("Segoe UI", 11, "bold"), background="#1a365d", foreground="white", padding=6)
        self.style.map("Generate.TButton", background=[("active", "#2b6cb0")])
        self.style.configure("Browse.TButton", font=("Segoe UI", 9), padding=2)
        
        # Main Container with generous padding
        main_container = ttk.Frame(root, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header Label
        header_lbl = ttk.Label(main_container, text="Timesheet Document Generator", style="Header.TLabel")
        header_lbl.pack(pady=(0, 2))
        
        subtitle_lbl = ttk.Label(
            main_container, 
            text="Distributes monthly target hours and exports styled Word templates", 
            style="Sub.TLabel"
        )
        subtitle_lbl.pack(pady=(0, 15))
        
        # Section 1: Employee Information
        emp_lf = ttk.LabelFrame(main_container, text=" Employee Details ", padding=12)
        emp_lf.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(emp_lf, text="Name Mitarbeiter /-in:").grid(row=0, column=0, sticky=tk.W, pady=4, padx=5)
        self.name_var = tk.StringVar(value="Max Mustermann")
        self.name_entry = ttk.Entry(emp_lf, textvariable=self.name_var, width=32)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=4, padx=5)
        
        ttk.Label(emp_lf, text="Personal Nummer:").grid(row=1, column=0, sticky=tk.W, pady=4, padx=5)
        self.id_var = tk.StringVar(value="12345678")
        self.id_entry = ttk.Entry(emp_lf, textvariable=self.id_var, width=32)
        self.id_entry.grid(row=1, column=1, sticky=tk.W, pady=4, padx=5)
        
        ttk.Label(emp_lf, text="Stadt:").grid(row=2, column=0, sticky=tk.W, pady=4, padx=5)
        self.city_var = tk.StringVar(value="Istanbul")
        self.city_entry = ttk.Entry(emp_lf, textvariable=self.city_var, width=32)
        self.city_entry.grid(row=2, column=1, sticky=tk.W, pady=4, padx=5)
        
        # Section 2: Timesheet Constraints
        settings_lf = ttk.LabelFrame(main_container, text=" Timesheet Settings ", padding=12)
        settings_lf.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_lf, text="Month & Year (MM.YYYY):").grid(row=0, column=0, sticky=tk.W, pady=4, padx=5)
        self.month_var = tk.StringVar(value="02.2026")
        self.month_entry = ttk.Entry(settings_lf, textvariable=self.month_var, width=15)
        self.month_entry.grid(row=0, column=1, sticky=tk.W, pady=4, padx=5)
        
        ttk.Label(settings_lf, text="Target Hours (e.g. 80):").grid(row=1, column=0, sticky=tk.W, pady=4, padx=5)
        self.hours_var = tk.StringVar(value="80")
        self.hours_entry = ttk.Entry(settings_lf, textvariable=self.hours_var, width=15)
        self.hours_entry.grid(row=1, column=1, sticky=tk.W, pady=4, padx=5)
        
        ttk.Label(settings_lf, text="Save To (Optional):").grid(row=2, column=0, sticky=tk.W, pady=4, padx=5)
        self.save_var = tk.StringVar()
        self.save_entry = ttk.Entry(settings_lf, textvariable=self.save_var, width=32)
        self.save_entry.grid(row=2, column=1, sticky=tk.W, pady=4, padx=5)
        
        self.browse_btn = ttk.Button(settings_lf, text="Browse...", command=self.action_browse, style="Browse.TButton")
        self.browse_btn.grid(row=2, column=2, sticky=tk.W, pady=4, padx=5)
        
        # Section 3: Solver Logs Area
        logs_lf = ttk.LabelFrame(main_container, text=" Solver Calculations Logs ", padding=8)
        logs_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.log_txt = ScrolledText(logs_lf, height=8, bg="#fafafa", fg="#333333", font=("Courier New", 9))
        self.log_txt.pack(fill=tk.BOTH, expand=True)
        self.log_txt.insert(tk.END, "[Status] System initialized. Ready to generate.\n")
        self.log_txt.config(state=tk.DISABLED)
        
        # Generate Action Button
        self.gen_btn = ttk.Button(
            main_container, 
            text="Generate Timesheet Document", 
            command=self.action_generate, 
            style="Generate.TButton"
        )
        self.gen_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Modern bottom status bar
        self.status_lbl = ttk.Label(main_container, text="Ready", style="Sub.TLabel")
        self.status_lbl.pack(anchor=tk.W)

    def write_log(self, text):
        """Thread-safe log printing into ScrolledText box."""
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.insert(tk.END, text)
        self.log_txt.see(tk.END)
        self.log_txt.config(state=tk.DISABLED)

    def update_status(self, text):
        """Thread-safe status bar text update."""
        self.status_lbl.config(text=text)

    def action_browse(self):
        """Action handler to select custom save file path."""
        initial_name = "timesheet.docx"
        name_val = self.name_var.get().strip()
        month_val = self.month_var.get().strip()
        if name_val and month_val:
            clean_name = "".join(c for c in name_val if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            initial_name = f"timesheet_{clean_name}_{month_val.replace('.', '_')}.docx"
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
            initialfile=initial_name
        )
        if file_path:
            self.save_var.set(file_path)

    def action_generate(self):
        """Initiates solver algorithm and generates document in background thread."""
        # Validation checks on UI main thread
        name = self.name_var.get().strip()
        personal_id = self.id_var.get().strip()
        city = self.city_var.get().strip()
        month_str = self.month_var.get().strip()
        hours_str = self.hours_var.get().strip()
        output_path = self.save_var.get().strip()
        
        if not name:
            messagebox.showerror("Input Error", "Employee Name cannot be empty.")
            return
        if not personal_id:
            messagebox.showerror("Input Error", "Personal ID Number cannot be empty.")
            return
        if not city:
            messagebox.showerror("Input Error", "City field cannot be empty.")
            return
            
        try:
            year, month = parse_month_year(month_str)
        except ValueError as e:
            messagebox.showerror("Date Input Error", str(e))
            return
            
        try:
            target_hours = float(hours_str.replace(",", "."))
            if target_hours < 0.0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Hours Input Error", "Target Hours must be a valid positive number.")
            return
            
        # Disable controls during run to ensure safety
        self.gen_btn.state(["disabled"])
        self.browse_btn.state(["disabled"])
        self.update_status("Running solver algorithm...")
        
        # Clear log area
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.delete("1.0", tk.END)
        self.log_txt.config(state=tk.DISABLED)
        self.write_log(f"[Solver] Starting distribution for {month_str} (Target: {target_hours} hrs)...\n")
        
        # Launch solver in separate thread to prevent GUI freezing
        threading.Thread(
            target=self._background_solver_run,
            args=(name, personal_id, year, month, target_hours, city, output_path if output_path else None),
            daemon=True
        ).start()

    def _background_solver_run(self, name, personal_id, year, month, target_hours, city, output_path):
        """Executes actual calculations and file generation in separate background thread."""
        num_days = calendar.monthrange(year, month)[1]
        
        try:
            # Distribute hours using solver, updating logs
            distributed = distribute_monthly_hours(
                num_days, 
                target_hours, 
                log_callback=self.write_log
            )
            
            # Generate and format Word document
            path = generate_docx_timesheet(
                name=name,
                personal_id=personal_id,
                year=year,
                month=month,
                distributed_hours=distributed,
                city=city,
                output_path=output_path
            )
            
            # Success callbacks
            active_days = sum(1 for h in distributed if h > 0.0)
            self.write_log(f"\n[Success] Timesheet file saved successfully:\n{path}\n")
            self.write_log(f"[Summary] Worked days: {active_days} days | Total: {target_hours} hrs.\n")
            
            # Update UI on Main thread via after
            self.root.after(0, lambda: self._on_solver_success(path, active_days, target_hours))
            
        except Exception as e:
            # Failure callbacks
            err_msg = str(e)
            self.root.after(0, lambda: self._on_solver_failure(err_msg))

    def _on_solver_success(self, path, active_days, target_hours):
        """Restores UI and alerts success."""
        self.gen_btn.state(["!disabled"])
        self.browse_btn.state(["!disabled"])
        self.update_status(f"File Saved: {os.path.basename(path)}")
        messagebox.showinfo(
            "Timesheet Generated",
            f"Timesheet successfully generated!\n\n"
            f"File: {os.path.basename(path)}\n"
            f"Target Hours: {target_hours} hrs\n"
            f"Worked Days: {active_days} days\n\n"
            f"Saved at: {path}"
        )

    def _on_solver_failure(self, error_message):
        """Restores UI and shows detailed solver error alerts."""
        self.gen_btn.state(["!disabled"])
        self.browse_btn.state(["!disabled"])
        self.update_status("Solver failed.")
        messagebox.showerror("Solver Error", error_message)


# ==============================================================================
# CLI / TERMINAL INTERFACES & EXECUTION ENTRY POINT
# ==============================================================================

def print_premium_banner():
    """Prints a premium visual header in the console."""
    print("=" * 60)
    print("      ***  OPTIMIZED TIMESHEET GENERATOR SYSTEM  ***")
    print("          Powered by Antigravity AI Engine (V6)")
    print("=" * 60)

def run_interactive_terminal():
    """Runs a highly styled, user-friendly interactive CLI wizard."""
    print_premium_banner()
    print("\nPlease enter the requested information below:\n")
    
    # Name
    while True:
        name = input("[User] Employee Name (e.g. Max Mustermann): ").strip()
        if name:
            break
        print("   [Error] Name cannot be empty. Please try again.")
        
    # ID Number
    while True:
        personal_id = input("[ID] Personal ID Number (e.g. 12345678): ").strip()
        if personal_id:
            break
        print("   [Error] Personal ID cannot be empty. Please try again.")
        
    # City
    city = input("[City] City (Press Enter for default 'Istanbul'): ").strip()
    if not city:
        city = "Istanbul"
        
    # Month & Year
    while True:
        month_year_str = input("[Month] Target Month & Year (e.g. 02.2026): ").strip()
        try:
            year, month = parse_month_year(month_year_str)
            break
        except ValueError as e:
            print(f"   [Error] {e}")
            
    # Target Working Hours
    num_days = calendar.monthrange(year, month)[1]
    max_possible = round((num_days - (num_days // 7)) * 6.5, 1)
    
    while True:
        hours_input = input(f"[Hours] Target Monthly Working Hours (Max possible for this month: {max_possible}): ").strip()
        try:
            target_hours = float(hours_input.replace(",", "."))
            if target_hours < 0.0:
                print("   [Error] Hours must be a positive number.")
                continue
            break
        except ValueError:
            print("   [Error] Invalid hours format. Please enter a number.")
            
    # Output path
    output_path = input("[Save] Save File Path (Press Enter for default): ").strip()
    if not output_path:
        output_path = None
        
    print("\n[Solver] Processing and distributing hours...")
    try:
        distributed = distribute_monthly_hours(num_days, target_hours, verbose=True)
        path = generate_docx_timesheet(name, personal_id, year, month, distributed, city, output_path)
        
        # Success report
        active_days = sum(1 for h in distributed if h > 0.0)
        avg_shift = target_hours / active_days if active_days > 0 else 0.0
        
        print("\n" + "=" * 60)
        print("[Success] TIMESHEET DOCUMENT GENERATED SUCCESSFULLY")
        print("-" * 60)
        print(f"[File] Output File: {path}")
        print(f"[Total] Total Hours: {target_hours} hrs")
        print(f"[Days] Days in Month: {num_days} days")
        print(f"[Work] Worked Days:  {active_days} days")
        print(f"[Avg] Avg shift length: {avg_shift:.2f} hrs")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n[Error] Error generating timesheet: {e}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Premium Word document timesheet generator with weighted monthly hour distribution solver."
    )
    parser.add_argument("--name", help="Employee name (e.g. 'Max Mustermann')")
    parser.add_argument("--id", help="Personal ID number (e.g. '12345678')")
    parser.add_argument("--hours", type=float, help="Target monthly working hours")
    parser.add_argument("--month", help="Target month/year (e.g. '02.2026')")
    parser.add_argument("--city", default="Istanbul", help="City name to list in metadata (default: Istanbul)")
    parser.add_argument("--output", help="Optional custom output path for the Word document")
    parser.add_argument("--cli", action="store_true", help="Launch guided interactive terminal prompt instead of GUI")
    
    args = parser.parse_args()
    
    # Check if CLI options or arguments are specified
    is_cli_run = args.cli or args.name or args.id or args.hours is not None or args.month
    
    if not is_cli_run:
        # Bypasses terminal and launches the Tkinter desktop GUI
        root = tk.Tk()
        app = TimesheetAppGUI(root)
        root.mainloop()
        return
        
    if args.cli:
        run_interactive_terminal()
        return
        
    # Check that required arguments are present for direct headless CLI execution
    if not args.name or not args.id or args.hours is None or not args.month:
        parser.print_help()
        print("\n[Error] Please specify all mandatory arguments (--name, --id, --hours, --month) or run --cli for the interactive terminal guide.")
        sys.exit(1)
        
    try:
        year, month = parse_month_year(args.month)
        num_days = calendar.monthrange(year, month)[1]
        
        print(f"[Solver] Running Solver for {args.month}...")
        distributed = distribute_monthly_hours(num_days, args.hours, verbose=True)
        
        path = generate_docx_timesheet(
            name=args.name,
            personal_id=args.id,
            year=year,
            month=month,
            distributed_hours=distributed,
            city=args.city,
            output_path=args.output
        )
        print(f"[Success] File saved to: {path}")
        
    except Exception as e:
        print(f"[Error] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
