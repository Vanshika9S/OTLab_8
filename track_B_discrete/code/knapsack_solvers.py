"""
knapsack_solvers.py
-------------------
Selection & Combinatorial Optimization Solvers for the 0-1 Knapsack Problem.

Problem Formulation:
  Maximize:   sum_{i=1}^N v_i * x_i
  Subject to: sum_{i=1}^N w_i * x_i <= W
              x_i in {0, 1}

Solvers Implemented:
  1. BruteForceKnapsack: Exhaustive 2^N combination search (Exact baseline).
  2. GreedyKnapsack: Value-to-weight density ratio heuristic (O(N log N)).
  3. DynamicProgrammingKnapsack: Exact 2D/1D tabulation (O(N * W)).
  4. ILPKnapsack: Exact Integer Linear Programming via PuLP (Branch-and-Cut).
  5. BranchAndBoundKnapsack: Hand-written exact Branch-and-Bound with
     fractional knapsack linear relaxation upper bounds.
"""

import time
import heapq
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pulp


class KnapsackInstance:
    """Represents a 0-1 Knapsack problem instance."""

    def __init__(self, values: List[int], weights: List[int], capacity: int):
        assert len(values) == len(weights), "Values and weights must have identical length"
        self.values = [int(v) for v in values]
        self.weights = [int(w) for w in weights]
        self.capacity = int(capacity)
        self.n = len(values)


def generate_knapsack_instance(n: int, capacity_ratio: float = 0.5, seed: int = 42) -> KnapsackInstance:
    """Generates synthetic 0-1 Knapsack instance with positive integer weights and values."""
    rng = np.random.RandomState(seed)
    weights = rng.randint(1, 50, size=n).tolist()
    values = rng.randint(10, 100, size=n).tolist()
    capacity = int(sum(weights) * capacity_ratio)
    return KnapsackInstance(values, weights, capacity)


# ---------------------------------------------------------------------
# 1. Brute Force (Exhaustive Search)
# ---------------------------------------------------------------------
def solve_knapsack_brute_force(inst: KnapsackInstance) -> Tuple[int, List[int], float]:
    """
    Exhaustive search over all 2^N binary assignments.
    Complexity: O(2^N). Feasible only for N <= 22.
    """
    start_time = time.perf_counter()
    n = inst.n
    best_value = 0
    best_solution = [0] * n

    for mask in range(1 << n):
        cur_weight = 0
        cur_val = 0
        for i in range(n):
            if (mask >> i) & 1:
                cur_weight += inst.weights[i]
                cur_val += inst.values[i]
                if cur_weight > inst.capacity:
                    break
        if cur_weight <= inst.capacity and cur_val > best_value:
            best_value = cur_val
            best_solution = [(mask >> i) & 1 for i in range(n)]

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_value, best_solution, runtime_ms


# ---------------------------------------------------------------------
# 2. Greedy Density Ratio Heuristic
# ---------------------------------------------------------------------
def solve_knapsack_greedy(inst: KnapsackInstance) -> Tuple[int, List[int], float]:
    """
    Greedy heuristic: Sorts items by value-to-weight density ratio (v_i / w_i) descending.
    Packs items greedily while capacity permits.
    Complexity: O(N log N).
    """
    start_time = time.perf_counter()
    n = inst.n
    # Pair items with original indices: (density, value, weight, index)
    items = []
    for i in range(n):
        density = inst.values[i] / inst.weights[i]
        items.append((density, inst.values[i], inst.weights[i], i))

    items.sort(key=lambda x: x[0], reverse=True)

    solution = [0] * n
    total_val = 0
    current_weight = 0

    for density, v, w, orig_idx in items:
        if current_weight + w <= inst.capacity:
            solution[orig_idx] = 1
            total_val += v
            current_weight += w

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return total_val, solution, runtime_ms


# ---------------------------------------------------------------------
# 3. Dynamic Programming (Exact Tabulation)
# ---------------------------------------------------------------------
def solve_knapsack_dp(inst: KnapsackInstance) -> Tuple[int, List[int], float]:
    """
    Classic Dynamic Programming table: dp[i][w] = max value using subset of first i items with capacity w.
    Complexity: O(N * W) time and memory.
    """
    start_time = time.perf_counter()
    n = inst.n
    W = inst.capacity

    # 2D table for backtracking item selections
    dp = np.zeros((n + 1, W + 1), dtype=int)

    for i in range(1, n + 1):
        v = inst.values[i - 1]
        w = inst.weights[i - 1]
        # Previous row values
        dp[i, :] = dp[i - 1, :]
        if w <= W:
            dp[i, w:] = np.maximum(dp[i - 1, w:], dp[i - 1, : W + 1 - w] + v)

    best_value = int(dp[n, W])

    # Backtrack to find chosen items
    solution = [0] * n
    curr_w = W
    for i in range(n, 0, -1):
        if dp[i, curr_w] != dp[i - 1, curr_w]:
            solution[i - 1] = 1
            curr_w -= inst.weights[i - 1]

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_value, solution, runtime_ms


