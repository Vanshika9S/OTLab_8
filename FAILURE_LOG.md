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
- **Key Lesson**: Compiler optimizations across control structures cannot rely on linear heuristics. Any transformation involving liveness (DCE), common subexpressions (CSE), or code motion (LICM) must operate over a mathematically rigorous CFG with fixed-point iterative dataflow equations that explicitly model loop back-edges.


