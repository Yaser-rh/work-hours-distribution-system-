import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ortools.sat.python import cp_model

# ==============================================================================
# Scaling Helper Constants and Functions
# ==============================================================================

# Time is scaled to 30-minute intervals (1 unit = 30 minutes)
# Allowed shift durations in scaled units:
# 2.0h -> 4 units, 2.5h -> 5 units, ..., 8.0h -> 16 units
ALLOWED_SHIFTS = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
ODD_SHIFTS = {5, 7, 9, 11, 13, 15}  # Represents non-integer shifts (2.5, 3.5, etc.)

def hours_to_units(hours: float) -> int:
    """Converts real hours (float) to scaled integer units."""
    return int(round(hours * 2))

def units_to_hours(units: int) -> float:
    """Converts scaled integer units to real hours (float)."""
    return units / 2.0

def clock_to_units(clock_str: str) -> int:
    """
    Converts a clock time ("HH:MM") into scaled units from midnight.
    e.g., "08:00" -> 16, "08:30" -> 17, "22:00" -> 44.
    """
    if not clock_str:
        return 0
    parts = clock_str.split(':')
    if len(parts) != 2:
        return 0
    try:
        h, m = int(parts[0]), int(parts[1])
        return h * 2 + (1 if m >= 30 else 0)
    except ValueError:
        return 0

def units_to_clock(units: int) -> str:
    """
    Converts scaled units from midnight to clock time string ("HH:MM").
    """
    h = units // 2
    m = 30 if (units % 2) != 0 else 0
    return f"{h:02d}:{m:02d}"


# ==============================================================================
# Dataclasses
# ==============================================================================

@dataclass
class DriverSpec:
    employee_id: int
    target_units: int   # target_hours * 2
    name: str

@dataclass
class SolverInput:
    drivers: List[DriverSpec]                         # Unlocked/active drivers to schedule
    city_start: int                                   # Scaled units from midnight
    city_end: int                                     # Scaled units from midnight
    num_days: int                                     # Days in the month
    prev_month_boundary: Dict[int, List[int]]         # employee_id -> last 6 days (0/1)
    cross_city_active: Dict[int, Dict[int, int]]       # employee_id -> {day: 0/1}
    existing_coverage: Dict[int, Dict[int, int]]       # day -> {slot: count} (incremental mode other drivers)
    locked_entries: Dict[int, List[Dict[str, Any]]]   # employee_id -> daily entries (for locked timesheets)
    mode: str                                         # 'batch' or 'incremental'

@dataclass
class DayEntry:
    day: int            # 1-indexed day of month
    hours: float        # Real hours worked (paid hours)
    start_time: str     # "HH:MM" or ""
    end_time: str       # "HH:MM" or ""
    break_minutes: int  # 0 or 30

@dataclass
class SolverResult:
    status: str                                  # 'exact', 'nearest', 'failed'
    schedules: Dict[int, List[DayEntry]]         # employee_id -> list of day entries
    target_deviation: float                      # 0.0 if exact, else the gap in real hours
    solve_time_seconds: float


# ==============================================================================
# Solve Routine
# ==============================================================================

