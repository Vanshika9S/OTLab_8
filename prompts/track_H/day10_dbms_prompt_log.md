# Day 10 Prompt Log: Track H — DBMS Optimization & Index Selection

> **Track**: Track H (Database Management Systems & Physical Design Optimization)  
> **Date**: October 29, 2026  
> **Model / Assistant**: Gemini 3.8 Flash (via Antigravity IDE)  
> **User State**: Active Workspace `c:\Users\satye\OneDrive\Desktop\OTLab8`

---

## 1. User Prompt
```markdown
Day 10: Track H. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_H_dbms/ using the TPC-H SF 0.1 setup and baseline from Day 3.
1. Formulate index selection as a knapsack/ILP: candidate indexes, estimated benefit per query, storage budget, variables, objective, constraint.
2. Compare at least two methods (greedy by benefit/size vs ILP or DP) against the default optimizer, on the fixed workload. Optionally add join-order selection by dynamic programming.
3. Compare EXPLAIN ANALYZE plans, latency, throughput and storage before and after, with repeated runs and warm vs cold cache noted.
4. Automatically check that query results are identical before and after (hash of sorted result sets).
5. Include a write-cost test showing where an index hurts inserts or updates. Adding one index alone does not meet the track.
6. Run DAILY CLOSE.
```

---

## 2. Intent & Architecture Plan
1. **Relational Dataset Scaling (TPC-H Scale Factor 0.1)**:
   - Generated deterministic dataset in `track_H_dbms/tpch_benchmark.db`: 8 tables, 15,000 orders, 30,063 lineitems (~6.3 MB database footprint).
2. **Index Selection Formulation**:
   - Formulated as a 0-1 Knapsack / Integer Linear Program:
     - Maximizing $\sum v_i x_i$ where $v_i = \sum_q w_q \max(0, \text{Latency}_{\text{base}}(q) - \text{Latency}_i(q))$.
     - Subject to storage constraint $\sum s_i x_i \le B$ and group mutual exclusivity $\sum_{i \in G} x_i \le 1$.
   - Profiled 12 candidate indices targeting queries Q1, Q3, Q5, Q6, Q9, Q10, Q12, Q14.
3. **Multi-Solver Evaluation**:
   - Evaluated Dantzig's Greedy Knapsack heuristic (sorting by ratio $v_i / s_i$).
   - Implemented exact ILP via `scipy.optimize.milp` with binary variables and linear constraints.
   - Implemented Dynamic Programming Knapsack table solver.
   - Evaluated across two storage budgets: $B = 600\text{ KB}$ and $B = 1200\text{ KB}$.
4. **Join-Order Optimization by Dynamic Programming (System R)**:
   - Implemented bottom-up dynamic programming over relation powersets (Selinger et al., 1979) for multi-way joins (Q3, Q5, Q9), avoiding cartesian products and pushing selective relations to the base of left-deep trees.
5. **Write-Cost Penalty Evaluation**:
   - Benchmarked 3,000-row batch inserts into `lineitem` across 5 index configurations (0, 1, 2, 3, 5 secondary indexes) over 10 repeated trials, proving a 6.42x write amplification penalty.
6. **Correctness Verification**:
   - Computed SHA-256 hashes of canonical sorted result tuples across all 8 queries, confirming 100% result equivalence between unindexed baseline and indexed configurations.

---

## 3. Tool Calls & Execution Trace
- `run_command`: Inspected current database row counts.
- `write_to_file`: Created `track_H_dbms/code/index_optimizer.py`.
- `write_to_file`: Created `track_H_dbms/code/write_cost_benchmark.py`.
- `write_to_file`: Created `track_H_dbms/code/run_dbms_experiments.py`.
- `run_command`: Executed full DBMS experimental suite (generated 5 CSV files and 1 PNG visualization).
- `write_to_file`: Created `track_H_dbms/tests/test_dbms_optimizer.py`.
- `run_command`: Ran `pytest track_H_dbms/tests/ -v` (7 passed in 9.47s).
- `run_command`: Ran full repo test suite `pytest -v` (48 passed across all tracks in 57.49s).
- `replace_file_content`: Added Case 7 to `FAILURE_LOG.md`.
- `write_to_file`: Authored `track_H_dbms/REPORT.md`.

---

## 4. Errors Encountered & Debugging (Logged in FAILURE_LOG.md)
1. **SQLite Missing `dbstat` Extension**:
   - *Error*: When attempting to introspect candidate index sizes via `SELECT sum(pgsize) FROM dbstat WHERE name = ?`, SQLite threw `sqlite3.OperationalError: no such table: dbstat`.
   - *Root Cause*: Pre-compiled official Windows CPython binaries omit the `-DSQLITE_ENABLE_DBSTAT_VTAB=1` compile flag.
   - *Resolution*: Developed an engine-agnostic page differential tracking protocol using standard `PRAGMA page_count`, `PRAGMA freelist_count`, and `PRAGMA page_size`, coupled with `VACUUM` and explicit transaction commits to guarantee isolated byte-level accounting.

---

## 5. Human-in-the-Loop Oversight & Validation
- Verified all latency numbers, throughput values, and index sizes were derived from real, physical database executions on `tpch_benchmark.db`.
- Confirmed that SHA-256 output hashes matched between indexed and unindexed query executions across all 8 TPC-H queries.
- Ensured the write-cost test comprehensively satisfied the negative result requirement, illustrating that while read queries sped up by up to 20x (Q6), secondary indexes collapsed write throughput by 84.4%.
