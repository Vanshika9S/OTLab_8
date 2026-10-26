# Track H: DBMS Optimization — Report

## 1. Objective & Task Formulation
Optimize a relational database workload on an engine (SQLite / PostgreSQL / DuckDB) using formal Chapter 6 optimization methods:
- **Optimization Task**: Index selection formulated as a Knapsack / ILP problem under storage budget constraints, and/or multi-way Join-Order Optimization comparing Dynamic Programming (System R style) vs Greedy heuristics.
- **Formulation**: Formulate index selection with binary variables $y_i \in \{0, 1\}$ indicating whether index $i$ is built, maximizing workload cost reduction $\sum_q w_q \Delta C_q(y)$ subject to total index storage $\sum_i s_i y_i \le B$.

## 2. Dataset & Workload
Documented synthetic benchmark / TPC-H subset (scale factor 0.05 - 0.1) with defined multi-table join and aggregation queries.

## 3. Fair Comparison Protocol
- Compare default optimizer behavior (no secondary indices or default join tree) vs Greedy index selection vs ILP optimal index selection.
- Extract `EXPLAIN` and `EXPLAIN QUERY PLAN` / execution metrics.
- Verify that query results are identical across all configurations.

## 4. Experimental Results & Verification
*(To be populated following approved test runs)*

## 5. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
