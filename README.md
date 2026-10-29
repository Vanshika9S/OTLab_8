# Assignment 8: Optimize Anything (14-Day Vibe-Coding Challenge)

> **Course**: Optimization Techniques  
> **Development Approach**: AI-Assisted (Vibe) Coding with strict verification & disclosure  
> **Repository Rules & Standards**: See [`PROJECT_RULES.md`](./PROJECT_RULES.md)  
> **Full Course & Assignment Specification**: See [`ASSIGNMENT_SPEC.md`](./ASSIGNMENT_SPEC.md)

---

## 1. Overview & Architecture

This repository hosts the complete work for **Assignment 8: Optimize Anything**, structured across ten compulsory experiment tracks (Tracks A through J). Each track investigates a focused optimization problem, establishes baseline measurements, implements optimization algorithms from Chapter 6 (or domain-specific frameworks), executes fair comparisons, and conducts rigorous verification.

### Track Directory Structure

| Track | Domain | Directory | Primary Focus |
| :--- | :--- | :--- | :--- |
| **Track A** | Continuous Optimization | [`track_A_continuous/`](./track_A_continuous/) | First- and second-order methods, curvature, convex vs non-convex landscapes |
| **Track B** | Discrete Optimization | [`track_B_discrete/`](./track_B_discrete/) | Greedy, ILP, Branch-and-Bound, DP, QUBO/Ising formulations |
| **Track C** | Quantum Optimization | [`track_C_quantum/`](./track_C_quantum/) | QAOA on Track B QUBO, VQE, PQC/QNN, noise & shot analysis |
| **Track D** | Submodular & Parallel | [`track_D_submodular_parallel/`](./track_D_submodular_parallel/) | Diminishing returns, Amdahl/Gustafson laws, FedAvg, MGDA/GradNorm |
| **Track E** | Main Case Study | [`track_E_case_study/`](./track_E_case_study/) | University Exam Timetabling (Hard/Soft constraints, ILP vs Heuristics) |
| **Track F** | Compiler Optimization | [`track_F_compiler/`](./track_F_compiler/) | Mini-compiler / optimization passes (DCE, constant folding, reg allocation) |
| **Track G** | xv6 OS Optimization | [`track_G_xv6/`](./track_G_xv6/) | Kernel scheduling / memory subsystem enhancement in xv6 under QEMU |
| **Track H** | DBMS Optimization | [`track_H_dbms/`](./track_H_dbms/) | Query execution, join-order selection, index/view knapsack optimization |
| **Track I** | Quantum Advantage | [`track_I_quantum_advantage/`](./track_I_quantum_advantage/) | Quantum algorithms vs classical counterparts, QML vs classical baseline |
| **Track J** | Software Engineering | [`track_J_software_eng/`](./track_J_software_eng/) | Profiling & bottleneck optimization in real codebase (>=1000 LOC) |

Each track directory is organized into:
- `code/`: Source code with input validation and inline comments.
- `tests/`: Automated unit and integration test suites.
- `results/`: Raw metric logs, benchmark tables, and generated visualization plots.
- `REPORT.md`: Track-specific objective, baseline, fair comparison, trade-offs, and critical review.

---

## 2. Setup & Installation

### Prerequisites
- Python 3.10+ (Recommended: 3.10 or 3.11)
- GCC / Clang (for Track F and native benchmarks)
- QEMU & RISC-V GNU Toolchain (for Track G xv6 virtualization)
- Git

### Virtual Environment Setup

#### On Linux / macOS / WSL:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Execution & Verification

### Running All Automated Tests
To run test suites across all tracks simultaneously:
```bash
bash run_all.sh
```
or via pytest directly:
```bash
pytest -v track_*/tests/
```

### Running Individual Track Experiments
Navigate to any track directory or run module-specific scripts:
```bash
# Example: Track A Continuous Optimization
python track_A_continuous/code/run_experiments.py

# Example: Track E University Exam Timetabling
python track_E_case_study/code/run_timetabler.py
```

---

## 4. AI Tools Register

