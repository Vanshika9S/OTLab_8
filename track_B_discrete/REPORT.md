# Track B: Discrete Optimization & QUBO/Ising — Comprehensive Report

> **Status**: Completed, Benchmark-Verified & Viva-Ready  
> **Course**: Optimization Techniques (Assignment 8, Track B)  
> **Implementations**: [`code/knapsack_solvers.py`](./code/knapsack_solvers.py) and [`code/qubo_ising.py`](./code/qubo_ising.py)  
> **Benchmark Runner**: [`code/run_benchmarks.py`](./code/run_benchmarks.py)  
> **Unit Tests**: [`tests/test_discrete_solvers.py`](./tests/test_discrete_solvers.py) (All 6 passed)  
> **Export for Track C (QAOA)**: [`results/qubo_instances.json`](./results/qubo_instances.json)

---

## 1. Selection & Allocation: 0-1 Knapsack Problem

### Problem Formulation
Given $N$ items, each with value $v_i > 0$ and integer weight $w_i > 0$, and knapsack capacity $W$:
$$\max_{x \in \{0, 1\}^N} \sum_{i=1}^N v_i x_i \quad \text{subject to} \quad \sum_{i=1}^N w_i x_i \le W$$

### Five Solvers Compared
1. **Brute Force (Exhaustive Search)**: Enumerates all $2^N$ bitmasks. Guaranteed global optimum, but exhibits exponential time complexity $O(2^N)$ (prohibitive beyond $N \approx 22$).
2. **Greedy Density Heuristic**: Sorts items by value-to-weight density ratio $r_i = v_i / w_i$ in descending order. Packs items greedily until capacity is reached. Time complexity: $O(N \log N)$.
3. **Dynamic Programming (DP)**: Exact 2D tabulation table $DP[i, w] = \max(DP[i-1, w], DP[i-1, w - w_i] + v_i)$. Runs in pseudo-polynomial time $O(N \cdot W)$ and reconstructs the optimal item subset via backtracking.
4. **Integer Linear Programming (ILP)**: Branch-and-cut solver using HiGHS (`scipy.optimize.milp`), solving LP relaxations at tree nodes and generating cutting planes.
5. **Hand-Written Branch-and-Bound (B&B)**:
   - Sorts items by density $v_i / w_i$ descending.
   - Searches the binary tree using Best-First Search with a priority queue.
   - **Upper Bound**: Solves the *Continuous / Fractional Knapsack Relaxation* at each node in $O(N)$ time (taking a fraction of the first overflow item).
   - **Pruning**: If `upper_bound <= current_best_value`, the entire subtree is pruned immediately!

---

### Empirical Knapsack Scaling Results across Problem Sizes ($N$)

> *All measurements below are `[Hardware-Measured]` on local CPU.*

| Items ($N$) | Capacity ($W$) | Brute Force (ms) | Greedy Heuristic (ms) | Dynamic Prog (ms) | ILP HiGHS (ms) | Branch & Bound (ms) | Exact Optima Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$N = 10$** | 112 | 1.44 ms (Val: 285) | **0.02 ms** (Val: 285) | 0.11 ms (Val: 285) | 44.92 ms (Val: 285) | **0.38 ms** (Val: 285) | **285** (100% agreement) |
| **$N = 20$** | 228 | 1,638.59 ms (Val: 738) | **0.02 ms** (Val: 738) | 0.13 ms (Val: 738) | 8.56 ms (Val: 738) | **0.25 ms** (Val: 738) | **738** (100% agreement) |
| **$N = 50$** | 656 | *(Infeasible: $> 10^{15}$ ops)*| **0.08 ms** (Val: 2161) | 2.13 ms (Val: 2171) | 4.38 ms (Val: 2171) | **1.02 ms** (Val: 2171) | **2171** (Greedy ratio: 99.5%) |
| **$N = 100$** | 1277 | *(Infeasible)* | **0.10 ms** (Val: 3949) | 2.59 ms (Val: 3959) | 40.32 ms (Val: 3959) | **0.53 ms** (Val: 3959) | **3959** (Greedy ratio: 99.7%) |
| **$N = 200$** | 2473 | *(Infeasible)* | **0.05 ms** (Val: 8385) | 2.15 ms (Val: 8387) | 19.18 ms (Val: 8387) | **2.86 ms** (Val: 8387) | **8387** (Greedy ratio: 99.9%) |
| **$N = 500$** | 6274 | *(Infeasible)* | **0.47 ms** (Val: 20945)| 13.22 ms (Val: 20952)| 124.47 ms (Val: 20952)| *(Tree depth cap)* | **20952** (Greedy ratio: 99.9%)|

