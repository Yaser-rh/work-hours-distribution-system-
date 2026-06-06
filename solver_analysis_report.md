# Solver Engine Analysis Report

## Executive Summary

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Correctness** | ⭐⭐⭐⭐⭐ 10/10 | All hard constraints (consecutive-day, cross-city, breaks, city window) are modeled flawlessly |
| **Approach Choice** | ⭐⭐⭐⭐ 8/10 | CP-SAT is a strong fit for this problem class; well-justified |
| **Model Quality** | ⭐⭐⭐ 6/10 | The `covers_var` auxiliary explosion is the critical bottleneck |
| **Scalability** | ⭐⭐ 4/10 | Variable count grows as O(W × D × S), causing the 180s convergence issue |
| **Objective Design** | ⭐⭐⭐ 6/10 | Multi-objective weights are reasonable but fight each other, slowing convergence |
| **Code Quality** | ⭐⭐⭐⭐ 8/10 | Clean structure, good separation of concerns, well-documented |
| **Overall** | ⭐⭐⭐½ | **7/10** — Correct and well-structured, but the model is too large for fast convergence |

---

## 1. Problem Classification

Your problem is a **multi-driver shift scheduling problem** with:
- Fixed monthly hour targets per driver
- A discrete time grid (30-min slots)
- Labor law constraints (max 6 consecutive workdays)
- Coverage/staggering quality objectives
- Multi-city awareness

This falls into the category of **Nurse Rostering / Employee Scheduling Problems (NRP/ESP)**, which are known to be **NP-hard**. Your formulation is essentially a hybrid of:

1. **Workforce scheduling** (assigning shifts to employees)
2. **Coverage optimization** (ensuring time slots are staffed)
3. **Fairness/distribution** (spreading work evenly)

---

## 2. Model Size Analysis — The Root Cause of 180s

### Variable Count Explosion

For a typical scenario of **W=5 drivers**, **D=30 days**, **S=28 slots** (08:00–22:00):

| Variable Type | Count Formula | Count (5 drivers) | Count (10 drivers) |
|---------------|---------------|--------------------|--------------------|
| `active_var[w,d]` | W × D | 150 | 300 |
| `hours_var[w,d]` | W × D | 150 | 300 |
| `start_var[w,d]` | W × D | 150 | 300 |
| `end_var[w,d]` | W × D | 150 | 300 |
| `break_var[w,d]` | W × D | 150 | 300 |
| `is_half_var[w,d]` | W × D | 150 | 300 |
| `is_long[w,d]` | W × D | 150 | 300 |
| **`covers_var[w,d,t]`** | **W × D × S** | **4,200** | **8,400** |
| `after_start[w,d,t]` | W × D × S | 4,200 | 8,400 |
| `before_end[w,d,t]` | W × D × S | 4,200 | 8,400 |
| `slot_dev[d,t]` | D × S | 840 | 840 |
| `daily_dev[d]` | D | 30 | 30 |
| `uncovered[d,t]` | D × S | 840 | 840 |
| **Total Variables** | | **~15,360** | **~28,770** |

> [!CAUTION]
> **The `covers_var`, `after_start`, and `before_end` variables alone account for 82% of all variables.** These are created for every (driver × day × slot) triple and are the primary reason the model is slow. Each `covers_var` also requires 4 boolean implications (the `AddBoolAnd` / `AddBoolOr` channeling constraints), multiplying the constraint count.

### Constraint Count

| Constraint Type | Count Formula | Count (5 drivers) |
|-----------------|---------------|-------------------|
| Channeling for `covers_var` | 4 × W × D × S | **16,800** |
| Active ↔ Hours linking | 2 × W × D | 300 |
| Break logic | 4 × W × D | 600 |
| City window bounds | 4 × W × D | 600 |
| End time derivation | W × D | 150 |
| Half-hour domain | 2 × W × D | 300 |
| Consecutive-day sliding window | W × ~30 | 150 |
| Weekly limits | W × ~25 × 2 | 250 |
| Hourly smoothing deviation | 2 × D × S | 1,680 |
| Daily distribution deviation | 2 × D | 60 |
| Batch max-coverage | D × S | 840 |
| Uncovered slot | D × S | 840 |
| **Total Constraints** | | **~22,570** |

