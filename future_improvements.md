# Future Improvements & Solver Scaling Blueprint

This document outlines performance findings and the recommended architectural design for scaling the Driver Shift & Timesheet Distribution Solver to handle larger workforces (30+ drivers).

---

## 📈 Current Performance & Scaling Findings

We ran performance benchmarks on a 30-day month with a city operational window of **08:00 to 22:00** (28 half-hour slots per day), using a mix of target hours (ranging from 40 to 120 hours per driver):

### 1. Batch Mode (Globally Joint Optimization)
In batch mode, the solver optimizes all active drivers simultaneously to achieve the absolute best staggering and daily coverage.
- **5 workers**: Solved exactly in **10.48s** (0.00h deviation, max overlap of 1 driver).
- **10 workers**: Solved exactly in **10.84s** (0.00h deviation, max overlap of 4 drivers).
- **30+ workers**: **Timeout / Failed**. Because the search space and variable count grows quadratically with the number of drivers (exceeding 100,000 boolean and constraint variables), the solver cannot find/prove a feasible solution within the CP-SAT timeout limits (10 seconds per phase).

### 2. Incremental Mode (Consecutive 1-by-1 Optimization)
In incremental mode, the solver schedules one driver at a time, lock their shifts, and schedules the next driver around the existing coverage.
- **10 workers**: Solved exactly in **75.20s** (average 7.52s per driver, 0.00h deviation, max overlap of 2 drivers).
- **20 workers**: Solved exactly in **156.48s** (average 7.82s per driver, 0.00h deviation, max overlap of 5 drivers).
- **Scaling**: Scales infinitely without timeouts, but introduces a **"first-come, first-served"** bias: drivers scheduled first get optimal shift blocks, while drivers scheduled last get highly fragmented hours to satisfy staggering constraints.

---

## 🧠 Future Improvement Blueprint: Clustered Sequential Batching

To combine the global optimization benefits of Batch Mode with the infinite scalability of Incremental Mode, we recommend implementing **Clustered Sequential Batching** inside `sat_solver.py`.

### The Core Concept
If a batch solve request has more than **10 active drivers**, the solver will automatically partition them into clusters of 10. The solver will solve the first cluster, accumulate its coverage, add it to the background constraints (`existing_coverage`) for the next cluster, and solve the next one.

```
[All Active Drivers (e.g., 30)]
               │
               ▼ (Partition if N > 10)
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
[Group A (1-10)]  [Group B (11-20)]  [Group C (21-30)]
     │                 │                 │
     ▼ (Solve Batch)   │                 │
[Lock Group A] ────────┼─► (Solve Batch  │
                       ▼   w/ Group A)   │
                  [Lock Group B] ────────┼─► (Solve Batch
                                         ▼   w/ Group A & B)
                                    [Lock Group C]
```

### Proposed Code Implementation inside `solver/sat_solver.py`

Modify the `solve()` routine to inspect the input list:

```python
def solve(solver_input: SolverInput) -> SolverResult:
    # ... preprocessing ...

    # Check if batch mode requires partitioning
    if solver_input.mode == 'batch' and len(solver_input.drivers) > 10:
        return _solve_clustered_batches(solver_input)

    # ... existing single-batch solver code ...
```

Implement the clustering wrapper:

```python
def _solve_clustered_batches(solver_input: SolverInput) -> SolverResult:
    import copy
    
    # 1. Chunk drivers list into groups of 10
    chunk_size = 10
    driver_chunks = [solver_input.drivers[i:i + chunk_size] 
                     for i in range(0, len(solver_input.drivers), chunk_size)]
    
    # 2. Maintain running existing coverage and aggregated schedules
    running_coverage = copy.deepcopy(solver_input.existing_coverage)
    aggregated_schedules = {}
    total_deviation = 0.0
    total_solve_time = 0.0
    status_summary = 'exact'
    
    for idx, chunk in enumerate(driver_chunks):
        # Create input for this chunk
        chunk_input = SolverInput(
            drivers=chunk,
            city_start=solver_input.city_start,
            city_end=solver_input.city_end,
            num_days=solver_input.num_days,
            prev_month_boundary=solver_input.prev_month_boundary,
            cross_city_active=solver_input.cross_city_active,
            existing_coverage=running_coverage,  # pass accumulated coverage
            locked_entries=solver_input.locked_entries,
            mode='batch'
        )
        
        # Solve this chunk
        result = solve(chunk_input)
        total_solve_time += result.solve_time_seconds
        
        if result.status == 'failed':
            return SolverResult(status='failed', schedules={}, target_deviation=0.0, solve_time_seconds=total_solve_time)
            
        if result.status == 'nearest':
            status_summary = 'nearest'
            
        total_deviation += result.target_deviation
        
        # Merge schedules
        aggregated_schedules.update(result.schedules)
        
        # Accumulate coverage to running_coverage for the next group
        for emp_id, schedule in result.schedules.items():
            # Only accumulate if driver belongs to the solved group (ignore background locked entries)
            if any(d.employee_id == emp_id for d in chunk):
                for entry in schedule:
                    if entry.hours > 0.0:
                        st_slot = clock_to_units(entry.start_time)
                        et_slot = clock_to_units(entry.end_time)
                        for slot in range(st_slot, et_slot):
                            if entry.day not in running_coverage:
                                running_coverage[entry.day] = {}
                            running_coverage[entry.day][slot] = running_coverage[entry.day].get(slot, 0) + 1
                            
    return SolverResult(
        status=status_summary,
        schedules=aggregated_schedules,
        target_deviation=total_deviation,
        solve_time_seconds=total_solve_time
    )
```

### Advantages of This Design
1. **Seamless Integration**: The GUI and tests call `sat_solver.solve()` exactly as they do today. The partitioning is handled entirely within the solver engine, ensuring backward compatibility.
2. **Guaranteed Execution**: Solving three 10-worker batches sequentially takes only **~30 seconds** in total, preventing solver timeouts entirely while maintaining high-quality staggering.
3. **No Duplicate Logic**: Avoids complex async threading chaining in `main_gui.py`.
