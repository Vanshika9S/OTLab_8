# Track J: Software-Engineering Optimization — Report

## 1. Objective & Codebase Selection
Optimize a real software-engineering task on a realistic codebase (>1,000 LOC):
- **Candidate Domain**: Test-suite minimization & regression prioritization (formulated as weighted set cover / 0-1 Knapsack solved via Greedy vs ILP) OR Build/CI scheduling / Memory cache-aware bottleneck refactoring.
- **Formulation**: Define decision variables $z_t \in \{0, 1\}$ (test selection), maximizing code coverage $\sum_c Cov_c$ subject to runtime execution budget $\sum_t T_t z_t \le B_{max}$.

## 2. Profiling & Baseline Bottleneck
- Profile unoptimized test-suite / baseline system execution.
- Identify wall-clock bottleneck and redundancy.

## 3. Fair Comparison Protocol
- Measure execution time, code coverage preservation, and failure detection capability before and after optimization.
- Assess readability and maintainability impact.

## 4. Experimental Results & Verification
*(To be populated following approved test runs)*

## 5. Trade-Off Analysis & Critical Review
*(To be populated per Project Rules)*