Generated scaling plot: [`results/knapsack_scaling_comparison.png`](./results/knapsack_scaling_comparison.png).

---

## 2. Max-Cut as QUBO & Ising Model

### 2.1 QUBO Formulation
Given an undirected graph $G = (V, E)$ with edge weights $w_{ij} \ge 0$:
- Binary decision variables: $x_i \in \{0, 1\}$.
- An edge $(i, j)$ is cut if and only if $x_i \neq x_j$, which corresponds to the algebraic indicator:
  $$\mathbb{I}(x_i \neq x_j) = x_i (1 - x_j) + x_j (1 - x_i) = x_i + x_j - 2 x_i x_j$$
- Total cut value:
  $$\text{Cut}(x) = \sum_{(i, j) \in E} w_{ij} (x_i + x_j - 2 x_i x_j)$$
- Since standard QUBO problems are formulated to **minimize** $H_{\text{QUBO}}(x) = x^T Q x$, we set $H_{\text{QUBO}}(x) = -\text{Cut}(x)$:
  $$H_{\text{QUBO}}(x) = \sum_{(i, j) \in E} w_{ij} (2 x_i x_j - x_i - x_j) = x^T Q x$$
  Where the symmetric matrix $Q$ has entries:
  $$Q_{ii} = - \sum_{j \in N(i)} w_{ij} = -\text{degree}(i), \quad Q_{ij} = w_{ij} \quad (i \neq j)$$

### 2.2 Binary-to-Spin Conversion (Ising Hamiltonian)
To map QUBO to quantum hardware (where qubits are Pauli-$Z$ spins), we introduce spin variables $s_i \in \{-1, +1\}$:
$$s_i = 1 - 2 x_i \iff x_i = \frac{1 - s_i}{2}$$

Substituting into the cut expression:
$$\text{Cut}(s) = \sum_{(i, j) \in E} w_{ij} \frac{1 - s_i s_j}{2} = \frac{1}{2} \sum_{(i, j) \in E} w_{ij} - \sum_{(i, j) \in E} \frac{w_{ij}}{2} s_i s_j$$

Minimizing energy is equivalent to the **Ising Spin Glass Hamiltonian**:
$$H_{\text{Ising}}(s) = \sum_{(i, j) \in E} J_{ij} s_i s_j + \sum_{i \in V} h_i s_i$$
Where:
$$J_{ij} = \frac{w_{ij}}{2}, \quad h_i = 0, \quad \text{Energy Offset} = -\frac{1}{2} \sum_{(i, j) \in E} w_{ij}$$

*Verification*: For every configuration, $H_{\text{QUBO}}(x) = H_{\text{Ising}}(s) - \frac{1}{2} \sum w_{ij}$ holds exactly (proven by unit test).

---

## 3. Worked Examples of Constraint Penalties

In QUBO, hard constraints $g(x) = 0$ cannot be expressed as linear inequalities; they must be incorporated as **quadratic penalty terms** $P(x) = \lambda (g(x))^2$ where $\lambda > 0$ is sufficiently large.

### Example A: Feature Selection with Exact Cardinality Constraint
Suppose we select features to minimize linear cost $\sum c_i x_i$ subject to selecting exactly $K$ features: $\sum_{i=1}^N x_i = K$.
$$H(x) = \sum_{i=1}^N c_i x_i + \lambda \left(\sum_{i=1}^N x_i - K\right)^2$$
Expanding the square:
$$\left(\sum_{i=1}^N x_i - K\right)^2 = \left(\sum_{i=1}^N x_i\right)^2 - 2K \sum_{i=1}^N x_i + K^2 = \sum_{i=1}^N x_i^2 + 2 \sum_{i < j} x_i x_j - 2K \sum_{i=1}^N x_i + K^2$$
Since $x_i \in \{0, 1\}$, $x_i^2 = x_i$. Combining linear terms:
$$= (1 - 2K) \sum_{i=1}^N x_i + 2 \sum_{i < j} x_i x_j + K^2$$
The penalty matrix entries are:
- **Diagonal**: $Q_{ii} = c_i + \lambda (1 - 2K)$
- **Off-Diagonal**: $Q_{ij} = 2 \lambda$ for $i < j$
- **Constant Offset**: $\lambda K^2$

