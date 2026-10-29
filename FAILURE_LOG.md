# FAILURE LOG: AI Mistakes, Unsafe Logic, and Corrections

Per Section 8 of the assignment specification, this document records cases where AI-generated code was wrong, unsafe, inefficient, or misleading. At least three documented cases are required, detailing the exact manifestation, root cause, verified fix, and lesson learned.

---

## Log Schema

Each entry must document:
1. **Track & Component**: Track identifier and subsystem.
2. **AI Tool & Model**: Prompting assistant used.
3. **Prompt & AI Output Description**: What was asked and what faulty code was generated.
4. **Issue Classification**: `[Correctness Failure]`, `[Unsafe Kernel/System State]`, `[Inefficiency/Scalability]`, or `[Subtle Mathematical Flaw]`.
5. **Why It Failed / Root Cause**: Deep technical explanation of the failure mode.
6. **The Verified Fix**: The human-verified resolution and resulting diff/code.
7. **The Key Lesson**: Permanent guideline derived from the failure.

---

## Case 1: Standalone Script Module Import Path Failure

- **Track & Component**: Track E (Main Case Study — `baselines.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Correctness Failure / Execution Incompatibility]`
- **Description & Output**: The AI-generated script `baselines.py` included the statement:
  ```python
  from track_E_case_study.code.validator import TimetableValidator
  ```
  When executed directly from the terminal via `python track_E_case_study/code/baselines.py`, the interpreter threw:
  `ModuleNotFoundError: No module named 'track_E_case_study'`.
- **Root Cause**: When a Python file is run directly as a script, Python initializes `sys.path[0]` to the script's directory (`track_E_case_study/code/`), not the repository root directory. The package name `track_E_case_study` was therefore invisible to the runtime.
- **Verified Fix**: Bootstrapped `sys.path` dynamically prior to module imports:
  ```python
  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  if REPO_ROOT not in sys.path:
      sys.path.insert(0, REPO_ROOT)
  ```
- **Key Lesson**: In multi-directory repositories, never assume the caller runs scripts via `python -m package.module` or has `PYTHONPATH=.` set. Every executable script must explicitly bootstrap the workspace root into `sys.path`.

---

## Case 2: Unicode Encoding Failure in Quantum Circuit ASCII Rendering on Windows

- **Track & Component**: Track C / Track I (`smoke_test_bell.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Platform Compatibility / Crash]`
- **Description & Output**: Calling `print(qc.draw(output="text"))` threw:
  `UnicodeEncodeError: 'charmap' codec can't encode characters in position 5-9: character maps to <undefined>`.
- **Root Cause**: On Windows systems, standard terminal stdout defaults to legacy `cp1252` encoding rather than UTF-8. Qiskit's text circuit drawer uses UTF-8 box-drawing characters (`┌`, `─`, `■`, `╫`), which fail to encode in `cp1252`.
- **Verified Fix**: Reconfigured `sys.stdout` to UTF-8 dynamically with a guarded fallback:
  ```python
  if hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8")
  ```
- **Key Lesson**: Console outputs containing Unicode symbols, box-drawing characters, or math symbols must always guard for Windows legacy codepages or force UTF-8 stdout reconfiguration.


---

## Case 3: Missing Inter-Table Join Population in Synthetic Database Generator

- **Track & Component**: Track H (DBMS Optimization — `tpch_benchmark_harness.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Subtle Data Generation Flaw]`
- **Description & Output**: While the database schema declared 8 tables, `populate_synthetic_tpch` populated `part` and `supplier` but completely omitted `partsupp`. As a result, unit test `test_schema_and_tables_exist` failed with:
  `AssertionError: Table partsupp is empty`.
  Furthermore, multi-table join Query Q9 (`WHERE s_suppkey = l_suppkey AND ps_suppkey = l_suppkey AND ps_partkey = l_partkey AND p_partkey = l_partkey`) returned 0 rows.
- **Root Cause**: The AI generated data for the principal entities but missed the intermediate associative table `partsupp`, assuming standard lineitems would be sufficient.
- **Verified Fix**: Implemented explicit relational generation of `partsupp` linking 2–4 suppliers per part with synthetic `availqty` and `supplycost`.
- **Key Lesson**: Always write unit tests verifying table row counts and non-empty query result sets when generating synthetic database benchmarks. Do not assume joins will succeed without explicit associative records.

---

## Case 4: Global Pytest Module Collection Failure across Multi-Track Repositories

- **Track & Component**: Root Test Harness (`pytest` test collection across Tracks A–J)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Environment & Test Harness Incompatibility]`
- **Description & Output**: Running `pytest -v` from the repository root produced fatal collection errors:
  `ERROR collecting track_A_continuous/tests/test_continuous_optimizers.py`
  `ModuleNotFoundError: No module named 'track_A_continuous'`
  `ERROR collecting track_B_discrete/tests/test_discrete_solvers.py`
  `ModuleNotFoundError: No module named 'track_B_discrete'`
- **Root Cause**: When pytest discovers test files in subdirectories, it imports each test module into Python's module cache. Because test files had `from track_A_continuous.code... import ...` at the top of the file *before* or without a root-level hook, Python could not resolve the package root unless `PYTHONPATH=.` was passed in the environment.
- **Verified Fix**: Created a root-level [`conftest.py`](./conftest.py) and [`pytest.ini`](./pytest.ini):
  ```ini
  [pytest]
  pythonpath = .
  testpaths = track_A_continuous/tests track_B_discrete/tests track_C_quantum/tests track_E_case_study/tests track_H_dbms/tests track_J_software_eng/tests
  ```
- **Key Lesson**: In multi-module monorepos, individual script bootstrapping (`sys.path.insert`) is necessary for direct script runs, but pytest requires a root `conftest.py` or `pytest.ini` configuration to guarantee consistent cross-platform module discovery.

---

## Case 5: Pytest Test Discovery Naming Collision on Subsystem Helper Functions

- **Track & Component**: Track D (Submodular Optimization — `submodular_opt.py` & `test_parallel_distributed.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Test Discovery & Fixture Resolution Failure]`
- **Description & Output**: Running `pytest -v` caused a collection/setup error:
  `ERROR at setup of test_diminishing_returns`
  `file submodular_opt.py:87: fixture 'obj' not found`
- **Root Cause**: The library function was named `def test_diminishing_returns(obj, num_trials=500, ...)`. When imported into the test module via `from track_D_submodular_parallel.code.submodular_opt import test_diminishing_returns`, pytest's default collector matched the `test_*` pattern, concluded that `test_diminishing_returns` was a test case rather than a library helper, and attempted to resolve the argument `obj` as a pytest fixture.
- **Verified Fix**: Renamed the helper function to `check_diminishing_returns` across the codebase, reserving the `test_*` prefix strictly for zero-argument or fixture-backed test cases.
---

## Case 6: Unsound Linear Liveness in Dead-Code Elimination and LICM Causing Infinite Loops

- **Track & Component**: Track F (Compiler Optimization — `optimizer.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Correctness Failure / Semantic Corruption]`
- **Description & Output**: During the optimization of `Prog3_LICM_Loop`, the VM interpreter entered an infinite loop, aborting with:
  `RuntimeError: Program exceeded maximum cycle limit (500000)`.
  Inspection of the optimized Three-Address Code (TAC) revealed that the loop variable update `i = i + 1` had been completely eliminated by the Dead-Code Elimination (DCE) pass, and the loop conditional header `t0 = i < 10` had been hoisted outside the loop as an invariant constant condition `1`.
- **Root Cause**: The initial implementation used a naive single-pass linear backward scan across the instruction sequence to compute variable liveness. Because the scan traversed instructions top-to-bottom/bottom-to-top without constructing a Control Flow Graph (CFG), it failed to propagate liveness across the loop back-edge (`JUMP $L_header`). As a result, the variable `i` appeared unread after the end of the loop, marking `i = i + 1` as dead code. Once the increment was removed, LICM observed that `i` was never modified within the loop body and incorrectly hoisted the loop termination test outside the loop header, locking the program in an infinite cycle.
- **Verified Fix**: Replaced the linear liveness heuristic with formal basic-block Control Flow Graph (CFG) partitioning and iterative backward dataflow analysis. Computed predecessors, successors, and solved the fixed-point equations:
  $$\text{IN}[B] = \text{USE}[B] \cup (\text{OUT}[B] \setminus \text{DEF}[B])$$
  $$\text{OUT}[B] = \bigcup_{S \in \text{SUCC}[B]} \text{IN}[S]$$
  Iterating until convergence ensured variables live across loop back-edges are preserved. LICM was also hardened to verify all loop-carried dependencies before hoisting.
---

## Case 7: SQLite Index Storage Introspection Failure via Missing dbstat Virtual Table

- **Track & Component**: Track H (DBMS Optimization — `index_optimizer.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Platform / Environment Introspection Failure]`
- **Description & Output**: When profiling candidate index storage costs, querying SQLite's standard storage diagnostic table via `SELECT sum(pgsize) FROM dbstat WHERE name = ?` threw:
  `sqlite3.OperationalError: no such table: dbstat`.
- **Root Cause**: The `dbstat` virtual table is an optional SQLite extension requiring compile-time flag `-DSQLITE_ENABLE_DBSTAT_VTAB=1`. Standard official CPython Windows binary distributions omit this flag, causing database storage introspection queries to fail catastrophically.
- **Verified Fix**: Replaced the `dbstat` dependency with an engine-agnostic page differential tracking protocol using standard SQLite pragmas:
  $$\Delta \text{Pages} = (\text{PageCount}_{\text{after}} - \text{PageCount}_{\text{before}}) + (\text{Freelist}_{\text{before}} - \text{Freelist}_{\text{after}})$$
  $$\text{Storage (Bytes)} = \Delta \text{Pages} \times \text{PageSize}$$
  coupled with `VACUUM` and explicit transaction commits (`conn.commit()`) between candidates to guarantee isolated, deterministic byte-level accounting.
---

## Case 8: Dense Matrix Memory Explosion in ILP Constraint Generation for Conflict Graphs

- **Track & Component**: Track E (Timetabling Optimization — `optimizers.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Inefficiency / Memory Explosion / Scalability Failure]`
- **Description & Output**: During the execution of the ILP timetabling benchmark on the primary instance (40 courses, 740 conflicts, 12 slots), Python processes locked the CPU in heavy garbage collection and memory allocation loops, taking $> 30$ seconds per solve before timing out.
- **Root Cause**: The constraint generation routine constructed a dense NumPy array `np.zeros(total_vars)` for each of the $8,932$ linear constraints. Across $9,372$ variables (including continuous conflict slack variables), this instantiated an $8,932 \times 9,372$ dense `float64` matrix consuming over $670\text{ MB}$ of RAM per single ILP invocation ($> 6.7\text{ GB}$ across 10 repeated trials). Because only $\sim 27,000$ matrix entries were non-zero (sparsity $> 99.96\%$), allocating and passing dense arrays to HiGHS caused catastrophic allocation latency.
- **Verified Fix**: Replaced dense matrix accumulation with `scipy.sparse.coo_matrix` converted to `csr_matrix`. Row, column, and coefficient values are accumulated into lightweight Python lists and assembled in $15.7\text{ ms}$ ($< 1\text{ MB}$ footprint), enabling HiGHS to solve or prove infeasibility in $< 900\text{ ms}$.
- **Key Lesson**: In discrete optimization models over dense graphs, never construct dense NumPy arrays for constraint matrices. Always construct sparse matrices (`scipy.sparse.csr_matrix` / `coo_matrix`) when non-zero coefficient density is below $5\%$.
---

## Case 9: Grover Amplitude Over-Rotation from Naive Rounding in Iteration Formula

- **Track & Component**: Track I (Quantum Algorithms — `quantum_algorithms.py`)
- **AI Tool & Model**: Gemini 3.8 Flash (High)
- **Issue Classification**: `[Algorithmic Logic Failure / State Over-Rotation]`
- **Description & Output**: During unit testing of Grover's search on a 2-qubit database ($n=2, N=4$) for marked target `'10'`, the algorithm completely failed to amplify the target state, yielding an almost uniform probability distribution `{'10': 264, '11': 234, '00': 257, '01': 269}` with empirical success probability only $\sim 25.8\%$.
- **Root Cause**: The optimal Grover iteration formula was initially coded as `int(round((pi / 4.0) * sqrt(N)))`. For $N=4$, $\frac{\pi}{4}\sqrt{4} = \frac{\pi}{2} \approx 1.5708$, which `round()` rounded up to $R = 2$ iterations. Because the initial state angle is $\theta = \arcsin(1/\sqrt{4}) = 30^\circ$, applying $R = 1$ rotation reaches $(2 \times 1 + 1) \times 30^\circ = 90^\circ$ ($\sin^2(90^\circ) = 1.0$, exact $100\%$ target recovery). Applying $R = 2$ rotations over-rotates the statevector to $(2 \times 2 + 1) \times 30^\circ = 150^\circ$, where $\sin^2(150^\circ) = (0.5)^2 = 0.25$, destroying quantum amplification.
- **Verified Fix**: Replaced `round()` with `int(math.floor((math.pi / 4.0) * math.sqrt(self.N)))`. This sets $R = 1$ for $N=4$, restoring $100\%$ target recovery probability, while properly setting $R = 2$ for $N=8$, $R = 3$ for $N=16$, and $R = 12$ for $N=256$.
- **Key Lesson**: In geometric quantum amplitude amplification, statevector rotations are discrete steps along a 2D subspace circle. Never use naive symmetric rounding for quantum iteration counts without verifying that the rotation angle $(2R+1)\arcsin(1/\sqrt{N})$ does not overshoot the target orthogonal axis ($\pi/2$).




