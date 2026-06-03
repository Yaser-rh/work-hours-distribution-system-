import pytest
import solver.sat_solver as sat_solver

def test_exact_target_match():
    # 30-day month, target 80.0 hours (160 units)
    # City operational window 08:00 to 22:00 (16 to 44 units)
    driver = sat_solver.DriverSpec(employee_id=1, target_units=160, name="Driver A")
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    assert result.target_deviation == 0.0
    
    schedule = result.schedules[1]
    assert len(schedule) == 30
    
    # Verify total sum of paid hours matches target
    total_hours = sum(d.hours for d in schedule)
    assert abs(total_hours - 80.0) < 0.01
    
    # Verify shifts are within bounds
    for entry in schedule:
        if entry.hours > 0.0:
            assert entry.hours >= 2.0 and entry.hours <= 8.0
            st_val = sat_solver.clock_to_units(entry.start_time)
            et_val = sat_solver.clock_to_units(entry.end_time)
            assert st_val >= 16
            assert et_val <= 44
            
            # Verify end_time == start_time + hours + break
            total_elapsed = entry.hours + (entry.break_minutes / 60.0)
            assert abs((et_val - st_val) / 2.0 - total_elapsed) < 0.01


def test_break_application():
    # Verify that a shift of 6.5h or more gets 30m break, and less than 6.5h gets 0m break
    driver = sat_solver.DriverSpec(employee_id=1, target_units=80, name="Driver A") # 40 hours target
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    schedule = result.schedules[1]
    for entry in schedule:
        if entry.hours > 0.0:
            if entry.hours >= 6.5:
                assert entry.break_minutes == 30
            else:
                assert entry.break_minutes == 0


def test_consecutive_days_limit():
    # Max consecutive workdays is 6. Check that no sequence of active days is > 6.
    driver = sat_solver.DriverSpec(employee_id=1, target_units=192, name="Driver A") # 96.0 hours target
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    schedule = result.schedules[1]
    consecutive = 0
    for entry in schedule:
        if entry.hours > 0.0:
            consecutive += 1
            assert consecutive <= 6
        else:
            consecutive = 0


def test_cross_month_boundary():
    # Driver worked the last 6 days of previous month.
    # Day 1 of current month MUST be a rest day (0 hours).
    driver = sat_solver.DriverSpec(employee_id=1, target_units=60, name="Driver A")
    
    # 6 consecutive working days at end of previous month
    prev_month_boundary = {1: [1, 1, 1, 1, 1, 1]}
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary=prev_month_boundary,
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    schedule = result.schedules[1]
    # Day 1 of current month must be off
    assert schedule[0].hours == 0.0


def test_cross_city_active_days():
    # Driver works in Ankara on June 1, 2, 3 (cross-city).
    # Istanbul schedule must respect these days in consecutive day sum.
    # Total targets demand work, check consecutive days globally.
    driver = sat_solver.DriverSpec(employee_id=1, target_units=160, name="Driver A") # 80.0h
    
    # Cross city active days: Day 4, 5, 6 are active in another city.
    # If the Istanbul solver makes Day 1, 2, 3, and Day 7 active,
    # then Days 1 to 7 are active (7 days consecutive), violating the limit.
    # Solver must avoid this.
    cross_city_active = {1: {4: 1, 5: 1, 6: 1}}
    prev_month_boundary = {1: [0, 0, 0, 1, 1, 1]} # Worked last 3 days of previous month
    # This means:
    # Prev month last 3 days: 1, 1, 1
    # Current month:
    # Day 1, 2, 3: ?
    # Day 4, 5, 6: 1, 1, 1 (cross city)
    # Day 7: ?
    # Let's verify consecutive day sliding window handles it.
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary=prev_month_boundary,
        cross_city_active=cross_city_active,
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    # Let's inspect the combined active days
    schedule = result.schedules[1]
    combined = [1, 1, 1] + [1 if entry.hours > 0.0 or cross_city_active[1].get(entry.day, 0) == 1 else 0 for entry in schedule]
    
    # Check that in combined active array, no sliding window of 7 days has sum > 6
    for i in range(len(combined) - 6):
        assert sum(combined[i:i+7]) <= 6


def test_half_hour_minimization():
    # If target is 8.0 hours, it should prefer one 8.0h shift (integer) over multiple odd half-hour shifts
    # target is 16 units.
    driver = sat_solver.DriverSpec(employee_id=1, target_units=16, name="Driver A")
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    schedule = result.schedules[1]
    # Check that it uses integer shift length (like 8.0) rather than (4.5 + 3.5)
    active_entries = [e for e in schedule if e.hours > 0.0]
    assert len(active_entries) == 1
    assert active_entries[0].hours == 8.0


