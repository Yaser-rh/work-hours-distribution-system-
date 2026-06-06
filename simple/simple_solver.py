import math
import calendar
import random
from datetime import datetime
from typing import Dict, List, Any

# ==============================================================================
# Helper Constants and Functions
# ==============================================================================

# Scaled time intervals: 1 unit = 30 minutes
ALLOWED_SHIFTS = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}  # 2.0h to 8.0h
ODD_SHIFTS = {5, 7, 9, 11, 13, 15}  # represent half-hour shifts (2.5h, 3.5h, etc.)

def hours_to_units(hours: float) -> int:
    """Converts hours (float) to scaled integer units (1 unit = 30 mins)."""
    return int(round(hours * 2))

def units_to_hours(units: int) -> float:
    """Converts scaled integer units to float hours."""
    return units / 2.0

def clock_to_units(clock_str: str) -> int:
    """Converts a clock time ("HH:MM") into scaled units from midnight."""
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
    """Converts scaled units from midnight to clock time string ("HH:MM")."""
    h = (units // 2) % 24
    m = 30 if (units % 2) != 0 else 0
    return f"{h:02d}:{m:02d}"

# ==============================================================================
# Pure Greedy Solver Engine
# ==============================================================================

def greedy_solve(
    target_hours: float,
    city_start_str: str,
    city_end_str: str,
    year: int,
    month: int,
    allow_morning: bool = True,
    allow_afternoon: bool = True,
    allow_evening: bool = True
) -> Dict[str, Any]:
    """
    Distributes target hours across a month using a pure greedy scheduling algorithm with randomized variety.
    Respects maximum shift lengths, minimum shift lengths, and the 6-consecutive-days rule.
    Does not use CP-SAT or database queries.
    
    Returns a dictionary containing:
        - 'daily_entries': List of daily entry dicts for docx_exporter.
        - 'scheduled_hours': Total hours actually scheduled.
        - 'work_days_count': Number of days scheduled.
        - 'deviation': Difference between scheduled and target hours.
    """
    # Initialize a non-deterministic random generator using system entropy
    solver_rng = random.Random()
    
    target_units = hours_to_units(target_hours)
    city_start = clock_to_units(city_start_str)
    city_end = clock_to_units(city_end_str)
    
    # Handle overnight city windows (e.g. 18:00 to 02:00)
    if city_end < city_start:
        city_end += 48
        
    num_days = calendar.monthrange(year, month)[1]
    
    # If target is non-positive, return empty timesheet
    if target_units <= 0:
        daily_entries = []
        for d in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{d:02d}"
            daily_entries.append({
                "work_date": date_str,
                "hours_worked": 0.0,
                "start_time": "",
                "end_time": "",
                "break_duration": "",
                "remarks": ""
            })
        return {
            "daily_entries": daily_entries,
            "scheduled_hours": 0.0,
            "work_days_count": 0,
            "deviation": -target_hours
        }

    # Step 1: Choose base shift length (prefer whole-hour near 6h/12 units)
    whole_hour_shifts = sorted(
        [s for s in ALLOWED_SHIFTS if s not in ODD_SHIFTS],
        key=lambda s: abs(s - 12)
    )  # [12, 10, 14, 8, 16, 6, 4]

    best_shift = 12
    best_waste = float('inf')
    for s in whole_hour_shifts:
        n = max(1, round(target_units / s))
        waste = abs(target_units - s * n)
        if waste < best_waste:
            best_shift = s
            best_waste = waste
            if waste == 0:
                break

    # Determine initial target work days
    num_work_days = max(1, round(target_units / best_shift))
    
    # Clamp based on physical min/max shift limits
    # Max limit: each day can have at most 16 units (8h)
    num_work_days = max(int(math.ceil(target_units / 16.0)), num_work_days)
    # Min limit: each day must have at least 4 units (2h) (unless target is very small)
    if target_units >= 4:
        num_work_days = min(target_units // 4, num_work_days)
        
    # Enforce maximum feasible days within the month under 6-of-7 days rule
    max_feasible = min(num_days, int(num_days * 6.0 / 7.0) + 1)
    num_work_days = min(num_work_days, max_feasible)
    num_work_days = max(1, num_work_days)

    # Step 2: Select work days using deterministic-random swapping to introduce natural variety
    # First, generate mathematically even days as a starting feasible solution
    step = num_days / max(1, num_work_days)
    selected_indices = [int(i * step + step / 2) for i in range(num_work_days)]
    selected_days = set(min(idx + 1, num_days) for idx in selected_indices)

    # Enforce consecutive-day limit (max 6 in any 7-day window) to establish base validated list
    global_active = [0] * 6
    validated_days = []
    
    for d in range(1, num_days + 1):
        if d in selected_days:
            test_window = (global_active + [1])[-7:]
            if sum(test_window) <= 6:
                validated_days.append(d)
                global_active.append(1)
            else:
                global_active.append(0)
        else:
            global_active.append(0)

    # Backfill if filter dropped any days
    while len(validated_days) < num_work_days:
        added_any = False
        for d in range(1, num_days + 1):
            if d not in validated_days:
                temp_active = [0] * 6
                for day_idx in range(1, num_days + 1):
                    is_active = 1 if (day_idx in validated_days or day_idx == d) else 0
                    temp_active.append(is_active)
                
                valid = True
                for start_idx in range(len(temp_active) - 6):
                    if sum(temp_active[start_idx : start_idx + 7]) > 6:
                        valid = False
                        break
                
                if valid:
                    validated_days.append(d)
                    validated_days.sort()
                    added_any = True
                    break
        if not added_any:
            break

    # Perturb/Shuffle the day selection via random swaps to introduce natural layout patterns
    validated_set = set(validated_days)
    all_days = list(range(1, num_days + 1))
    
    for _ in range(300):
        if len(validated_set) < 2:
            break
        d_active = solver_rng.choice(list(validated_set))
        d_inactive = solver_rng.choice([d for d in all_days if d not in validated_set])
        
        # Test swap
        temp_set = (validated_set - {d_active}) | {d_inactive}
        
        temp_active = [0] * 6
        is_valid = True
        for day_idx in range(1, num_days + 1):
            is_active = 1 if day_idx in temp_set else 0
            temp_active.append(is_active)
            if sum(temp_active[-7:]) > 6:
                is_valid = False
                break
                
        if is_valid:
            validated_set = temp_set
            
    validated_days = sorted(list(validated_set))

    # Step 3: Distribute hours across selected days
    remaining = target_units
    day_hours = {}
    
    if validated_days:
        # Initialize all validated days with a baseline shift
        base_val = target_units // len(validated_days)
        base_val = max(4, min(16, base_val))
        
        for d in validated_days:
            day_hours[d] = base_val
            remaining -= base_val

        # Pass 2: Distribute positive remaining units one-by-one to days that have room (<16)
        if remaining > 0:
            for d in validated_days:
                if remaining <= 0:
                    break
                current = day_hours[d]
                add = min(16 - current, remaining)
                day_hours[d] = current + add
                remaining -= add

        # Pass 3: If we distributed too much (remaining < 0), subtract units from days (>4)
        if remaining < 0:
            for d in reversed(validated_days):
                if remaining >= 0:
                    break
                current = day_hours[d]
                sub = min(current - 4, abs(remaining))
                day_hours[d] = current - sub
                remaining += sub

        # Pass 4: Introduce daily shift length variety via random donations
        if len(validated_days) > 1:
            for _ in range(150):
                donor = solver_rng.choice(validated_days)
                receiver = solver_rng.choice(validated_days)
                if donor == receiver:
                    continue
                
                # Random transfer size: 1 to 6 units (0.5h to 3.0h)
                transfer = solver_rng.choice([1, 2, 3, 4, 5, 6])
                
                if day_hours[donor] - transfer >= 4 and day_hours[receiver] + transfer <= 16:
                    day_hours[donor] -= transfer
                    day_hours[receiver] += transfer

    # Step 3.5: Build start categories list from allowed options
    possible_categories = []
    if allow_morning:
        possible_categories.append('morning')
    if allow_afternoon:
        possible_categories.append('afternoon')
    if allow_evening:
        possible_categories.append('evening')

    # Fallback if none checked
    if not possible_categories:
        possible_categories = ['morning']

    # Fill categories patterns for round robin rotation
    category_patterns = []
    for i in range(num_work_days):
        category_patterns.append(possible_categories[i % len(possible_categories)])

    # Shuffle start patterns
    solver_rng.shuffle(category_patterns)

    # Step 4: Construct the complete daily entries dictionary list
    daily_entries = []
    scheduled_units_sum = 0
    work_days_count = 0

    for d in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{d:02d}"
        if d in day_hours and day_hours[d] > 0:
            h = day_hours[d]
            scheduled_units_sum += h
            
            # Get preferred start category
            category = 'morning'
            if work_days_count < len(category_patterns):
                category = category_patterns[work_days_count]
                
            work_days_count += 1
            
            # Determine daily randomized start time (within a 3.5-hour span in 30-min steps)
            offset_units = solver_rng.randint(0, 7)  # 0 to 7 units (0 to 3.5 hours)
            
            if category == 'morning':
                preferred_start = city_start + offset_units
            elif category == 'afternoon':
                preferred_start = city_start + 8 + offset_units
            else:  # 'evening'
                preferred_start = city_start + 16 + offset_units

            # Shifting rule: Shifts >= 6.5h (13 units) get 30-min break
            has_break = 1 if h >= 13 else 0
            total_span = h + has_break
            
            # Start shift at preferred time, shifting back if it exceeds closing time
            start = preferred_start
            if start + total_span > city_end:
                start = city_end - total_span
            start = max(city_start, start)
            
            end = start + total_span
            
            daily_entries.append({
                "work_date": date_str,
                "hours_worked": units_to_hours(h),
                "start_time": units_to_clock(start),
                "end_time": units_to_clock(end),
                "break_duration": "00:30" if has_break else "00:00",
                "remarks": ""
            })
        else:
            daily_entries.append({
                "work_date": date_str,
                "hours_worked": 0.0,
                "start_time": "",
                "end_time": "",
                "break_duration": "",
                "remarks": ""
            })

    scheduled_hours = units_to_hours(scheduled_units_sum)
    return {
        "daily_entries": daily_entries,
        "scheduled_hours": scheduled_hours,
        "work_days_count": work_days_count,
        "deviation": round(scheduled_hours - target_hours, 2)
    }