# ---------------------------------------------------------------------
# 4. Integer Linear Programming (Exact Branch-and-Cut via SciPy HiGHS)
# ---------------------------------------------------------------------
def solve_knapsack_ilp(inst: KnapsackInstance) -> Tuple[int, List[int], float]:
    """
    Exact Branch-and-Cut ILP solver using SciPy's HiGHS solver (scipy.optimize.milp).
    Maximizes sum v_i * x_i subject to sum w_i * x_i <= W and x_i in {0, 1}.
    """
    from scipy.optimize import milp, LinearConstraint, Bounds

    start_time = time.perf_counter()
    n = inst.n

    # milp minimizes c^T x, so c = -values
    c = -np.array(inst.values, dtype=float)
    A = np.array([inst.weights], dtype=float)
    constraints = LinearConstraint(A, lb=0, ub=inst.capacity)
    integrality = np.ones(n)  # All variables integer (binary)
    bounds = Bounds(lb=0, ub=1)

    res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)

    best_value = int(round(-res.fun))
    solution = [int(round(xi)) for xi in res.x]

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_value, solution, runtime_ms


# ---------------------------------------------------------------------
# 5. Hand-Written Branch-and-Bound
# ---------------------------------------------------------------------
class Node:
    """State node in the Branch-and-Bound search tree."""

    def __init__(self, level: int, value: int, weight: int, bound: float, items: List[int]):
        self.level = level
        self.value = value
        self.weight = weight
        self.bound = bound
        self.items = items

    # For max-priority queue (heapq is min-heap, so invert bound)
    def __lt__(self, other):
        return self.bound > other.bound


def fractional_knapsack_bound(
    level: int, current_val: int, current_weight: int, capacity: int, sorted_items: List[Tuple[float, int, int, int]]
) -> float:
    """
    Computes upper bound via Continuous/Fractional Knapsack Relaxation.
    Greedily packs items from 'level' onwards; allows taking a fraction of the first item that overflows.
    """
    if current_weight >= capacity:
        return 0.0

    bound = float(current_val)
    weight_left = capacity - current_weight
    n = len(sorted_items)

    for i in range(level, n):
        _, v, w, _ = sorted_items[i]
        if w <= weight_left:
            weight_left -= w
            bound += v
        else:
            # Take fraction of this item to completely fill remaining capacity
            bound += v * (weight_left / w)
            break

    return bound


def solve_knapsack_branch_and_bound(inst: KnapsackInstance) -> Tuple[int, List[int], float]:
    """
    Hand-written exact Branch-and-Bound solver.
    1. Sorts items by value-to-weight density descending.
    2. Explores the binary decision tree (include vs exclude item).
    3. At each node, computes a rigorous upper bound via fractional relaxation.
    4. Prunes subtrees where upper_bound <= current_best_value.
    """
    start_time = time.perf_counter()
    n = inst.n

    # Sort items by density descending
    sorted_items = []
    for i in range(n):
        density = inst.values[i] / inst.weights[i]
        sorted_items.append((density, inst.values[i], inst.weights[i], i))
    sorted_items.sort(key=lambda x: x[0], reverse=True)

    # Priority queue for Best-First Search
    pq = []
    initial_bound = fractional_knapsack_bound(0, 0, 0, inst.capacity, sorted_items)
    root = Node(level=0, value=0, weight=0, bound=initial_bound, items=[])
    heapq.heappush(pq, root)

    best_value = 0
    best_items_indices: List[int] = []

    while pq:
        curr = heapq.heappop(pq)

        # Prune if bound cannot beat best known value
        if curr.bound <= best_value:
            continue

        if curr.level == n:
            if curr.value > best_value:
                best_value = curr.value
                best_items_indices = curr.items
            continue

        _, v, w, orig_idx = sorted_items[curr.level]

        # Branch 1: INCLUDE item curr.level (if capacity allows)
        if curr.weight + w <= inst.capacity:
            inc_val = curr.value + v
            inc_weight = curr.weight + w
            inc_items = curr.items + [orig_idx]
            inc_bound = fractional_knapsack_bound(curr.level + 1, inc_val, inc_weight, inst.capacity, sorted_items)

            if inc_val > best_value:
                best_value = inc_val
                best_items_indices = inc_items

            if inc_bound > best_value:
                heapq.heappush(pq, Node(curr.level + 1, inc_val, inc_weight, inc_bound, inc_items))

        # Branch 2: EXCLUDE item curr.level
        exc_bound = fractional_knapsack_bound(curr.level + 1, curr.value, curr.weight, inst.capacity, sorted_items)
        if exc_bound > best_value:
            heapq.heappush(pq, Node(curr.level + 1, curr.value, curr.weight, exc_bound, curr.items))

    solution = [0] * n
    for idx in best_items_indices:
        solution[idx] = 1

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_value, solution, runtime_ms