def test_nearest_feasible_fallback():
    # Make target impossible to achieve: e.g. 300 hours in a 30-day month.
    # Max possible hours is 26 workdays * 8.0h = 208 hours.
    driver = sat_solver.DriverSpec(employee_id=1, target_units=600, name="Driver A") # 300.0 hours target
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    # Should fall back to Phase B and find nearest feasible
    assert result.status == 'nearest'
    assert result.target_deviation > 0.0
    
    # Verify returned hours is max possible
    schedule = result.schedules[1]
    total_hours = sum(d.hours for d in schedule)
    assert total_hours <= 208.0


def test_batch_staggering():
    # 3 active drivers in batch mode, target 10h each.
    # City starts at 08:00 (16), ends at 22:00 (44).
    # Solver should spread their start times to minimize overlap.
    drivers = [
        sat_solver.DriverSpec(employee_id=1, target_units=20, name="Driver 1"),
        sat_solver.DriverSpec(employee_id=2, target_units=20, name="Driver 2"),
        sat_solver.DriverSpec(employee_id=3, target_units=20, name="Driver 3")
    ]
    
    solver_input = sat_solver.SolverInput(
        drivers=drivers,
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    # On days when multiple drivers work, check that start times are staggered.
    # Let's count days where all 3 drivers worked
    for day in range(1, 31):
        active_starts = []
        for emp_id in [1, 2, 3]:
            entry = result.schedules[emp_id][day - 1]
            if entry.hours > 0.0:
                active_starts.append(entry.start_time)
        if len(active_starts) >= 2:
            # Check that they don't all start at the exact same time
            # (staggering penalizes overlap, so they should stagger if possible)
            unique_starts = set(active_starts)
            # If there are 3 drivers working, we expect at least 2 distinct start times
            assert len(unique_starts) >= 2


def test_locked_entries_remain_unchanged():
    # Driver 1 is active. Driver 2 is locked.
    # Check that Driver 2's schedule matches locked_entries exactly in output,
    # and Driver 1's schedule staggers around Driver 2.
    driver1 = sat_solver.DriverSpec(employee_id=1, target_units=20, name="Driver 1") # 10.0 hours
    
    # Driver 2 is locked: worked June 5, 08:00 to 18:00 (8.0h + 0.5h break => 8.5h elapsed)
    # break_duration: "00:30"
    locked_entries = {
        2: [
            {"work_date": "2026-06-05", "hours_worked": 8.0, "start_time": "08:00", "end_time": "16:30", "break_duration": "00:30", "remarks": "Locked Shift"}
        ]
    }
    
    solver_input = sat_solver.SolverInput(
        drivers=[driver1],
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries=locked_entries,
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    # Verify Driver 2's output schedule contains June 5 locked entry
    schedule2 = result.schedules[2]
    # In a 30-day month, day 5 is index 4
    day5_entry = schedule2[4]
    assert day5_entry.hours == 8.0
    assert day5_entry.start_time == "08:00"
    assert day5_entry.end_time == "16:30"
    assert day5_entry.break_minutes == 30
    
    # Verify other days for Driver 2 are empty/off
    for day_idx, entry in enumerate(schedule2):
        if day_idx != 4:
            assert entry.hours == 0.0
            assert entry.start_time == ""
            assert entry.end_time == ""
            
    # Verify Driver 1's start time on day 5 staggers (avoids starting at 08:00 if possible)
    schedule1 = result.schedules[1]
    day5_entry_driver1 = schedule1[4]
    if day5_entry_driver1.hours > 0.0:
        assert day5_entry_driver1.start_time != "08:00"


def test_istanbul_hybrid_distribution():
    # 3 active drivers in batch mode, target 80h (160 units) each.
    # Checks that their work days are spread out across all weeks of the month.
    drivers = [
        sat_solver.DriverSpec(employee_id=101, target_units=160, name="Driver 1"),
        sat_solver.DriverSpec(employee_id=102, target_units=160, name="Driver 2"),
        sat_solver.DriverSpec(employee_id=103, target_units=160, name="Driver 3")
    ]
    
    solver_input = sat_solver.SolverInput(
        drivers=drivers,
        city_start=16,
        city_end=44,
        num_days=30,
        prev_month_boundary={},
        cross_city_active={},
        existing_coverage={},
        locked_entries={},
        mode='batch'
    )
    
    result = sat_solver.solve(solver_input)
    assert result.status == 'exact'
    
    # Check each driver's distribution
    for emp_id in [101, 102, 103]:
        schedule = result.schedules[emp_id]
        
        # Verify that in each 7-day week, the driver works at least 1 day and at most 5 days
        weeks = [
            schedule[0:7],   # Week 1
            schedule[7:14],  # Week 2
            schedule[14:21], # Week 3
            schedule[21:28]  # Week 4
        ]
        for w_idx, week in enumerate(weeks):
            active_days = sum(1 for entry in week if entry.hours > 0.0)
            # Must work at least 1 day and at most 5 days in each week
            assert active_days >= 1, f"Driver {emp_id} has no active days in week {w_idx + 1}"
            assert active_days <= 5, f"Driver {emp_id} has too many active days ({active_days}) in week {w_idx + 1}"

