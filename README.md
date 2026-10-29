# Assignment 8: Optimize Anything (14-Day Vibe-Coding Challenge)

> **Course**: Optimization Techniques  
> **Development Approach**: AI-Assisted (Vibe) Coding with strict verification & disclosure  
> **Test Status**: **78 / 78 Passing Tests Across All 10 Tracks (100% Green)**  
> **Repository Rules & Standards**: See [`PROJECT_RULES.md`](./PROJECT_RULES.md)  
> **Full Course & Assignment Specification**: See [`ASSIGNMENT_SPEC.md`](./ASSIGNMENT_SPEC.md)

---

## Quick Navigation & Core Deliverables

- 📄 **Master Technical Report**: [`report/TECHNICAL_REPORT.md`](./report/TECHNICAL_REPORT.md) (All 10 Tracks A–J + Section 11 Answers)
- 📋 **Final Submission Checklist**: [`SUBMISSION_CHECKLIST.md`](./SUBMISSION_CHECKLIST.md) (Verified against Section 9)
- 🎙️ **5-Minute Demo Script & Shot List**: [`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md) (Timing, speaker lines & live commands)
- 🧠 **Viva Cheat-Sheet & Questions**: [`VIVA_CHEATSHEET.md`](./VIVA_CHEATSHEET.md) (30 oral defense questions & invariants)
- ⚠️ **AI Failure Log**: [`FAILURE_LOG.md`](./FAILURE_LOG.md) (10 authentic AI error cases, fixes & lessons)
- ⚔️ **Head-to-Head AI Tool Comparison**: [`TOOL_COMPARISON.md`](./TOOL_COMPARISON.md) (Gemini 3.8 Flash vs Claude 3.5 Sonnet vs GPT-4o)
- 💬 **Complete Prompt Logs**: [`prompts/`](./prompts/) (Prompt histories for every track)

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
- Python 3.10+ (Recommended: 3.10, 3.11, or 3.13)
- GCC / Clang (for Track F and native benchmarks)
- QEMU & RISC-V GNU Toolchain (optional, for native Track G xv6 virtualization)
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
To run the full suite across all 10 tracks simultaneously (78 tests):
```bash
# Cross-platform via pytest:
python -m pytest

# Or native script on Windows PowerShell:
.\run_all.ps1

# Or native script on Linux / macOS / WSL:
chmod +x run_all.sh
./run_all.sh
```

### Running Individual Track Experiments
```bash
# Track A Continuous Optimization
python track_A_continuous/code/benchmark.py

# Track E University Exam Timetabling
python track_E_case_study/code/run_benchmarks.py

# Track G xv6 OS Scheduler Simulation
python track_G_xv6/code/lottery_scheduler_sim.py

# Track J Software Engineering Test Suite Minimization
python track_J_software_eng/code/run_track_j_benchmarks.py
```

---

## 4. AI Tools Register

Per Section 8 of the assignment specification, every AI tool and model version utilized throughout the project is disclosed here:

| Tool & Model Version | Tracks Used | Date(s) | Role / Kind of Work |
| :--- | :--- | :--- | :--- |
| **Gemini 3.8 Flash (High)** | Tracks A through J (All tracks) | 2026-10-26 to 2026-10-30 | Primary coding agent: architecture, mathematical formulations, implementation, debugging, unit tests, benchmark harnesses, technical reports, and failure diagnosis. |
| **Claude 3.5 Sonnet** | Track J | 2026-10-30 | Tool comparison benchmark: Chvátal greedy weighted set cover implementation, approximation proof analysis, and mutation test design. |
| **OpenAI GPT-4o** | Track J | 2026-10-30 | Tool comparison benchmark: Integer Linear Program formulation for set cover, sparse constraint matrix construction, and heuristic comparison. |

---

## 5. Chapter 6 Coverage Checklist

Per Section 5 of [`ASSIGNMENT_SPEC.md`](./ASSIGNMENT_SPEC.md), every taught algorithm and technique must be accounted for with a valid implementation or verifiable library experiment:

| Chapter 6 Area | Method / Topic Required | Track | Code Location | Status & Result Summary |
| :--- | :--- | :--- | :--- | :--- |
| **Foundations in ML** | ML as Optimization (params, loss, regularization) | Track A | `track_A_continuous/code/models.py` | **Complete**: Ridge regression demo; L2 eigenvalue shift proved |
| | Convex vs Non-Convex Landscapes (minima, saddle points) | Track A | `track_A_continuous/code/benchmark.py` | **Complete**: Evaluated across convex, Rosenbrock, Rastrigin, and saddle surface |
| | Quantum computing concepts & optimization role in QML | Track C / I / A | `track_A_continuous/REPORT.md` | **Documented**: Theoretical analysis of PQCs, hybrid VQE/QAOA loop, barren plateaus |
| **Continuous Optimization** | GD, SGD, Mini-batch SGD | Track A | `track_A_continuous/code/continuous_optimizers.py` | **Complete**: Implemented from scratch; verified across 4 landscapes |
| | Momentum & Nesterov Accelerated Gradient (NAG) | Track A | `track_A_continuous/code/continuous_optimizers.py` | **Complete**: Polyak heavy-ball & Nesterov lookahead braking verified |
| | AdaGrad, RMSProp, Adam | Track A | `track_A_continuous/code/continuous_optimizers.py` | **Complete**: Adaptive per-coordinate coordinate scaling & moment tracking |
| | Second-order / Curvature (Newton, Gauss-Newton) | Track A | `track_A_continuous/code/continuous_optimizers.py` | **Complete**: Exact Newton damping; Gauss-Newton on non-linear residuals |
| | Backpropagation (distinct from optimizer) | Track A | `track_A_continuous/code/neural_net_backprop.py` | **Complete**: Hand-derived 2-layer MLP backprop verified vs finite differences ($2.14 \times 10^{-11}$) |
| | Curvature Approximations (Fisher, diagonal/low-rank, HVP) | Track A | `track_A_continuous/code/neural_net_backprop.py` | **Complete**: Directional HVP, empirical Fisher FIM, diagonal & truncated low-rank SVD |
| | Convergence analysis (convex, strongly convex, non-convex) | Track A | `track_A_continuous/REPORT.md` | **Complete**: Convergence rate analysis; documented Newton saddle trap |
| | Step-size, optimizer tuning, noisy objectives | Track A | `track_A_continuous/code/benchmark.py` | **Complete**: 10-seed repeated runs on noisy objective; step-size sweep ($\eta \in [10^{-4}, 2.0]$) |
| **Discrete Optimization** | Greedy selection methods | Track B / J | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: Value-to-weight density ratio heuristic ($O(N \log N)$) |
| | Integer Linear Programming (ILP) | Track B / E / J | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: HiGHS branch-and-cut solving 0-1 knapsack |
| | Branch-and-Bound | Track B | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: Hand-written B&B with fractional relaxation bounds (0.78 ms on N=20) |
| | Dynamic Programming | Track B / F / H | `track_B_discrete/code/knapsack_solvers.py` | **Complete**: 2D tabulation $O(N \cdot W)$ with subset backtracking |
| | Feature selection / combinatorial applications | Track B | `track_B_discrete/code/qubo_maxcut.py` | **Complete**: Cardinality constraint penalty formulation verified |
| | QUBO & Ising formulation with penalty terms | Track B / C / I | `track_B_discrete/code/qubo_maxcut.py` | **Complete**: Max-Cut QUBO & Ising derived; 10-seed SA solved; exported for Track C |
| **Quantum Optimization** | QAOA (solving Track B QUBO / Max-Cut) | Track C | `track_C_quantum/code/qaoa_maxcut.py` | **Complete**: Multi-depth QAOA ($p=1..3$) evaluated on Max-Cut QUBO |
| | VQE (Variational Quantum Eigensolver) | Track C | `track_C_quantum/code/vqe_hamiltonian.py` | **Complete**: Ground-state energy verified on Hamiltonian |
| | Parameterized Quantum Circuits (PQCs) & QNNs | Track C / I | `track_C_quantum/code/pqc_qnn.py` | **Complete**: Variational angle encoding ansatz trained on non-linear data |
| | Parameter-shift rule & SPSA | Track C | `track_C_quantum/code/gradients.py` | **Complete**: Analytical gradient verified vs central finite differences ($|\Delta| < 10^{-5}$) |
| | Quantum Natural Gradient | Track C | `track_C_quantum/code/gradients.py` | **Complete**: Fubini-Study metric tensor conditioning implemented |
| | Barren plateaus, shot cost, hardware noise | Track C / I | `track_I_quantum_advantage/code/noise_experiment.py` | **Complete**: Exponential variance decay $\mathcal{O}(2^{-n})$ and fidelity collapse under NISQ noise |
| | Quantum annealing & QUBO embedding limits | Track C / I | `track_I_quantum_advantage/code/quantum_algorithms.py` | **Complete**: Quadratic physical qubit blowup $\mathcal{O}(n^2)$ and chain break model |
| **Submodular Optimization** | Diminishing returns property verification | Track D | `track_D_submodular_parallel/code/submodular_max.py` | **Complete**: Verified submodularity and monotonicity on facility location |
| | Greedy selection & approximation guarantee check | Track D | `track_D_submodular_parallel/code/submodular_max.py` | **Complete**: Proven $(1 - 1/e)$ approximation factor satisfied (96.8% achieved) |
| **Parallel Optimization** | Makespan, load balancing, work stealing | Track D | `track_D_submodular_parallel/code/parallel_work_stealing.py` | **Complete**: Work stealing achieved $4.85\times$ speedup on 6 cores (80.8% efficiency) |
| | Data, model, pipeline parallelism | Track D | `track_D_submodular_parallel/code/parallel_work_stealing.py` | **Complete**: Multiprocessing across 6 physical CPU cores |
| | Amdahl's Law and Gustafson's Law evaluation | Track D | `track_D_submodular_parallel/code/parallel_work_stealing.py` | **Complete**: Speedup matching Amdahl model ($s=0.95$) |
| **Distributed / Multi-task** | FedAvg vs centralized (varying steps & comm rounds) | Track D | `track_D_submodular_parallel/code/fedavg_simulation.py` | **Complete**: 5-node federation, $10\times$ bandwidth reduction, 93.4% accuracy |
| | MGDA and GradNorm vs equal weighting on two-task model | Track D | `track_D_submodular_parallel/code/multi_task_opt.py` | **Complete**: Minimum-norm Pareto-optimal descent vector verified |
| **Strategy Selection & Main Study** | Exam Timetabling Baselines & Full Optimization | Track E | `track_E_case_study/code/ilp_solver.py` | **Complete**: DSATUR (4.2 ms), HiGHS exact ILP (38.0 penalty), 6-core SA, Toronto benchmark |
| **Compiler Optimization** | ToyLang Grammar & Optimization Passes | Track F | `track_F_compiler/code/passes.py` | **Complete**: CF, DCE, CSE, SR, LICM, ILP register allocation, 100% semantics equivalence |
| **Operating System (xv6)** | xv6-riscv Benchmark Suite & Lottery Scheduler | Track G | `track_G_xv6/code/` | **Complete**: Proportional-share Lottery Scheduler (+31.1% turnaround speedup), `pstat` syscalls |
| **DBMS Optimization** | TPC-H Index Selection & Join-Order Optimization | Track H | `track_H_dbms/code/index_optimizer.py` | **Complete**: Knapsack/ILP index selection (-84.5% latency), System R join-order DP (-85.8%) |
| **Quantum Algorithms** | Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE, Shor | Track I | `track_I_quantum_advantage/code/quantum_algorithms.py` | **Complete**: 7 algorithms verified on ground truths; 2 hand-crafted circuits |
| | Variational classifier / Quantum Kernel vs classical model | Track I | `track_I_quantum_advantage/code/qml_benchmark.py` | **Complete**: 10 seeds, VQC vs Classical MLP (honest negative result, 79x slower simulation) |
| **Software Engineering** | Test-Suite Minimization & Prioritization via Set Cover | Track J | `track_J_software_eng/code/test_suite_optimizer.py` | **Complete**: Greedy & HiGHS ILP Set Cover (-34.4% time, 100% coverage & mutation score) |

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
- [`prompts/day14_final_synthesis_prompt_log.md`](./prompts/day14_final_synthesis_prompt_log.md)

AI mistakes and corrections are documented in [`FAILURE_LOG.md`](./FAILURE_LOG.md). Comparative evaluation across tools is in [`TOOL_COMPARISON.md`](./TOOL_COMPARISON.md).
