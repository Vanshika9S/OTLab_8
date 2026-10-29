# Technical Report Index & Structure

This folder contains the consolidated technical report for **Assignment 8: Optimize Anything**.

## Master Technical Report Document
The complete consolidated report covering Tracks A through J, limitations, trade-offs, next steps, and the answers to the mandatory 10 final questions is published in:
👉 [**`report/TECHNICAL_REPORT.md`**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/report/TECHNICAL_REPORT.md)

---

## Individual Track Report Direct Links
Per Section 9 & 11 of [`ASSIGNMENT_SPEC.md`](../ASSIGNMENT_SPEC.md), each track maintains its detailed scientific report linked to its source code, tests, and raw experimental results:

1. [**Track A: Continuous Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_A_continuous/REPORT.md)
   - 1st & 2nd order methods, Backpropagation, Curvature, 4 Loss Landscapes.
2. [**Track B: Discrete Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_B_discrete/REPORT.md)
   - Greedy, Dynamic Programming, Branch-and-Bound, HiGHS ILP, Max-Cut QUBO/Ising.
3. [**Track C: Quantum Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_C_quantum/REPORT.md)
   - QAOA on QUBO, VQE, Parameter-Shift, SPSA, Quantum Natural Gradient, NISQ Noise & Barren Plateaus.
4. [**Track D: Submodular, Parallel & Distributed Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_D_submodular_parallel/REPORT.md)
   - Facility Location (Diminishing Returns), Work-Stealing vs Static Partitioning (Amdahl/Gustafson), FedAvg, MGDA/GradNorm.
5. [**Track E: Main Case Study (University Exam Timetabling)**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_E_case_study/REPORT.md)
   - Problem Formulation, DSATUR Greedy, Exact HiGHS ILP, Parallel SA (6 Cores), Toronto `sta83` Benchmark.
6. [**Track F: Compiler Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_F_compiler/REPORT.md)
   - 5 IR Passes (Constant Folding/Prop, DCE, CSE, Strength Reduction, LICM), Graph Coloring ILP vs Linear Scan.
7. [**Track G: xv6 Operating-System Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_G_xv6/REPORT.md)
   - Proportional-Share Lottery Scheduler, Kernel Lock Discipline, `settickets`/`getpstat` Syscalls, 3 Workload Benchmarks.
8. [**Track H: DBMS Workload Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_H_dbms/REPORT.md)
   - TPC-H SF 0.1 Workload, Knapsack/ILP Index Selection, System R Dynamic Programming Join Ordering, Write Penalty.
9. [**Track I: Quantum Algorithms & Advantage**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_I_quantum_advantage/REPORT.md)
   - 7 Core Quantum Algos (Deutsch-Jozsa, BV, Grover, QFT, QPE, Shor, Annealing), QML vs Classical MLP, Simulation Overhead.
10. [**Track J: Software-Engineering Optimization**](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_J_software_eng/REPORT.md)
    - Test Suite Profiling & Minimization as Weighted Set Cover (Greedy vs HiGHS ILP), Mutation Testing, Budget Prioritization.

---

## Supporting Disclosures
- **AI Tools Register**: [README.md AI Register](../README.md#ai-tools-register)
- **Failure Log (10 Authentic Cases)**: [FAILURE_LOG.md](../FAILURE_LOG.md)
- **Head-to-Head AI Tool Comparison**: [TOOL_COMPARISON.md](../TOOL_COMPARISON.md)
- **Prompt Logs**: [`prompts/`](../prompts/)
