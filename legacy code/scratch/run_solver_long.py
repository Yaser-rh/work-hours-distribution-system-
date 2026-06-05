import sys
import os
import calendar
import time

sys.path.insert(0, 'c:/Users/rh22/Desktop/excel')

from db.database import initialize_database
import db.models as models
import solver.sat_solver as sat_solver
from ortools.sat.python import cp_model

city_id = 2
year = 2026
month = 6

all_ts = models.get_timesheets(city_id=city_id, year=year, month=month)
active_ts = [t for t in all_ts if t['status'] == 'Draft' and not t['is_distribution_locked']]
locked_ts = [t for t in all_ts if t['status'] == 'Finalized' or t['is_distribution_locked']]

print(f"Active drivers: {len(active_ts)}")
print(f"Locked drivers: {len(locked_ts)}")

cities = models.get_cities()
city = next((c for c in cities if c['id'] == city_id), None)
city_start = sat_solver.clock_to_units(city['start_time'])
city_end = sat_solver.clock_to_units(city['end_time'])
_, num_days = calendar.monthrange(year, month)

drivers = []
for ts in active_ts:
    drivers.append(sat_solver.DriverSpec(
        employee_id=ts['employee_id'],
        target_units=sat_solver.hours_to_units(ts['target_hours']),
        name=ts['employee_name']
    ))

locked_entries = {}
for ts in locked_ts:
    ts_detail = models.get_timesheet_with_entries(ts['id'])
    locked_entries[ts['employee_id']] = ts_detail.get('entries', [])

prev_month_boundary = {}
cross_city_active = {}
for d_spec in drivers:
    prev_month_boundary[d_spec.employee_id] = models.get_previous_month_boundary(
        d_spec.employee_id, year, month
    )
    cross_city_active[d_spec.employee_id] = models.get_cross_city_active_days(
        d_spec.employee_id, year, month, city_id
    )

existing_coverage = models.get_city_coverage(city_id, year, month, exclude_timesheet_ids=[t['id'] for t in active_ts])

solver_input = sat_solver.SolverInput(
    drivers=drivers,
    city_start=city_start,
    city_end=city_end,
    num_days=num_days,
    prev_month_boundary=prev_month_boundary,
    cross_city_active=cross_city_active,
    existing_coverage=existing_coverage,
    locked_entries=locked_entries,
    mode='batch'
)

# Build model
model = cp_model.CpModel()
locked_coverage = {d: {slot: 0 for slot in range(48)} for d in range(1, num_days + 1)}
for emp_id, entries in locked_entries.items():
    for entry in entries:
        work_date = entry.get("work_date", "")
        day = int(work_date.split('-')[2]) if '-' in work_date else int(work_date.split('.')[0])
        st = entry.get("start_time", "")
        et = entry.get("end_time", "")
        if st and et:
            st_slot = sat_solver.clock_to_units(st)
            et_slot = sat_solver.clock_to_units(et)
            for slot in range(st_slot, et_slot):
                if 0 <= slot < 48:
                    locked_coverage[day][slot] += 1

vars_dict = sat_solver._build_solver_vars_and_constraints(model, solver_input, locked_coverage, exact=True)

# Run CP-SAT solver for 60 seconds
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = False

print("Solving for 60 seconds...")
start_time = time.time()
status = solver.Solve(model)
duration = time.time() - start_time
print(f"Status: {solver.StatusName(status)}")
print(f"Solve duration: {duration:.2f}s")
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"Objective value: {solver.ObjectiveValue()}")
    
    # Calculate daily statistics
    schedules = sat_solver._extract_results(solver, solver_input, vars_dict)
    
    # Check Day 7 coverage profile in this new solution
    d = 7
    active_covers = {slot: 0 for slot in range(city_start, city_end)}
    for emp_id, sched in schedules.items():
        day_entry = sched[d - 1]
        if day_entry.hours > 0:
            st_slot = sat_solver.clock_to_units(day_entry.start_time)
            et_slot = sat_solver.clock_to_units(day_entry.end_time)
            for slot in range(st_slot, et_slot):
                if city_start <= slot < city_end:
                    active_covers[slot] += 1
                    
    # Locked coverage on Day 7
    locked_day = locked_coverage.get(d, {})
    total_covers = {slot: active_covers[slot] + locked_day.get(slot, 0) for slot in range(city_start, city_end)}
    
    print("\nNew Day 7 Coverage Profile:")
    for slot in range(city_start, city_end):
        clock = sat_solver.units_to_clock(slot)
        print(f"{clock} -> active: {active_covers[slot]}, locked: {locked_day.get(slot, 0)}, total: {total_covers[slot]}")
else:
    print("No solution found.")
