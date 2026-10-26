# Track F: Compiler Optimization — Report

## 1. Objective
Build a mini-compiler or optimization passes for a toy intermediate representation (IR) or bytecode engine. Implement at least four optimizations (for full credit):
1. Constant folding and constant propagation.
2. Dead-code elimination (DCE).
3. Common subexpression elimination (CSE) or strength reduction.
4. Loop unrolling or loop-invariant code motion (LICM).

Formulate at least one compiler decision (e.g. register allocation via graph coloring or instruction scheduling / unroll factor selection) as an optimization problem solved using a Chapter 6 method (Greedy / ILP / Dynamic Programming).

## 2. Baseline
Unoptimized intermediate representation code generator executing without optimization passes.

## 3. Fair Comparison Protocol
- Measure dynamic instruction execution count, total IR instruction size, compilation time, and runtime.
- **Correctness Check**: Ensure the optimized program produces identical outputs to the unoptimized program across all test workloads.

## 4. Experimental Results & Verification
*(To be populated following approved test runs)*

## 5. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