For 10 drivers, this balloons to **~40,000+ constraints**.

### Why 180 Seconds?

The solver finds a **feasible** solution quickly (usually in < 2s), but that first solution has a poor objective value. The multi-objective function has **competing penalties**:

```
Minimize:  1·half_hour + 10·stagger + 10·daily_dist + 5·hourly_smooth + 10000·uncovered
```

- The solver prioritizes `uncovered` (weight 10,000) first, then slowly improves `daily_dist` and `hourly_smooth`
- Improving one penalty often worsens another (e.g., spreading hours evenly across days may create worse hourly coverage variance)
- CP-SAT's branch-and-bound needs to explore many branches to prove that a solution with lower objective exists
- The **`relative_gap_limit = 0.00`** setting demands mathematical proof of optimality, which is extremely expensive for this model size

**In short: the model is correct but over-specified. It has too many auxiliary variables that create a huge search space, and the zero-gap requirement forces exhaustive exploration.**

---

## 3. Comparison with Alternative Algorithms

### 3.1 Integer Linear Programming (ILP) — e.g., Gurobi, CPLEX

| Aspect | Your CP-SAT | ILP (Gurobi/CPLEX) |
|--------|-------------|---------------------|
| **Modeling** | Boolean channeling for coverage tracking | Same model, but LP relaxation gives tighter bounds |
| **Bound Quality** | CP-SAT's LP relaxation is weaker for scheduling | Commercial ILP solvers have cutting planes tuned for scheduling |
| **Speed** | 180s for even heatmap | Likely **30–60s** for same quality (better LP bounds → faster pruning) |
| **Cost** | Free (OR-Tools) | $$$$ (commercial licenses) |
| **Verdict** | CP-SAT is the right free choice | Would be faster but not worth the cost for this problem size |

> [!NOTE]
> CP-SAT internally uses a portfolio approach (LP relaxation + SAT + LNS). For pure integer problems, commercial solvers like Gurobi have stronger LP relaxations and cutting planes. However, your problem has enough combinatorial structure that CP-SAT is a reasonable choice.

### 3.2 Column Generation

Used in airline crew scheduling (the gold standard for large-scale shift problems).

| Aspect | Your CP-SAT | Column Generation |
|--------|-------------|-------------------|
| **Approach** | Monolithic: all variables at once | Decomposed: master problem picks shifts, subproblem generates new shift patterns |
| **Scalability** | O(W × D × S) variables | Only considers "promising" shift patterns; far fewer variables |
| **Speed** | 180s | Typically **5–20s** for similar problems |
| **Implementation** | Simple, single model | Complex: requires master LP + pricing subproblem loop |
| **Fit for your problem** | ✅ Works | ⚠️ Overkill — designed for 100+ employees and 1000+ shifts |

> [!IMPORTANT]
> Column generation is the **theoretically superior** approach for employee scheduling. But it requires significant implementation effort (Dantzig-Wolfe decomposition). For < 20 drivers, the overhead isn't justified.

### 3.3 Simulated Annealing (SA)

| Aspect | Your CP-SAT | Simulated Annealing |
|--------|-------------|---------------------|
| **Guarantees** | Proves optimality (with enough time) | No optimality proof; heuristic |
| **Constraint handling** | Native hard constraints | Must encode as penalties or repair operators |
| **Coverage quality** | Optimal (given time) | Good but unpredictable; depends on cooling schedule |
| **Speed to "good" solution** | 180s | **5–30s** for comparable quality |
| **Consecutive-day constraint** | Perfect enforcement | Hard to enforce without rejection/repair |
| **Verdict** | Better correctness guarantees | Faster but no guarantee of constraint satisfaction |

### 3.4 Genetic Algorithms (GA) — e.g., NSGA-II