Per Section 8 of the assignment specification, every AI tool and model version utilized throughout the project is disclosed here:

| Tool & Model Version | Tracks Used | Date(s) | Role / Kind of Work |
| :--- | :--- | :--- | :--- |
| Gemini 3.8 Flash (High) | Track E (and Repo setup) | 2026-10-26 | Repo architecture, spec compilation, Track E dataset generator, independent validator, 10-seed baseline benchmarking |
| Gemini 3.8 Flash (High) | Tracks C, G, H, F, J | 2026-10-26 | Day 3 environment harnesses, Qiskit Bell state smoke test, TPC-H profiler, ToyLang grammar proposal, test profiler |
| Gemini 3.8 Flash (High) | Track A | 2026-10-26 | Day 4: 10 continuous optimizers in NumPy, hand-derived backprop, HVP, Fisher/low-rank curvature, 4 landscapes, sensitivity sweep |
| Gemini 3.8 Flash (High) | Track B | 2026-10-26 | Day 5: 5 knapsack solvers (BF, Greedy, DP, ILP, B&B), Max-Cut QUBO/Ising, constraint penalties, 10-seed SA, Track C export |
| Gemini 3.8 Flash (High) | Track C | 2026-10-26 | Day 6: QAOA, VQE ground state, parameter-shift rule, SPSA, QNG metric tensor, barren plateau variance decay |
| Gemini 3.8 Flash (High) | Track D | 2026-10-27 | Day 7: Submodular greedy (1-1/e), work stealing, Amdahl/Gustafson scaling, FedAvg, MGDA/GradNorm |
| Gemini 3.8 Flash (High) | Track F | 2026-10-27 | Day 8: Lexer, parser, CFG, 4 optimizations (CF, DCE, CSE, SR, LICM), ILP register allocation |
| Gemini 3.8 Flash (High) | Track G | 2026-10-28 | Day 9: xv6-riscv benchmark suite (CPU, IO, mixed) and pstat header specification |
| Gemini 3.8 Flash (High) | Track H | 2026-10-28 | Day 10: DBMS index selection (Knapsack/ILP/DP), System R join-order DP, write-cost penalty |
| Gemini 3.8 Flash (High) | Track E | 2026-10-29 | Day 11: University exam timetabling full optimization (DSATUR, exact HiGHS ILP, parallel SA 6 cores, Toronto benchmark, scaling & sensitivity) |
| Gemini 3.8 Flash (High) | Track I | 2026-10-29 | Day 12: Quantum algorithms suite (7 algos, hand-crafted circuits), NISQ noise degradation, QML vs classical (10 seeds), Grover scaling, honest negative analysis |
| *(Pending user inputs for other tools: Claude, Copilot, ChatGPT, etc.)* | | | |

---

## 5. Chapter 6 Coverage Checklist

Per Section 5 of [`ASSIGNMENT_SPEC.md`](./ASSIGNMENT_SPEC.md), every taught algorithm and technique must be accounted for with a valid implementation or verifiable library experiment:

| Chapter 6 Area | Method / Topic Required | Track | Code Location | Status & Result Summary |
| :--- | :--- | :--- | :--- | :--- |
| **Foundations in ML** | ML as Optimization (params, loss, regularization) | Track A | `track_A_continuous/code/landscapes.py` | **Complete**: Ridge regression demo; L2 eigenvalue shift proved |
| | Convex vs Non-Convex Landscapes (minima, saddle points) | Track A | `track_A_continuous/code/landscapes.py` | **Complete**: Evaluated across convex, strongly convex, and saddle landscape |
| | Quantum computing concepts & optimization role in QML | Track C / I / A | `track_A_continuous/REPORT.md` | **Documented**: Theoretical analysis of PQCs, hybrid VQE/QAOA loop, barren plateaus |
| **Continuous Optimization** | GD, SGD, Mini-batch SGD | Track A | `track_A_continuous/code/optimizers.py` | **Complete**: Implemented from scratch; verified across 4 landscapes |
| | Momentum & Nesterov Accelerated Gradient (NAG) | Track A | `track_A_continuous/code/optimizers.py` | **Complete**: Polyak heavy-ball & Nesterov lookahead braking verified |
| | AdaGrad, RMSProp, Adam | Track A | `track_A_continuous/code/optimizers.py` | **Complete**: Adaptive per-coordinate coordinate scaling & moment tracking |
| | Second-order / Curvature (Newton, Gauss-Newton) | Track A | `track_A_continuous/code/optimizers.py` | **Complete**: Exact Newton damping; Gauss-Newton on non-linear residuals |
| | Backpropagation (distinct from optimizer) | Track A | `track_A_continuous/code/neural_net_backprop.py` | **Complete**: Hand-derived 2-layer MLP backprop verified vs finite differences ($2.14 \times 10^{-11}$) |
| | Curvature Approximations (Fisher, diagonal/low-rank, HVP) | Track A | `track_A_continuous/code/neural_net_backprop.py` | **Complete**: Directional HVP, empirical Fisher FIM, diagonal & truncated low-rank SVD |
| | Convergence analysis (convex, strongly convex, non-convex) | Track A | `track_A_continuous/REPORT.md` | **Complete**: Convergence rate analysis; documented Newton saddle trap |
| | Step-size, optimizer tuning, noisy objectives | Track A | `track_A_continuous/code/run_benchmarks.py` | **Complete**: 10-seed repeated runs on noisy objective; step-size sweep ($\eta \in [10^{-4}, 2.0]$) |
| **Discrete Optimization** | Greedy selection methods | Track B | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: Value-to-weight density ratio heuristic ($O(N \log N)$) |
| | Integer Linear Programming (ILP) | Track B / E | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: HiGHS branch-and-cut solving 0-1 knapsack |
| | Branch-and-Bound | Track B | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: Hand-written B&B with fractional relaxation bounds (0.25 ms on N=20) |
| | Dynamic Programming | Track B / F | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: 2D tabulation $O(N \cdot W)$ with subset backtracking |
| | Feature selection / combinatorial applications | Track B | `track_B_discrete/code/qubo_ising.py` | **Complete**: Cardinality constraint penalty formulation verified |
| | QUBO & Ising formulation with penalty terms | Track B / C | `track_B_discrete/code/qubo_ising.py` | **Complete**: Max-Cut QUBO & Ising derived; 10-seed SA solved; exported for Track C |
| **Quantum Optimization** | QAOA (solving Track B QUBO / Max-Cut) | Track C | `track_C_quantum/code/qaoa_maxcut.py` | **Complete**: Multi-depth QAOA ($p=1..4$) evaluated on 5-qubit ring |
| | VQE (Variational Quantum Eigensolver) | Track C | `track_C_quantum/code/vqe_solver.py` | **Complete**: Ground-state energy verified on H2 molecular Hamiltonian |
| | Parameterized Quantum Circuits (PQCs) & QNNs | Track C / I | `track_C_quantum/code/gradients_and_qnn.py` | **Complete**: Variational angle encoding ansatz trained on non-linear data |
| | Parameter-shift rule & SPSA | Track C | `track_C_quantum/code/gradients_and_qnn.py` | **Complete**: Analytical gradient verified vs central finite differences ($3.2 \times 10^{-7}$) |
| | Quantum Natural Gradient | Track C | `track_C_quantum/code/gradients_and_qnn.py` | **Complete**: Fubini-Study metric tensor conditioning implemented |
| | Barren plateaus, shot cost, hardware noise | Track C / I | `track_I_quantum_advantage/code/noise_experiment.py` | **Complete**: Exponential fidelity collapse under NISQ noise ($p \in [0, 0.05]$) |
| | Quantum annealing & QUBO embedding limits | Track C / I | `track_I_quantum_advantage/code/quantum_algorithms.py` | **Complete**: Quadratic physical qubit blowup $\mathcal{O}(n^2)$ and chain break model |
| **Submodular Optimization** | Diminishing returns property verification | Track D | `track_D_submodular_parallel/code/submodular_greedy.py` | **Complete**: Verified submodularity and monotonicity on sensor coverage |
| | Greedy selection & approximation guarantee check | Track D | `track_D_submodular_parallel/code/submodular_greedy.py` | **Complete**: Proven $(1 - 1/e)$ approximation factor satisfied; counterexample documented |
| **Parallel Optimization** | Makespan, load balancing, work stealing | Track D | `track_D_submodular_parallel/code/parallel_execution.py` | **Complete**: Work stealing reduces load imbalance from 42% to 6% |
| | Data, model, pipeline parallelism | Track D | `track_D_submodular_parallel/code/parallel_execution.py` | **Complete**: Multi-worker multiprocessing across 6 CPU cores |
| | Amdahl's Law and Gustafson's Law evaluation | Track D | `track_D_submodular_parallel/code/parallel_execution.py` | **Complete**: Speedup up to $5.2\times$ measured; efficiency modeled |
| **Distributed / Multi-task** | FedAvg vs centralized (varying steps & comm rounds) | Track D | `track_D_submodular_parallel/code/distributed_multitask.py` | **Complete**: 5-node federation evaluated across heterogeneous data |
| | MGDA and GradNorm vs equal weighting on two-task model | Track D | `track_D_submodular_parallel/code/distributed_multitask.py` | **Complete**: Frank-Wolfe min-norm common descent direction verified |
| **Strategy Selection & Main Study** | Exam Timetabling Baselines & Full Optimization | Track E | `track_E_case_study/code/optimizers.py` | **Complete**: DSATUR, HiGHS exact ILP, 6-core parallel SA (66.7% clash reduction), Toronto benchmark 100% feasible |
| **Compiler Optimization** | ToyLang Grammar & Optimization Passes | Track F | `track_F_compiler/code/optimizer.py` | **Complete**: CF, DCE, CSE, SR, LICM, ILP register allocation, 100% semantics equivalence |
| **Operating System (xv6)** | xv6-riscv Benchmark Suite & pstat System Call | Track G | `track_G_xv6/code/` | **Complete**: CPU-bound, IO-bound, and mixed benchmarks with pstat header |
| **DBMS Optimization** | TPC-H Index Selection & Join-Order Optimization | Track H | `track_H_dbms/code/index_optimizer.py` | **Complete**: Knapsack/ILP index selection, System R join-order DP, write-cost amplification |
| **Quantum Algorithms** | Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE, Shor | Track I | `track_I_quantum_advantage/code/quantum_algorithms.py` | **Complete**: 7 algorithms verified on ground truths; 2 hand-crafted circuits |
| | Variational classifier / Quantum Kernel vs classical model | Track I | `track_I_quantum_advantage/code/qml_benchmark.py` | **Complete**: 10 seeds, VQC vs RBF SVM / MLP / LogReg (honest negative result) |
| **Software Engineering** | Test-Suite Profiler & Coverage Matrix Instrumentation | Track J | `track_J_software_eng/code/baseline_profiler.py` | **Complete**: Runtime & line coverage matrix collector operational |

---

## 6. Prompt Logs & Traceability

Prompt histories, revisions, model responses, and verification notes for each track are maintained in:
- [`prompts/track_A/`](./prompts/track_A/)
- [`prompts/track_B/`](./prompts/track_B/)
- [`prompts/track_C/`](./prompts/track_C/)
- [`prompts/track_D/`](./prompts/track_D/)
- [`prompts/track_E/`](./prompts/track_E/)
- [`prompts/track_F/`](./prompts/track_F/)
- [`prompts/track_G/`](./prompts/track_G/)
- [`prompts/track_H/`](./prompts/track_H/)
- [`prompts/track_I/`](./prompts/track_I/)
- [`prompts/track_J/`](./prompts/track_J/)

AI mistakes and corrections are documented in [`FAILURE_LOG.md`](./FAILURE_LOG.md). Comparative evaluation across tools is in [`TOOL_COMPARISON.md`](./TOOL_COMPARISON.md).
