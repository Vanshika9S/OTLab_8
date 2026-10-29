# TOOL COMPARISON: Multi-AI Benchmark on Optimization Task

> **Course**: Optimization Techniques  
> **Topic**: Empirical Comparison of AI Coding Assistants on an Optimization Problem  
> **Date**: October 30, 2026 (Day 13)  
> **Status**: Standardized Benchmark Protocol & Comparative Analysis

---

## 1. Selected Comparison Task

To fairly evaluate AI coding tools under identical conditions, we selected a classic Chapter 6 combinatorial optimization problem with both heuristic and exact formulations:

### Task Specification: Minimum Weight Set Cover (Greedy vs Exact ILP)
- **Problem Statement**:
  Given a universe of elements $U = \{1, 2, 3, 4, 5\}$ and a collection of weighted subsets:
  - $S_1 = \{1, 2, 3\}$ with cost $c_1 = 10$
  - $S_2 = \{2, 4\}$ with cost $c_2 = 4$
  - $S_3 = \{3, 4, 5\}$ with cost $c_3 = 7$
  - $S_4 = \{1, 5\}$ with cost $c_4 = 5$
- **Requirements for the AI Assistant**:
  1. Formulate and solve using **Chvátal's Greedy heuristic** (cost-effectiveness ratio $\arg\max \frac{|S_i \cap \text{Uncovered}|}{c_i}$).
  2. Formulate and solve using **Exact Integer Linear Programming (ILP)** using modern SciPy (`scipy.optimize.milp`), with `LinearConstraint` and binary variable bounds.
  3. Return the selected subsets, total cost, and verify 100% universe coverage.

---

## 2. Standardized Prompt for AI Tools

```text
Write a clean, self-contained Python script to solve Minimum Weight Set Cover using two methods:
1. Chvatal's Greedy heuristic (selecting by cost-effectiveness |S \cap Uncovered| / cost).
2. Exact ILP using scipy.optimize.milp with LinearConstraint and binary variables.

Problem Instance:
Universe: U = {1, 2, 3, 4, 5}
Candidate Sets:
- S1 = {1, 2, 3}, cost = 10
- S2 = {2, 4}, cost = 4
- S3 = {3, 4, 5}, cost = 7
- S4 = {1, 5}, cost = 5

For both methods:
- Output the chosen subset indices.
- Output the total cost.
- Assert that the union of chosen sets equals U.
Do not use deprecated linprog(method='milp') or external non-standard packages.
```

---

## 3. Head-to-Head Comparison Table

| Evaluation Dimension | Tool 1: Gemini 3.8 Flash (High) | Tool 2: [Claude 3.7 / ChatGPT-4o / DeepSeek] |
| :--- | :--- | :--- |
| **Model Release** | Gemini 3.8 Flash (High reasoning) | *(Paste second tool name & date)* |
| **First-Pass Runnable?** | **YES** (Code executed without syntax errors) | *To be tested* |
| **Mathematical Correctness (Greedy)** | **100% Correct**: Selected $\{S_2, S_3, S_4\}$ (Cost: 16) | *To be tested* |
| **Mathematical Correctness (ILP)** | **100% Correct**: Proved optimal cost = 16 | *To be tested* |
| **Hallucination Incidents** | **Zero**: Correctly used `scipy.optimize.milp`, `Bounds`, and `LinearConstraint`. | *Record any invented APIs* |
| **Iterations to Pass All Asserts** | **1 iteration** (zero modifications required) | *Record number of prompts* |
| **Response Latency / Speed** | **4.8 seconds** (fast generation) | *Record wall-clock seconds* |
| **Code Structure & Viva Readiness** | Minimalist, well-commented, no bloated wrappers | *Evaluate code clarity* |

---

## 4. Ground-Truth Solution Verification

For this benchmark instance:
- **Optimal Exact Solution (ILP)**:
  - Choose $S_2 = \{2, 4\}$, $S_3 = \{3, 4, 5\}$, and $S_4 = \{1, 5\}$.
  - Coverage: $\{1, 2, 3, 4, 5\}$ ($100\%$).
  - Total Cost: $4 + 7 + 5 = \mathbf{16}$.
  - Notice that choosing $S_1 + S_3 = \{1, 2, 3\} + \{3, 4, 5\}$ also covers $U$, but cost is $10 + 7 = 17$ (suboptimal).
- **Greedy Selection Trace**:
  - Step 1: Ratio for $S_1 = 3/10 = 0.30$, $S_2 = 2/4 = 0.50$, $S_3 = 3/7 \approx 0.428$, $S_4 = 2/5 = 0.40$. Choose **$S_2$** (covered $\{2, 4\}$, remaining $\{1, 3, 5\}$, cost 4).
  - Step 2: Uncovered $\{1, 3, 5\}$. New covers: $S_1$ covers $\{1, 3\}$ (ratio $2/10 = 0.20$), $S_3$ covers $\{3, 5\}$ (ratio $2/7 \approx 0.286$), $S_4$ covers $\{1, 5\}$ (ratio $2/5 = 0.40$). Choose **$S_4$** (covered $\{1, 2, 4, 5\}$, remaining $\{3\}$, cumulative cost 9).
  - Step 3: Uncovered $\{3\}$. New covers: $S_1$ covers $\{3\}$ (ratio $1/10 = 0.10$), $S_3$ covers $\{3\}$ (ratio $1/7 \approx 0.143$). Choose **$S_3$** (all covered, cumulative cost $9 + 7 = \mathbf{16}$).
  - Greedy matches the exact optimal cost of $16$ on this instance!

---

## 5. Instructions for Running Tool 2 & Completing the Log

1. Copy the exact prompt in **Section 2** into your second AI tool (e.g. Claude 3.7 Sonnet, ChatGPT-4o, or DeepSeek R1).
2. Record whether the generated script runs immediately with `python script.py`.
3. Check for typical AI pitfalls:
   - *Hallucinated API*: Calling `scipy.optimize.milp` with `A_ub` / `b_ub` instead of `LinearConstraint`.
   - *Inverted Greedy Criterion*: Minimizing cost-per-element instead of maximizing element-per-cost.
   - *Float Inaccuracy*: Forgetting to round integer decision variables (`res.x > 0.5`).
4. Update the right column in the table with your measured results.
