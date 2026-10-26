# Track B: Discrete Optimization — Report

## 1. Objective
Solve discrete combinatorial problems (selection, scheduling, allocation) comparing exact methods (ILP, Branch-and-Bound, Dynamic Programming) against heuristics (Greedy selection). Formulate at least one problem as a QUBO/Ising model with quadratic penalty terms (e.g. Max-Cut or feature selection) solved classically to serve as the baseline for Track C.

## 2. Algorithms Tested
- **Greedy Heuristic**: Fast constructive heuristic.
- **Dynamic Programming (DP)**: Optimal substructure memoization/tabulation.
- **Branch-and-Bound / Integer Linear Programming (ILP)**: Exact branch-and-cut solving.
- **QUBO / Ising Formulation**: Quadratic Unconstrained Binary Optimization with penalty terms for constraints, solved via classical simulated annealing / exact state enumeration.

## 3. Baseline
Greedy selection or naive exhaustive search.

## 4. Fair Comparison Protocol
- Same problem instances across all solvers.
- Measure solution quality (objective cost), execution time, and constraint violation (if any).

## 5. Experimental Results & Verification
*(To be populated following approved test runs)*

## 6. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