| Aspect | Your CP-SAT | Genetic Algorithm |
|--------|-------------|-------------------|
| **Multi-objective** | Scalarized (weighted sum) | True Pareto front (NSGA-II) — user picks preferred trade-off |
| **Speed** | 180s for convergence | 10–60s depending on population size |
| **Constraint handling** | Perfect | Requires penalty functions or repair operators |
| **Reproducibility** | Deterministic | Stochastic |
| **Verdict** | Simpler, more reliable | Better for exploring trade-offs, but weaker on hard constraints |

### 3.5 Greedy Construction Heuristic + Local Search

| Aspect | Your CP-SAT | Greedy + Local Search |
|--------|-------------|----------------------|
| **Speed** | 180s | **< 1 second** |
| **Quality** | Optimal | 80–90% of optimal |
| **Approach** | Global optimization | Build initial solution greedily, then swap/move shifts |
| **Constraint handling** | Perfect | Easy to enforce during construction |
| **Verdict** | Much better quality | Dramatically faster; good for real-time previews |

> [!TIP]
> A **two-phase approach** (greedy warm-start → CP-SAT polish) could give you the best of both worlds. The CP-SAT solver accepts solution hints, so a greedy solution could be fed in as a starting point, dramatically cutting convergence time.

### 3.6 Large Neighborhood Search (LNS)

| Aspect | Your CP-SAT | Standalone LNS |
|--------|-------------|----------------|
| **Approach** | CP-SAT uses LNS internally as one worker | Dedicated LNS with problem-specific destroy/repair |
| **Speed** | 180s (generic LNS) | **10–30s** (domain-specific neighborhoods) |
| **Key idea** | — | Freeze most drivers, re-optimize 2–3 at a time |
| **Verdict** | Already partially used internally | Custom LNS would be faster for batch scenarios |

### 3.7 Two-Stage Decomposition (Recommended for Your Case)

| Stage | What it does | Time |
|-------|-------------|------|
| **Stage 1: Day Assignment** | Assign which days each driver works (binary), respecting consecutive-day limits and daily hour targets | ~2s |
| **Stage 2: Time Placement** | For each day, assign start times to minimize coverage variance (much smaller per-day problem) | ~1s per day, parallelizable |

| Aspect | Your CP-SAT | Two-Stage |
|--------|-------------|-----------|
| **Speed** | 180s | **5–15s total** |
| **Quality** | Global optimum | Near-optimal (slight loss from decomposition) |
| **Complexity** | O(W × D × S) | Stage 1: O(W × D), Stage 2: O(W × S) per day |
| **Key benefit** | — | Eliminates the W × D × S variable explosion |

---

## 4. Summary Comparison Matrix

| Algorithm | Speed | Quality | Constraint Safety | Implementation Effort | Best For |
|-----------|-------|---------|-------------------|-----------------------|----------|
| **Your CP-SAT** | ⭐⭐ (180s) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Already built | Correctness-critical, < 5 drivers |
| ILP (Gurobi) | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Same but faster, requires license |
| Column Generation | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 50+ drivers, airline-scale |
| Simulated Annealing | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | Quick good solutions, no guarantees |
| Genetic Algorithm | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Multi-objective exploration |
| Greedy + Local Search | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Real-time previews, warm starts |
| **Two-Stage Decomposition** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **Best fit for your problem** |
| Custom LNS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Improving existing solutions |

---

## 5. Specific Bottlenecks in Your Code

### 5.1 The `covers_var` Explosion (Lines 323–335)

```python
for t in range(city_start, city_end):        # 28 iterations
    after_start = model.NewBoolVar(...)       # +1 var
    model.Add(start_var[w,d] <= t)...         # +2 constraints
    before_end = model.NewBoolVar(...)        # +1 var
    model.Add(end_var[w,d] >= t+1)...         # +2 constraints
    c_var = model.NewBoolVar(...)             # +1 var
    model.AddBoolAnd(...)                     # +2 constraints
    covers_var[w, d, t] = c_var
```

**Per (driver, day): 28 × 3 = 84 auxiliary booleans + 28 × 6 = 168 constraints.**
**Total for 5 drivers × 30 days: 12,600 booleans + 25,200 constraints — just for coverage tracking.**

This is the single biggest contributor to slow convergence.

