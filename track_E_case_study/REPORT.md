# Track E: Main Real-Process Case Study — Report
## University Examination Timetabling Optimization

> **Status**: Baseline Established & Inefficiency Documented  
> **Course**: Optimization Techniques (Assignment 8)  
> **Problem Domain**: University Educational Operations & Timetabling  
> **Full Formulation**: See [`FORMULATION.md`](./FORMULATION.md)  
> **Dataset Documentation**: See [`data/DATASET_DOCUMENTATION.md`](./data/DATASET_DOCUMENTATION.md)

---

## 1. Problem Statement & Inefficiency Discovery

University examination scheduling is an NP-hard combinatorial problem. An institution must allocate $|E|$ examinations for $|U|$ enrolled students into $|S|$ available time slots partitioned across $|D|$ calendar days, subject to venue seating capacity $C_{\text{max}}$.

Uncoordinated manual scheduling or naive greedy allocation causes severe structural failures:
1. **Direct Schedule Clashes**: Students are double-booked for two or more examinations in the exact same time slot.
2. **Academic Fatigue & Stress**: Students are forced into consecutive examinations on the same day (back-to-back) or scheduled for 3 or more examinations in a single 24-hour day.
3. **Venue Underutilization / Bloat**: Active slots are used inefficiently, inflating campus proctoring labor, heating, and facility overhead.

---

## 2. Experimental Baseline Setup

All experiments were executed on the primary reference synthetic dataset:
- **Instance**: `synthetic_primary_300.json` (300 students, 40 courses, 12 slots across 4 days, 3 slots/day).
- **Venue Capacity**: 300 seats per slot ($C_{\text{max}} = 300$).
- **Conflict Graph**: 740 conflict edges out of 780 possible (graph density = 0.9487).
- **Repetitions**: 10 repeated runs across fixed deterministic seeds ($0, 1, 2, \dots, 9$).
- **Evaluation Engine**: Fully decoupled independent [`validator.py`](./code/validator.py).
- **Label**: `[Hardware-Measured]` on local CPU.

---

## 3. Baseline Results (10 Seeds: Mean ± Std)

| Evaluation Metric | Target / Unit | Baseline 1: Random Schedule | Baseline 2: Greedy First-Fit |
| :--- | :--- | :--- | :--- |
| **Feasibility Rate** | 100% | **0.0% ± 0.0%** (0 / 10 feasible) | **0.0% ± 0.0%** (0 / 10 feasible) |
| **Hard Student Clashes** | 0 clashes | **218.10 ± 35.41** (Min: 162, Max: 287) | **120.20 ± 9.05** (Min: 105, Max: 134) |
| **Capacity Violations** | 0 slots | 0.10 ± 0.30 slots | **0.00 ± 0.00 slots** |
| **Back-to-Back Count ($Z_{\text{b2b}}$)** | Minimize | 348.50 ± 53.60 pairs | 364.70 ± 23.82 pairs |
| **3+ Exams in a Day ($Z_{\ge 3}$)** | 0 occurrences | 146.40 ± 26.08 students | 113.50 ± 10.48 students |
| **Active Slots Utilized** | Minimize | 11.80 ± 0.60 slots | 12.00 ± 0.00 slots |
| **Overall Objective Penalty ($Z$)** | Minimize | 10,864.00 ± 1,767.51 | **9,382.00 ± 712.81** |
| **Wall-Clock Solve Time** | Milliseconds | **0.014 ± 0.003 ms** | 0.453 ± 0.244 ms |

### Generated Plot
The empirical comparison plot is saved at:
[`results/baseline_inefficiency_comparison.png`](./results/baseline_inefficiency_comparison.png)

---

## 4. Evidence That the Process Needs Optimization (Question 1)

These hardware-measured results provide concrete, indisputable evidence of process failure:
1. **Zero Feasibility**: Neither baseline produced a single valid timetable across all 10 independent trials.
2. **Massive Clashes**: Greedy First-Fit produced an average of **120.2 student exam clashes**. This means over 120 times, a student would be physically double-booked into two concurrent exam rooms.
3. **Severe Student Overload**: Over 113 student-day instances involved students taking $\ge 3$ exams in a single calendar day, alongside 364 consecutive exam sessions.
4. **Conclusion**: Greedy constructive orderings cannot navigate dense conflict networks ($density \approx 0.95$). Exact mathematical programming (ILP) and metaheuristics (Simulated Annealing) are strictly required.

---

## 5. Next Steps for Track E
- Day 11: Implement exact **Integer Linear Programming (ILP)** via PuLP/CBC to eliminate all 120+ clashes and achieve 100% feasibility.
- Implement **Simulated Annealing with Kempe Chain Swaps** to compare exact vs metaheuristic trade-offs on the scaling benchmark suite (100 to 3,000 students).
