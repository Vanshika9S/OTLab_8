"""
qubo_ising.py
-------------
QUBO and Ising Formulations for Max-Cut and Constrained Combinatorial Optimization.

Mathematical Formulations:
  1. Max-Cut as QUBO:
     Given graph G = (V, E) with weights w_ij.
     Binary decision variable x_i in {0, 1} indicates partition assignment.
     Edge (i, j) is cut if x_i != x_j:
       Cut(x) = sum_{(i, j) in E} w_ij * (x_i + x_j - 2 * x_i * x_j)
     QUBO minimizes H_QUBO(x) = -Cut(x) = x^T Q x.

  2. Binary-to-Spin Conversion (Ising Model):
     Spin variable s_i in {-1, +1}.
     Mapping: s_i = 1 - 2 * x_i  <===>  x_i = (1 - s_i) / 2
     Ising Hamiltonian:
       H_Ising(s) = sum_{(i, j) in E} J_ij * s_i * s_j + sum_i h_i * s_i
       where J_ij = w_ij / 2.
     Relation:
       H_QUBO(x) = H_Ising(s) - 0.5 * sum_{(i, j)} w_ij.

  3. Penalty Term Method for Constraints:
     Encodes equality constraint g(x) = 0 via quadratic penalty P(x) = lambda * (g(x))^2.
     - Cardinality Constraint: sum x_i = K  ===> lambda * (sum x_i - K)^2
     - Timetabling Clash: x_{e1, s} + x_{e2, s} <= 1 ===> lambda * (x_{e1, s} * x_{e2, s})

  4. Classical Solvers:
     - BruteForceQUBO: Exact 2^N state enumeration for small graphs (N <= 16).
     - SimulatedAnnealingQUBO: Metropolis-Hastings Markov Chain Monte Carlo.
"""

import json
import time
import numpy as np
from typing import Dict, List, Tuple, Any, Optional


class GraphMaxCut:
    """Represents an undirected graph for Max-Cut."""

    def __init__(self, num_nodes: int, edges: List[Tuple[int, int, float]]):
        self.num_nodes = num_nodes
        self.edges = edges
        self.adj_matrix = np.zeros((num_nodes, num_nodes), dtype=float)
        for u, v, w in edges:
            self.adj_matrix[u, v] += w
            self.adj_matrix[v, u] += w

    def compute_cut_value(self, x: np.ndarray) -> float:
        """Computes total weight of cut edges where x_u != x_v."""
        cut = 0.0
        for u, v, w in self.edges:
            if x[u] != x[v]:
                cut += w
        return cut


def build_maxcut_qubo(graph: GraphMaxCut) -> np.ndarray:
    """
    Constructs the upper-triangular or symmetric QUBO matrix Q such that:
      x^T Q x = -Cut(x)
    Since Cut(x) = sum_{(u, v)} w_uv * (x_u + x_v - 2 * x_u * x_v):
      -Cut(x) = sum_{(u, v)} w_uv * (2 * x_u * x_v - x_u - x_v)
    Matrix Q entries:
      Diagonal: Q_uu = - sum_{v in N(u)} w_uv = - degree(u)
      Off-diagonal (symmetric): Q_uv = w_uv
    """
    n = graph.num_nodes
    Q = np.zeros((n, n), dtype=float)

    for u in range(n):
        # Diagonal term: - degree(u)
        Q[u, u] = -np.sum(graph.adj_matrix[u, :])
        for v in range(n):
            if u != v:
                # Off-diagonal interaction: + w_uv
                Q[u, v] = graph.adj_matrix[u, v]

    return Q


def binary_to_spin(x: np.ndarray) -> np.ndarray:
    """Converts binary x in {0, 1} to spin s in {+1, -1}: s = 1 - 2*x."""
    return 1 - 2 * x


