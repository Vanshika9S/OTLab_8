# Prompt Log: Track B — Day 5 (Discrete Optimization & QUBO/Ising)

## 1. Interaction Metadata
- **Date**: 2026-10-26
- **Tool / Assistant**: Gemini 3.8 Flash (High)
- **Track**: Track B (Discrete Optimization)
- **Milestone**: Day 5 — Knapsack Solvers (BruteForce, Greedy, DP, ILP, Branch-and-Bound), Max-Cut QUBO & Ising formulation, Constraint Penalties, Classical Solvers, and Export for Track C.

---

## 2. Original User Prompt
```text
Day 5: Track B. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_B_discrete/.
1. Pick a selection/allocation problem (knapsack or feature selection). Implement a naive baseline, greedy, dynamic programming, ILP (PuLP or OR-Tools) and my own Branch-and-Bound. Compare quality and runtime over growing sizes and verify against exact optima on small instances.
2. Formulate Max-Cut as QUBO and Ising: binary-to-spin conversion, and a worked example of penalty terms encoding a constraint (e.g. feature selection with a cardinality constraint, or a small scheduling constraint). Optionally convert a tiny timetabling instance from Track E to QUBO.
3. Solve classically: brute force on small graphs plus simulated annealing (10 seeds, mean and std). Save graphs, optimal values and solutions to results/ in a format Track C can load.
4. Tests: QUBO energy equals cut value, spin conversion round-trips, B&B equals brute force on small cases.
5. Run DAILY CLOSE.
```

---

## 3. Implementation Summary
1. Implemented all 5 knapsack solvers in [`track_B_discrete/code/knapsack_solvers.py`](../../track_B_discrete/code/knapsack_solvers.py):
   - `BruteForceKnapsack`: Exact $O(2^N)$ exhaustive search.
   - `GreedyKnapsack`: $O(N \log N)$ density ratio heuristic.
   - `DynamicProgrammingKnapsack`: $O(N \cdot W)$ 2D tabulation with solution backtracking.
   - `ILPKnapsack`: Exact branch-and-cut via SciPy HiGHS (`scipy.optimize.milp`).
   - `BranchAndBoundKnapsack`: Hand-written priority queue branch-and-bound with continuous/fractional relaxation upper bounds.
2. Formulated Max-Cut as QUBO and Ising in [`track_B_discrete/code/qubo_ising.py`](../../track_B_discrete/code/qubo_ising.py):
   - Proved $H_{\text{QUBO}}(x) = -\text{Cut}(x) = x^T Q x$.
   - Derived spin transformation $s_i = 1 - 2 x_i$ and verified $H_{\text{QUBO}}(x) = H_{\text{Ising}}(s) - 0.5 \sum w_{ij}$.
   - Implemented worked examples of quadratic penalty terms:
     - Cardinality constraint $\sum x_i = K \implies \lambda (\sum x_i - K)^2$.
     - Tiny Track E Exam Timetabling constraint mapped to 4-variable QUBO.
3. Solved classically:
   - Exact Brute Force on 5-node ring, 8-node cube, 12-node random graph.
   - Simulated Annealing across 10 repeated seeds (0..9) with mean ± std (100% success rate reaching ground state).
   - Exported instances and exact solutions to [`track_B_discrete/results/qubo_instances.json`](../../track_B_discrete/results/qubo_instances.json) formatted for Track C QAOA.
4. Wrote 6 unit tests in [`track_B_discrete/tests/test_discrete_solvers.py`](../../track_B_discrete/tests/test_discrete_solvers.py). All 6 pass.
5. Authored comprehensive report in [`track_B_discrete/REPORT.md`](../../track_B_discrete/REPORT.md).

---

## 4. Verification & Correctness Notes
- Branch-and-Bound solved $N=20$ knapsack in **0.25 ms** finding the exact optimum 738, identical to Brute Force (which took 1,638.59 ms).
- Dynamic Programming and ILP verified exact 100% optimality across small instances.
- QUBO energy confirmed exactly equal to $-\text{Cut}(x)$ across all binary states.
- Spin round-trip verified identity $x \to s \to x$.
