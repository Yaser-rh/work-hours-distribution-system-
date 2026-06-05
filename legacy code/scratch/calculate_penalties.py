import sqlite3
import sys
import calendar

sys.path.insert(0, 'c:/Users/rh22/Desktop/excel')
import solver.sat_solver as sat_solver

conn = sqlite3.connect('c:/Users/rh22/Desktop/excel/timesheets.db')
c = conn.cursor()

# Get all daily entries
c.execute("""
    select de.work_date, t.employee_id, de.start_time, de.end_time, de.hours_worked
    from daily_entry de
    join timesheet t on de.timesheet_id = t.id
    where t.month = 6 and t.year = 2026 and t.city_id = 2 and de.hours_worked > 0
""")
rows = c.fetchall()

city_start = sat_solver.clock_to_units("06:00")
city_end = sat_solver.clock_to_units("22:00")
num_days = 30

# Reconstruct daily coverage
coverage = {d: {slot: 0 for slot in range(city_start, city_end)} for d in range(1, num_days + 1)}
half_hour_penalty = 0

for work_date, emp_id, start, end, hours in rows:
    day = int(work_date.split('-')[2])
    st_slot = sat_solver.clock_to_units(start)
    et_slot = sat_solver.clock_to_units(end)
    
    # Half-hour penalty: count shifts with non-integer hour lengths
    # (scaled units are odd)
    units = et_slot - st_slot
    # Note: break duration is not included in units_worked but start/end time difference is hours + break.
    # Let's count if the worked hours (excluding break) is odd.
    # From sat_solver.py: hours_var is the worked units.
    # If worked hours is float with .5, it is odd.
    if hours % 1.0 != 0:
        half_hour_penalty += 1
        
    for slot in range(st_slot, et_slot):
        if city_start <= slot < city_end:
            coverage[day][slot] += 1

# 1. Half-hour penalty
print(f"Half-hour penalty (alpha=1): {half_hour_penalty}")

# 2. Staggering penalty (Batch Mode: sum of daily peak coverages)
staggering_penalty = 0
for d in range(1, num_days + 1):
    daily_peak = max(coverage[d].values()) if coverage[d] else 0
    staggering_penalty += daily_peak
print(f"Staggering penalty (beta=10): {staggering_penalty} (weighted: {staggering_penalty * 10})")

# 3. Daily distribution penalty
# ideal_daily_units
total_worked_units = sum(int(round(h * 2)) for _, _, _, _, h in rows)
ideal_daily_units = total_worked_units // num_days
print(f"Total worked units: {total_worked_units}, Ideal daily units: {ideal_daily_units}")

daily_distribution_penalty = 0
for d in range(1, num_days + 1):
    daily_units = sum(int(round(h * 2)) for wd, _, _, _, h in rows if int(wd.split('-')[2]) == d)
    daily_distribution_penalty += abs(daily_units - ideal_daily_units)
print(f"Daily distribution penalty (eta=10): {daily_distribution_penalty} (weighted: {daily_distribution_penalty * 10})")

# 4. Uncovered penalty
uncovered_penalty = 0
for d in range(1, num_days + 1):
    for slot in range(city_start, city_end):
        if coverage[d][slot] == 0:
            uncovered_penalty += 1
            print(f"Day {d} slot {sat_solver.units_to_clock(slot)} is uncovered")
print(f"Uncovered slots penalty (delta=10000): {uncovered_penalty} (weighted: {uncovered_penalty * 10000})")

total_obj = half_hour_penalty * 1 + staggering_penalty * 10 + daily_distribution_penalty * 10 + uncovered_penalty * 10000
print(f"Reconstructed objective: {total_obj}")
conn.close()
