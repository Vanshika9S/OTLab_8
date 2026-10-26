# Day 7 Prompt Log: Track D — Submodular, Parallel, and Distributed Optimization

> **Track**: Track D (Submodular, Parallel & Distributed Optimization)  
> **Date**: October 26, 2026  
> **Model / Assistant**: Gemini 3.8 Flash (via Antigravity IDE)  
> **User State**: Active Workspace `c:\Users\satye\OneDrive\Desktop\OTLab8`

---

## 1. User Prompt
```markdown
Day 7: Track D. Read ASSIGNMENT_SPEC.md and PROJECT_RULES.md first. Work in track_D_parallel_distributed/. Use the CPU details I gave on Day 1.
1. Submodular: greedy on coverage or facility location. First test diminishing returns empirically, then check the conditions behind the (1-1/e) guarantee before mentioning it. Compare with brute force on small instances and show a non-submodular objective where greedy has no guarantee.
2. Parallel (multiprocessing): demonstrate load balancing, makespan, work stealing (vs static partitioning), locality and synchronization cost, plus data, model and pipeline parallelism on a real workload. Measure speedup and efficiency vs number of cores, and interpret with Amdahl and Gustafson. Report overhead honestly, including cases where parallelism does not help.
3. Distributed: FedAvg vs centralized training (vary local steps and communication rounds). MGDA and GradNorm vs equal weighting on a two-task model.
4. Repeated runs, plots, tests. Run DAILY CLOSE.
```

---

## 2. Intent & Planning
1. **Hardware Profile Detection**:
   - Inspected host hardware: 12th Gen Intel Core i3-1215U (Alder Lake architecture).
   - 6 physical cores: 2 Performance-cores (with Hyper-Threading) + 4 Efficient-cores (single-threaded), totaling 8 logical threads.
2. **Directory Resolution**:
   - Created directory junction `track_D_parallel_distributed <<===>> track_D_submodular_parallel` using Windows NTFS symlink to handle path aliases seamlessly.
3. **Submodular Optimization**:
   - Implemented `FacilityLocationCoverage` in `track_D_submodular_parallel/code/submodular_opt.py`.
   - Empirically verified diminishing returns $\Delta(e \mid A) \ge \Delta(e \mid B)$ across 500 subset pairs (0 violations).
   - Programmatically verified the four Nemhauser preconditions (normalized, monotone, submodular, cardinality constraint) before citing the $(1 - 1/e)$ bound.
   - Evaluated greedy vs exact brute force $\binom{n}{k}$ for $k \in [1, 5]$.
   - Constructed `NonSubmodularSynergyObjective` demonstrating greedy failure ($\alpha = 0.0294$) due to supermodular pairwise synergy.
4. **Parallel Multiprocessing**:
   - Implemented load balancing benchmarks in `parallel_multiprocessing.py`.
   - Compared static block partitioning against dynamic work stealing on a workload with straggler tasks, demonstrating up to 46.6% makespan reduction.
   - Evaluated Amdahl's strong scaling ($f = 0.7503$, $S_{\max} = 4.00\times$) and Gustafson's weak scaling.
   - Measured pipeline bubble fraction for 3-stage pipeline parallelism.
   - Demonstrated an honest negative result: micro-workload IPC dispatch caused an $18.7\times$ slowdown compared to sequential execution.
5. **Distributed & Multi-Task Optimization**:
   - Implemented `FedAvg` with Dirichlet non-IID client partitions across communication rounds ($R \in [5, 20]$) and local epochs ($E \in [1, 15]$).
   - Evaluated two-task learning with strongly conflicting gradients ($\cos \theta = -0.9792$), comparing Equal Weighting vs MGDA vs GradNorm.
6. **Automated Testing & Daily Close**:
   - Wrote 8 unit tests in `test_parallel_distributed.py`.
   - Updated `pytest.ini` and executed full repo test suite (34 passed in 6.98s).

---

## 3. Tool Calls & Execution Trace
- `run_command`: Inspected CPU specifications via `psutil` and `Get-CimInstance Win32_Processor`.
- `run_command`: `cmd /c mklink /J track_D_parallel_distributed track_D_submodular_parallel`.
- `write_to_file`: `track_D_submodular_parallel/code/submodular_opt.py`.
- `write_to_file`: `track_D_submodular_parallel/code/parallel_multiprocessing.py`.
- `write_to_file`: `track_D_submodular_parallel/code/distributed_and_multitask.py`.
- `write_to_file`: `track_D_submodular_parallel/code/run_track_d_benchmarks.py`.
- `run_command`: Executed benchmark suite (generated 7 CSV files and 5 PNG plots).
- `write_to_file`: `track_D_submodular_parallel/tests/test_parallel_distributed.py`.
- `run_command`: `pytest -v` (caught test fixture naming collision, resolved).
- `replace_file_content`: Renamed `test_diminishing_returns` to `check_diminishing_returns`.
- `run_command`: `pytest -v` (34 passed in 6.98s).
- `write_to_file`: `track_D_submodular_parallel/REPORT.md`.

---

## 4. Errors Encountered & Debugging
1. **Pytest Test Function Auto-Discovery Conflict**:
   - *Error*: `test_parallel_distributed.py` imported `test_diminishing_returns(obj, ...)` from `submodular_opt.py`. Pytest recognized the `test_` prefix and attempted to treat the library helper as a test function, failing with `fixture 'obj' not found`.
   - *Fix*: Renamed the helper function to `check_diminishing_returns` across `submodular_opt.py`, `run_track_d_benchmarks.py`, and `test_parallel_distributed.py`. Pytest collected and executed all 8 unit tests cleanly.
2. **Pytest.ini Path Registration**:
   - Added `track_D_submodular_parallel/tests` to `testpaths` in root `pytest.ini` to ensure global discovery.

---

## 5. Human-in-the-Loop Oversight
- Ensured all results are labelled `[Hardware-Measured]` for local multiprocessing and `[Simulated]` for distributed FedAvg/multi-task benchmarks.
- Verified that the $(1 - 1/e)$ approximation theorem was only quoted after programmatically checking all 4 prerequisites.
- Verified that real CPU core heterogeneity (2 P-cores + 4 E-cores) was explicitly modeled and accounted for in the scaling analysis.