def spin_to_binary(s: np.ndarray) -> np.ndarray:
    """Converts spin s in {+1, -1} to binary x in {0, 1}: x = (1 - s) / 2."""
    return ((1 - s) // 2).astype(int)


def build_maxcut_ising(graph: GraphMaxCut) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Constructs Ising Hamiltonian parameters:
      H_Ising(s) = sum_{u < v} J_uv * s_u * s_v + sum_u h_u * s_u + offset
    Where J_uv = w_uv / 2, h_u = 0, offset = - 0.5 * sum w_uv.
    """
    n = graph.num_nodes
    J = 0.5 * graph.adj_matrix.copy()
    h = np.zeros(n)
    total_weight = 0.5 * np.sum(graph.adj_matrix)
    offset = -0.5 * total_weight
    return J, h, offset


def evaluate_qubo_energy(Q: np.ndarray, x: np.ndarray) -> float:
    """Evaluates E = x^T Q x."""
    return float(x.T @ Q @ x)


def evaluate_ising_energy(J: np.ndarray, h: np.ndarray, s: np.ndarray, offset: float = 0.0) -> float:
    """Evaluates E = 0.5 * s^T J s + h^T s + offset."""
    return float(0.5 * s.T @ J @ s + h.T @ s + offset)


# ---------------------------------------------------------------------
# Penalty Method Worked Examples
# ---------------------------------------------------------------------
def build_cardinality_constrained_qubo(
    linear_costs: np.ndarray, K: int, penalty_lambda: float = 10.0
) -> Tuple[np.ndarray, float]:
    """
    Feature Selection / Knapsack with Exact Cardinality Constraint:
      Minimize:   sum c_i * x_i
      Subject to: sum x_i = K
    Unconstrained Penalty Formulation:
      H(x) = sum c_i * x_i + lambda * (sum x_i - K)^2
    Expanding:
      (sum x_i - K)^2 = sum x_i^2 + 2 sum_{i<j} x_i x_j - 2K sum x_i + K^2
      Since x_i in {0, 1}, x_i^2 = x_i:
      = sum (1 - 2K) * x_i + 2 sum_{i<j} x_i x_j + K^2
    Returns: (Q, constant_offset)
    """
    n = len(linear_costs)
    Q = np.zeros((n, n))

    for i in range(n):
        # Linear cost + penalty linear contribution
        Q[i, i] = linear_costs[i] + penalty_lambda * (1 - 2 * K)
        for j in range(i + 1, n):
            Q[i, j] = penalty_lambda * 2.0
            Q[j, i] = 0.0  # Upper-triangular convention

    offset = penalty_lambda * (K ** 2)
    return Q, offset


def build_tiny_timetabling_qubo(penalty_lambda: float = 20.0) -> np.ndarray:
    """
    Tiny University Exam Timetabling (Track E instance) mapped to QUBO:
      2 Exams (e1, e2), 2 Time Slots (s1, s2) -> 4 binary variables:
        x = [x_{1,1}, x_{1,2}, x_{2,1}, x_{2,2}]
      Constraint 1 (Exam 1 in exactly 1 slot): (x_{1,1} + x_{1,2} - 1)^2
      Constraint 2 (Exam 2 in exactly 1 slot): (x_{2,1} + x_{2,2} - 1)^2
      Constraint 3 (Clash: Students in both e1 & e2 cannot share slot 1 or slot 2):
        x_{1,1} * x_{2,1} = 0  and  x_{1,2} * x_{2,2} = 0
    Returns 4x4 QUBO matrix Q.
    """
    Q = np.zeros((4, 4))
    # Constraint 1: (x0 + x1 - 1)^2 = -x0 - x1 + 2 x0 x1 + 1
    Q[0, 0] += -penalty_lambda
    Q[1, 1] += -penalty_lambda
    Q[0, 1] += 2.0 * penalty_lambda

    # Constraint 2: (x2 + x3 - 1)^2 = -x2 - x3 + 2 x2 x3 + 1
    Q[2, 2] += -penalty_lambda
    Q[3, 3] += -penalty_lambda
    Q[2, 3] += 2.0 * penalty_lambda

    # Constraint 3 (Clash penalty): lambda * x0 * x2 + lambda * x1 * x3
    Q[0, 2] += penalty_lambda
    Q[1, 3] += penalty_lambda

    return Q


# ---------------------------------------------------------------------
# Classical QUBO Solvers: Brute Force & Simulated Annealing
# ---------------------------------------------------------------------
def solve_qubo_brute_force(Q: np.ndarray) -> Tuple[float, np.ndarray, float]:
    """
    Exhaustive search over all 2^N binary assignments for QUBO: min x^T Q x.
    Feasible for N <= 18.
    """
    start_time = time.perf_counter()
    n = Q.shape[0]
    best_energy = float("inf")
    best_x = np.zeros(n, dtype=int)

    for mask in range(1 << n):
        x = np.array([(mask >> i) & 1 for i in range(n)])
        energy = float(x.T @ Q @ x)
        if energy < best_energy:
            best_energy = energy
            best_x = x

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_energy, best_x, runtime_ms


def solve_qubo_simulated_annealing(
    Q: np.ndarray,
    initial_temp: float = 10.0,
    cooling_rate: float = 0.98,
    num_steps: int = 1000,
    seed: int = 42,
) -> Tuple[float, np.ndarray, float, List[float]]:
    """
    Metropolis-Hastings Simulated Annealing on QUBO state space.
    Single-spin flip proposal with temperature decay T <- cooling_rate * T.
    """
    start_time = time.perf_counter()
    rng = np.random.RandomState(seed)
    n = Q.shape[0]

    # Random initial configuration
    x = rng.randint(0, 2, size=n)
    current_energy = float(x.T @ Q @ x)
    best_energy = current_energy
    best_x = x.copy()

    energy_history = [current_energy]
    T = initial_temp

    for step in range(num_steps):
        # Choose random spin to flip
        flip_idx = rng.randint(0, n)
        x_candidate = x.copy()
        x_candidate[flip_idx] = 1 - x_candidate[flip_idx]

        candidate_energy = float(x_candidate.T @ Q @ x_candidate)
        delta_E = candidate_energy - current_energy

        # Metropolis acceptance rule
        if delta_E < 0 or rng.rand() < np.exp(-delta_E / max(T, 1e-8)):
            x = x_candidate
            current_energy = candidate_energy
            if current_energy < best_energy:
                best_energy = current_energy
                best_x = x.copy()

        energy_history.append(current_energy)
        T *= cooling_rate

    runtime_ms = (time.perf_counter() - start_time) * 1000.0
    return best_energy, best_x, runtime_ms, energy_history