def solve(solver_input: SolverInput) -> SolverResult:
    """
    Solves the driver shift distribution problem using CP-SAT.
    Runs Phase A (exact target match), falling back to Phase B (nearest feasible) if A fails.
    """
    start_time_perf = time.perf_counter()

    # Pre-populate return structure with locked entries for locked drivers
    final_schedules: Dict[int, List[DayEntry]] = {}
    
    # Process locked timesheets. These drivers don't have variables solved.
    # Note that locked_entries is employee_id -> list of dicts.
    for emp_id, entries in solver_input.locked_entries.items():
        # Map existing entries by day
        entries_by_day = {}
        for entry in entries:
            work_date = entry.get("work_date", "")
            day = 1
            if '-' in work_date:
                day = int(work_date.split('-')[2])
            elif '.' in work_date:
                day = int(work_date.split('.')[0])
            entries_by_day[day] = entry

        driver_schedule = []
        for day in range(1, solver_input.num_days + 1):
            if day in entries_by_day:
                entry = entries_by_day[day]
                hours_worked = entry.get("hours_worked", 0.0)
                st = entry.get("start_time", "")
                et = entry.get("end_time", "")
                
                # break_duration format is typically "hh:mm" or "HH:MM" or string
                break_dur = entry.get("break_duration", "")
                break_min = 0
                if ":" in break_dur:
                    parts = break_dur.split(":")
                    break_min = int(parts[0]) * 60 + int(parts[1])
                
                driver_schedule.append(DayEntry(
                    day=day,
                    hours=hours_worked,
                    start_time=st if hours_worked > 0.0 else "",
                    end_time=et if hours_worked > 0.0 else "",
                    break_minutes=break_min if hours_worked > 0.0 else 0
                ))
            else:
                driver_schedule.append(DayEntry(
                    day=day,
                    hours=0.0,
                    start_time="",
                    end_time="",
                    break_minutes=0
                ))
        final_schedules[emp_id] = driver_schedule

    # If there are no active drivers to solve, we are already done!
    if not solver_input.drivers:
        return SolverResult(
            status='exact',
            schedules=final_schedules,
            target_deviation=0.0,
            solve_time_seconds=time.perf_counter() - start_time_perf
        )

    # ---------------------------------------------------------
    # Building Coverage Maps from Locked Drivers
    # ---------------------------------------------------------
    # day -> {slot: count}
    locked_coverage: Dict[int, Dict[int, int]] = {
        d: {slot: 0 for slot in range(48)} for d in range(1, solver_input.num_days + 1)
    }
    for emp_id, entries in solver_input.locked_entries.items():
        for entry in entries:
            work_date = entry.get("work_date", "")
            day = None
            if '-' in work_date:
                day = int(work_date.split('-')[2])
            elif '.' in work_date:
                day = int(work_date.split('.')[0])
            
            if day is not None and day in locked_coverage:
                st = entry.get("start_time", "")
                et = entry.get("end_time", "")
                if st and et:
                    st_slot = clock_to_units(st)
                    et_slot = clock_to_units(et)
                    for slot in range(st_slot, et_slot):
                        if 0 <= slot < 48:
                            locked_coverage[day][slot] += 1

    # ==============================================================================
    # Phase A: Exact Solve
    # ==============================================================================
    model_a = cp_model.CpModel()
    vars_a = _build_solver_vars_and_constraints(model_a, solver_input, locked_coverage, exact=True)
    
    solver_a = cp_model.CpSolver()
    solver_a.parameters.max_time_in_seconds = 10.0
    solver_a.parameters.num_search_workers = 8
    solver_a.parameters.relative_gap_limit = 0.05
    
    status_a = solver_a.Solve(model_a)
    
    if status_a in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        active_schedules = _extract_results(solver_a, solver_input, vars_a)
        final_schedules.update(active_schedules)
        return SolverResult(
            status='exact',
            schedules=final_schedules,
            target_deviation=0.0,
            solve_time_seconds=time.perf_counter() - start_time_perf
        )

    # ==============================================================================
    # Phase B: Nearest Feasible Solve
    # ==============================================================================
    model_b = cp_model.CpModel()
    vars_b = _build_solver_vars_and_constraints(model_b, solver_input, locked_coverage, exact=False)
    
    solver_b = cp_model.CpSolver()
    solver_b.parameters.max_time_in_seconds = 10.0
    solver_b.parameters.num_search_workers = 8
    solver_b.parameters.relative_gap_limit = 0.05
    
    status_b = solver_b.Solve(model_b)
    
    if status_b in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        active_schedules = _extract_results(solver_b, solver_input, vars_b)
        final_schedules.update(active_schedules)
        
        # Calculate deviation in real hours
        total_dev_units = solver_b.ObjectiveValue()
        # Note: Phase B objective includes deviation * 1000 + staggering/half-hour weights.
        # We can extract the deviation_var values to get exact deviation units.
        deviation_units = 0
        for d_spec in solver_input.drivers:
            dev_var = vars_b['deviation_var'][d_spec.employee_id]
            deviation_units += solver_b.Value(dev_var)
            
        return SolverResult(
            status='nearest',
            schedules=final_schedules,
            target_deviation=units_to_hours(deviation_units),
            solve_time_seconds=time.perf_counter() - start_time_perf
        )
        
    return SolverResult(
        status='failed',
        schedules={},
        target_deviation=0.0,
        solve_time_seconds=time.perf_counter() - start_time_perf
    )


# ==============================================================================
# Model Construction
# ==============================================================================