### 5.2 Zero Relative Gap (Line 192)

```python
solver_a.parameters.relative_gap_limit = 0.00
```

This means CP-SAT won't stop until it **proves** the current solution is optimal. For a model this size, proving optimality can take orders of magnitude longer than finding a near-optimal solution. A gap of 0.01–0.05 (1–5%) would let the solver stop much sooner with a solution that's visually indistinguishable.

### 5.3 Competing Objectives

The five penalty terms pull in different directions:

```
uncovered (δ=10000) vs. daily_dist (η=10) vs. hourly_smooth (θ=5)
```

- **Uncovered slots** wants every slot covered → drives towards many short shifts
- **Daily distribution** wants equal hours per day → drives towards uniform daily totals
- **Hourly smoothing** wants equal coverage per slot → drives towards identical shift patterns
- **Half-hour penalty** wants whole-hour shifts → may conflict with exact target matching

The solver must explore trade-offs between these, which creates a "plateau" in the objective landscape where many solutions have similar total cost but different distributions. This is why the heatmap only "evens out" after 180s — the solver is slowly improving the smoothing terms.

### 5.4 Batch Staggering is Over-Constrained (Lines 417–428)

The batch mode creates a `max_cov[d]` variable per day and adds `S` constraints per day. But `max_cov` is a **minimax** formulation (minimize the maximum), which is known to be harder for CP-SAT than minimize-sum formulations. This adds difficulty to the search.

---

## 6. Actionable Optimization Recommendations

Ranked by **impact vs. effort**:

### 🔴 High Impact, Low Effort

| # | Change | Expected Speedup | Effort |
|---|--------|-------------------|--------|
| 1 | **Set `relative_gap_limit = 0.02`** (2% gap) | 3–5× faster | 1 line change |
| 2 | **Add solution hints** from a greedy pre-solve | 2–4× faster | ~50 lines of code |
| 3 | **Reduce slot granularity to 1 hour** for coverage tracking (keep 30-min for shift lengths) | 4× fewer coverage vars | Moderate refactor of `covers_var` |

### 🟡 High Impact, Medium Effort

| # | Change | Expected Speedup | Effort |
|---|--------|-------------------|--------|
| 4 | **Two-stage decomposition**: separate day-assignment from time-placement | 10–20× faster | New architecture (~200 lines) |
| 5 | **Replace `covers_var` with interval variables** using `AddNoOverlap` / cumulative constraints | 3–5× fewer variables | Significant refactor |
| 6 | **Use CP-SAT's `NewIntervalVar`** for shifts instead of manual start/end/covers channeling | Cleaner model, better propagation | Medium refactor |

### 🟢 Medium Impact, Low Effort

| # | Change | Expected Speedup | Effort |
|---|--------|-------------------|--------|
| 7 | **Replace `hourly_smoothing` with a sampled version** (check every 3rd slot instead of every slot) | ~2× fewer smoothing vars | Small change |
| 8 | **Use `AddDecisionStrategy`** to prioritize branching on `active_var` first, then `hours_var` | Better early solutions | ~5 lines |
| 9 | **Increase `num_search_workers` to 16** if the machine has cores available | ~1.5× | 1 line |

---

## 7. Verdict

**Your algorithm is a solid, correct implementation.** CP-SAT is the right tool for this problem class, and all the constraints are modeled correctly. The architecture (two-phase solve, locked/active separation, batch/incremental modes) shows strong engineering.

The **180-second convergence issue** is not a fundamental algorithm problem — it's a **model size problem** caused by the `covers_var` auxiliary variable explosion. The coverage tracking creates O(W × D × S) boolean variables with 6 channeling constraints each, making the search space enormous.

> [!IMPORTANT]
> **The fastest win**: Change `relative_gap_limit` from `0.00` to `0.02` and add a greedy warm-start hint. These two changes alone would likely bring convergence to an even heatmap from 180s down to **30–45s** with no loss in perceived quality.

For a more fundamental speedup, the **two-stage decomposition** (day assignment → time placement) would reduce the problem to two much smaller models that solve in seconds, at the cost of a small quality trade-off that would be invisible in practice.