*Unit test result*: Tested with costs $[10, 5, 8, 2, 6]$ and $K=2$. The QUBO solver chooses indices $1$ and $3$ (costs 5 and 2), achieving exact cardinality constraint satisfaction without violation.

### Example B: Tiny University Timetabling (Track E) Mapped to QUBO
2 Exams ($e_1, e_2$), 2 Slots ($s_1, s_2$) yielding 4 binary variables $x = [x_{11}, x_{12}, x_{21}, x_{22}]$:
1. Exam 1 in 1 slot: $\lambda_1 (x_{11} + x_{12} - 1)^2$
2. Exam 2 in 1 slot: $\lambda_1 (x_{21} + x_{22} - 1)^2$
3. Conflict penalty: Student in both exams $\implies \lambda_2 (x_{11} x_{21} + x_{12} x_{22})$
The resulting $4 \times 4$ QUBO matrix enforces clash-free timetabling purely through quadratic interaction terms (verified by unit test).

---

## 4. Classical Max-Cut Benchmarks & Export for Track C (QAOA)

All three benchmark graphs were solved to provable optimality via exact Brute Force and verified with Simulated Annealing over **10 deterministic seeds (0 to 9)**:

| Benchmark Graph | Nodes ($|V|$) | Edges ($|E|$) | Exact Max-Cut | Ground Energy ($H^*$) | Optimal Bitstring | SA Mean Energy (10 Seeds) | SA Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`Graph_5Ring`** ($C_5$) | 5 | 5 | **4.0** | **-4.0** | `10100` | **-4.00 ± 0.00** | **10 / 10** (100%) |
| **`Graph_8Cube`** ($Q_3$) | 8 | 12 | **12.0** | **-12.0** | `01011010` | **-12.00 ± 0.00** | **10 / 10** (100%) |
| **`Graph_12ER`** (Erdős-Rényi) | 12 | 18 | **16.0** | **-16.0** | `101011010100` | **-16.00 ± 0.00** | **10 / 10** (100%) |

The instances, graphs, adjacency matrices, QUBO matrices $Q$, Ising coupling matrices $J$, and exact ground states are saved in:
[`track_B_discrete/results/qubo_instances.json`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_B_discrete/results/qubo_instances.json)  
*This file will be directly imported by Track C on Day 6 to benchmark QAOA against these classical baselines.*

Simulated annealing convergence curves: [`track_B_discrete/results/sa_convergence_curves.png`](file:///c:/Users/satye/OneDrive/Desktop/OTLab8/track_B_discrete/results/sa_convergence_curves.png).

---

## 5. Trade-Off Analysis & 5-Line Critical Review

1. *DP Memory Explosion*: Dynamic programming is exact but pseudo-polynomial ($O(N \cdot W)$); if capacity $W$ scales to $10^7$ or weights are continuous floats, DP memory overflows completely.
2. *Greedy Approximation Quality*: The density heuristic is blazing fast ($<0.5$ ms for $N=500$) and achieves $>99\%$ optimality on uniform knapsacks, but can have arbitrary approximation ratios on adversarial pathological instances.
3. *Branch-and-Bound Efficiency*: Hand-written B&B with fractional relaxation bounds drastically outperforms brute force (solving $N=20$ in **0.25 ms** vs 1,638 ms), but exhibits exponential tree depth on hard knapsack instances with identical density ratios.
4. *QUBO Quadratic Bloat*: Converting inequality constraints to quadratic penalties introduces quadratic interactions $x_i x_j$ between all involved variables, transforming sparse problem graphs into dense cliques that require extensive qubit connectivity on quantum hardware.
5. *Penalty Tuning Sensitivity*: If the penalty multiplier $\lambda$ is too small, constraints are violated; if $\lambda$ is too large, it dwarfs the primary objective and creates steep barrier ravines that impede optimization.