def _build_solver_vars_and_constraints(model: cp_model.CpModel,
                                      solver_input: SolverInput,
                                      locked_coverage: Dict[int, Dict[int, int]],
                                      exact: bool) -> Dict[str, Any]:
    """
    Constructs all decision variables, hard constraints, and the multi-objective
    function on the provided CpModel.
    """
    num_days = solver_input.num_days
    city_start = solver_input.city_start
    city_end = solver_input.city_end

    # Variables storage
    active_var = {}
    hours_var = {}
    start_var = {}
    break_var = {}
    end_var = {}
    is_half_var = {}
    covers_var = {}
    deviation_var = {}

    all_active_driver_ids = [d.employee_id for d in solver_input.drivers]

    # Domain for shift hours: 0 or S
    # S = {4, 5, ..., 16}
    hours_domain = cp_model.Domain.FromIntervals([(0, 0)] + [(s, s) for s in ALLOWED_SHIFTS])
    odd_domain = cp_model.Domain.FromValues(list(ODD_SHIFTS))
    even_domain = cp_model.Domain.FromValues([0] + [s for s in ALLOWED_SHIFTS if s not in ODD_SHIFTS])

    for d_spec in solver_input.drivers:
        w = d_spec.employee_id
        
        # Load driver boundary data
        prev_month = solver_input.prev_month_boundary.get(w, [0] * 6)
        cross_city = solver_input.cross_city_active.get(w, {})
        
        for d in range(1, num_days + 1):
            active_var[w, d] = model.NewBoolVar(f"active_{w}_{d}")
            hours_var[w, d] = model.NewIntVarFromDomain(hours_domain, f"hours_{w}_{d}")
            start_var[w, d] = model.NewIntVar(0, 48, f"start_{w}_{d}")
            break_var[w, d] = model.NewBoolVar(f"break_{w}_{d}")
            end_var[w, d] = model.NewIntVar(0, 48, f"end_{w}_{d}")
            
            # C1: active[w,d] == 0  <=>  hours[w,d] == 0
            model.Add(hours_var[w, d] == 0).OnlyEnforceIf(active_var[w, d].Not())
            model.Add(hours_var[w, d] > 0).OnlyEnforceIf(active_var[w, d])
            
            # C3: Auto-break. Shift of >= 6.5 hours (13 units) triggers break = 1 unit.
            is_long = model.NewBoolVar(f"is_long_{w}_{d}")
            model.Add(hours_var[w, d] >= 13).OnlyEnforceIf(is_long)
            model.Add(hours_var[w, d] < 13).OnlyEnforceIf(is_long.Not())
            model.Add(break_var[w, d] == 1).OnlyEnforceIf(is_long)
            model.Add(break_var[w, d] == 0).OnlyEnforceIf(is_long.Not())
            
            # C4: City window bounds when active
            model.Add(start_var[w, d] >= city_start).OnlyEnforceIf(active_var[w, d])
            model.Add(end_var[w, d] <= city_end).OnlyEnforceIf(active_var[w, d])
            
            # If inactive, bind times to 0 to keep variables clean
            model.Add(start_var[w, d] == 0).OnlyEnforceIf(active_var[w, d].Not())
            model.Add(end_var[w, d] == 0).OnlyEnforceIf(active_var[w, d].Not())
            
            # C6: End time derivation
            model.Add(end_var[w, d] == start_var[w, d] + hours_var[w, d] + break_var[w, d])
            
            # Ergonomic preferences: track half-hour shifts
            is_half_var[w, d] = model.NewBoolVar(f"is_half_{w}_{d}")
            model.AddLinearExpressionInDomain(hours_var[w, d], odd_domain).OnlyEnforceIf(is_half_var[w, d])
            model.AddLinearExpressionInDomain(hours_var[w, d], even_domain).OnlyEnforceIf(is_half_var[w, d].Not())
            
            # Covers variables for staggering
            for t in range(city_start, city_end):
                after_start = model.NewBoolVar(f"after_start_{w}_{d}_{t}")
                model.Add(start_var[w, d] <= t).OnlyEnforceIf(after_start)
                model.Add(start_var[w, d] > t).OnlyEnforceIf(after_start.Not())
                
                before_end = model.NewBoolVar(f"before_end_{w}_{d}_{t}")
                model.Add(end_var[w, d] >= t + 1).OnlyEnforceIf(before_end)
                model.Add(end_var[w, d] < t + 1).OnlyEnforceIf(before_end.Not())
                
                c_var = model.NewBoolVar(f"covers_{w}_{d}_{t}")
                model.AddBoolAnd([after_start, before_end]).OnlyEnforceIf(c_var)
                model.AddBoolOr([after_start.Not(), before_end.Not()]).OnlyEnforceIf(c_var.Not())
                covers_var[w, d, t] = c_var

        # C2: Monthly target
        sum_hours = sum(hours_var[w, d] for d in range(1, num_days + 1))
        if exact:
            model.Add(sum_hours == d_spec.target_units)
        else:
            # Phase B: Minimize absolute deviation
            # target_deviation = |sum_hours - target_units|
            # Let dev_var be >= 0
            dev_var = model.NewIntVar(0, 48 * num_days, f"dev_{w}")
            model.Add(sum_hours - d_spec.target_units <= dev_var)
            model.Add(d_spec.target_units - sum_hours <= dev_var)
            deviation_var[w] = dev_var

        # C5: 6-consecutive-day limit globally (incorporates prior month & other cities)
        global_active = []
        # 1. Prior month's last 6 days (constants)
        for prev_val in prev_month:
            global_active.append(prev_val)
            
        # 2. Current month days
        for d in range(1, num_days + 1):
            cross_city_active_day = cross_city.get(d, 0)
            if cross_city_active_day == 1:
                # If active in another city, they are globally active on this day
                global_active.append(1)
            else:
                # Otherwise, active status is determined by current city's active variable
                global_active.append(active_var[w, d])
                
        # 3. Apply sliding window constraint (sum of any 7 consecutive days <= 6)
        for i in range(len(global_active) - 6):
            model.Add(sum(global_active[i:i+7]) <= 6)

    # ==============================================================================
    # Objective Formulation
    # ==============================================================================
    alpha = 1   # weight of half-hour penalty
    beta = 10   # weight of staggering/overlap penalty
    gamma = 1000 # weight of target deviation in Phase B

    # 1. Half-hour penalty
    half_hour_penalty = sum(is_half_var[w, d] for w in all_active_driver_ids for d in range(1, num_days + 1))

    # 2. Overlap/Staggering penalty
    staggering_penalty = 0
    if solver_input.mode == 'incremental':
        # Minimize overlap with existing coverage profile (constant)
        # existing_coverage: day -> {slot: count}
        for d in range(1, num_days + 1):
            day_cov = solver_input.existing_coverage.get(d, {})
            for t in range(city_start, city_end):
                w = all_active_driver_ids[0] # Incremental has exactly 1 driver
                weight = day_cov.get(t, 0)
                if weight > 0:
                    staggering_penalty += covers_var[w, d, t] * weight
    else:
        # Batch Mode: Minimize peak coverage across all slots
        batch_penalties = []
        for d in range(1, num_days + 1):
            max_cov = model.NewIntVar(0, len(all_active_driver_ids) + len(solver_input.locked_entries), f"max_cov_{d}")
            locked_day = locked_coverage.get(d, {})
            for t in range(city_start, city_end):
                active_covers = [covers_var[w, d, t] for w in all_active_driver_ids]
                locked_val = locked_day.get(t, 0)
                # max_cov[d] >= sum(active_covers) + locked_val
                model.Add(max_cov >= sum(active_covers) + locked_val)
            batch_penalties.append(max_cov)
        staggering_penalty = sum(batch_penalties)

    if exact:
        model.Minimize(alpha * half_hour_penalty + beta * staggering_penalty)
    else:
        dev_penalty = sum(deviation_var[w] for w in all_active_driver_ids)
        model.Minimize(alpha * half_hour_penalty + beta * staggering_penalty + gamma * dev_penalty)

    return {
        'active_var': active_var,
        'hours_var': hours_var,
        'start_var': start_var,
        'break_var': break_var,
        'end_var': end_var,
        'deviation_var': deviation_var
    }


