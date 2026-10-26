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
| **Quantum Optimization** | QAOA (solving Track B QUBO / Max-Cut) | Track C | `track_C_quantum/code/` | Planned (Smoke test operational; Track B export ready) |
| | VQE (Variational Quantum Eigensolver) | Track C | `track_C_quantum/code/` | Planned |
| | Parameterized Quantum Circuits (PQCs) & QNNs | Track C / I | `track_C_quantum/code/` | Planned |
| | Parameter-shift rule & SPSA | Track C | `track_C_quantum/code/` | Planned |
| | Quantum Natural Gradient | Track C | `track_C_quantum/code/` | Planned |
| | Barren plateaus, shot cost, hardware noise | Track C / I | `track_C_quantum/code/` | Planned |
| | Quantum annealing & QUBO embedding limits | Track C / I | `track_C_quantum/code/` | Planned |
| **Submodular Optimization** | Diminishing returns property verification | Track D | `track_D_submodular_parallel/code/` | Planned |
| | Greedy selection & approximation guarantee check | Track D | `track_D_submodular_parallel/code/` | Planned |
| **Parallel Optimization** | Makespan, load balancing, work stealing | Track D | `track_D_submodular_parallel/code/` | Planned |
| | Data, model, pipeline parallelism | Track D | `track_D_submodular_parallel/code/` | Planned |
| | Amdahl's Law and Gustafson's Law evaluation | Track D | `track_D_submodular_parallel/code/` | Planned |
| **Distributed / Multi-task** | FedAvg vs centralized (varying steps & comm rounds) | Track D | `track_D_submodular_parallel/code/` | Planned |
| | MGDA and GradNorm vs equal weighting on two-task model | Track D | `track_D_submodular_parallel/code/` | Planned |
| **Strategy Selection & Main Study** | Exam Timetabling Baselines & Independent Validation | Track E | `track_E_case_study/code/` | **Complete**: 10-seed baseline benchmarked (0% feasibility, 120.2 clashes); validator verified by unit tests |
| **Compiler Optimization** | ToyLang Grammar & Optimization Passes Design | Track F | `track_F_compiler/PROPOSAL.md` | **Design Stage**: Grammar specified with 3 benchmark programs |
| **Operating System (xv6)** | xv6-riscv QEMU Setup & usertests Validation | Track G | `track_G_xv6/SETUP_AND_BASELINE.md` | **Harness Defined**: QEMU setup and usertests protocol ready |
| **DBMS Optimization** | TPC-H Workload Baseline & Default Optimizer Profiling | Track H | `track_H_dbms/code/tpch_benchmark_harness.py` | **Complete**: 8-query workload profiled (cold vs warm latency, EXPLAIN plans) |
| **Quantum Algorithms** | Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE | Track I | `track_I_quantum_advantage/code/` | Planned (Qiskit 2.6.1 installed) |
| | Variational classifier / Quantum Kernel vs classical model | Track I | `track_I_quantum_advantage/code/` | Planned |
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
