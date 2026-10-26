# Track G: xv6 Operating-System Optimization — Report

## 1. Objective & Features Selected
Modify the xv6-riscv kernel to optimize core operating system subsystems:
- **Feature 1**: Scheduler optimization (e.g. Priority / Lottery / MLFQ scheduler replacing naive round-robin).
- **Feature 2 (for full credit)**: Memory or I/O subsystem optimization (e.g. Copy-On-Write (COW) fork or an LRU buffer cache replacement policy).

## 2. Kernel Concepts & Objectives
- **OS Concepts**: Process scheduling dispatch, kernel lock contention, virtual memory page fault handling, buffer cache hit rates.
- **Metrics Optimized**: Average turnaround time, response time, CPU utilization fairness, page allocation overhead.

## 3. Workload Benchmarks & Verification
- At least three user-level benchmark programs designed to stress:
  1. CPU-intensive compute workloads (measuring turnaround time / CPU allocation).
  2. Interactive / mixed I/O workloads (measuring response time).
  3. Fork-heavy memory allocation workloads (measuring allocation speed and memory footprint).
- **Correctness Check**: xv6 must successfully boot and pass the official `usertests` suite. Clean patch/diff submitted.

## 4. Experimental Results & Verification
*(To be populated following QEMU test runs)*

## 5. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