# ==============================================================================
# Results Extraction
# ==============================================================================

def _extract_results(solver: cp_model.CpSolver,
                     solver_input: SolverInput,
                     variables: Dict[str, Any]) -> Dict[int, List[DayEntry]]:
    """
    Extracts the solved schedules from the solver variables.
    """
    schedules = {}
    num_days = solver_input.num_days

    for d_spec in solver_input.drivers:
        w = d_spec.employee_id
        driver_schedule = []
        
        for d in range(1, num_days + 1):
            is_active = solver.Value(variables['active_var'][w, d])
            
            if is_active:
                units = solver.Value(variables['hours_var'][w, d])
                start_val = solver.Value(variables['start_var'][w, d])
                end_val = solver.Value(variables['end_var'][w, d])
                has_break = solver.Value(variables['break_var'][w, d])
                
                hours = units_to_hours(units)
                start_time = units_to_clock(start_val)
                end_time = units_to_clock(end_val)
                break_min = 30 if has_break else 0
            else:
                hours = 0.0
                start_time = ""
                end_time = ""
                break_min = 0
                
            driver_schedule.append(DayEntry(
                day=d,
                hours=hours,
                start_time=start_time,
                end_time=end_time,
                break_minutes=break_min
            ))
            
        schedules[w] = driver_schedule

    return schedules
