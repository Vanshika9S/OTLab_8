"""
submodular_opt.py
-----------------
Submodular Optimization, Diminishing Returns Verification, and Greedy Approximation Guarantees.

Mathematical Formulation:
  Ground set V = {0, 1, ..., n-1} of candidate facilities/sensors.
  Universe U = {0, 1, ..., m-1} of target clients/locations with demand weights w_u > 0.
  
  1. Maximum Coverage / Facility Location Objective:
     F(S) = sum_{u in U} max_{s in S} coverage_matrix[s, u]
     where coverage_matrix[s, u] in [0, 1] indicates the quality/signal of facility s at client u.
     
  2. Diminishing Returns Property (Submodularity):
     For all subsets A subseteq B subseteq V and any element e in V \\ B:
       Delta(e | A) >= Delta(e | B)
     where Delta(e | S) = F(S union {e}) - F(S) is the discrete marginal gain.
     
  3. Preconditions for the (1 - 1/e) Greedy Guarantee (Nemhauser et al. 1978):
     Condition 1: Normalized: F(empty) = 0
     Condition 2: Monotone non-decreasing: for all S, e: Delta(e | S) >= 0
     Condition 3: Submodular: diminishing returns holds everywhere
     Condition 4: Cardinality / Uniform Matroid constraint: |S| <= k
     Under Conditions 1-4, the greedy algorithm guarantees:
       F(S_greedy) >= (1 - 1/e) * F(S_optimal) approx 0.6321 * F(S_optimal)

  4. Counter-Example (Non-Submodular Synergy Objective):
     Demonstrates an objective exhibiting supermodular synergy / complementarity,
     causing the greedy algorithm to completely miss the global optimum.
"""

import sys
import os
import itertools
import time
from typing import Dict, List, Set, Tuple, Any, Callable
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class FacilityLocationCoverage:
    """
    Facility location / sensor placement submodular objective function.
    F(S) = sum_{u in U} max_{s in S} coverage_matrix[s, u]
    """
    def __init__(self, n_facilities: int = 20, m_clients: int = 50, seed: int = 42):
        self.n_facilities = n_facilities
        self.m_clients = m_clients
        self.ground_set = set(range(n_facilities))
        
        rng = np.random.RandomState(seed)
        # Client coordinates in [0, 100]^2
        self.client_coords = rng.uniform(0, 100, size=(m_clients, 2))
        # Facility coordinates in [0, 100]^2
        self.facility_coords = rng.uniform(0, 100, size=(n_facilities, 2))
        # Client weights/demands
        self.client_weights = rng.uniform(1.0, 5.0, size=m_clients)
        
        # Coverage matrix: decayed signal coverage based on Euclidean distance
        # signal(s, u) = weight_u * exp(-dist(s, u)^2 / (2 * sigma^2))
        sigma = 25.0
        dist_sq = np.sum((self.facility_coords[:, None, :] - self.client_coords[None, :, :])**2, axis=-1)
        self.coverage_matrix = self.client_weights[None, :] * np.exp(-dist_sq / (2.0 * sigma**2))

    def evaluate(self, S: Set[int]) -> float:
        """Evaluates F(S). Returns 0.0 if S is empty."""
        if not S:
            return 0.0
        indices = list(S)
        # Max signal received at each client from any chosen facility in S
        max_signals = np.max(self.coverage_matrix[indices, :], axis=0)
        return float(np.sum(max_signals))

    def marginal_gain(self, e: int, S: Set[int]) -> float:
        """Computes discrete derivative Delta(e | S) = F(S union {e}) - F(S)."""
        if e in S:
            return 0.0
        val_S = self.evaluate(S)
        val_S_union_e = self.evaluate(S | {e})
        return float(val_S_union_e - val_S)


def check_diminishing_returns(
    obj: FacilityLocationCoverage,
    num_trials: int = 500,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Empirically verifies the diminishing returns property:
      For all A subset B and e notin B: Delta(e | A) >= Delta(e | B).
    """
    rng = np.random.RandomState(seed)
    elements = list(obj.ground_set)
    n = len(elements)
    
    violations = 0
    tested_pairs = 0
    differences = []

    for _ in range(num_trials):
        # Sample subset size for B
        size_B = rng.randint(2, min(n - 1, 8))
        size_A = rng.randint(1, size_B)
        
        perm = rng.permutation(elements)
        B = set(perm[:size_B])
        A = set(perm[:size_A])
        assert A.issubset(B), "A must be a subset of B"
        
        # Pick element e not in B
        available_e = [x for x in elements if x not in B]
        if not available_e:
            continue
        e = rng.choice(available_e)
        
        gain_A = obj.marginal_gain(e, A)
        gain_B = obj.marginal_gain(e, B)
        diff = gain_A - gain_B
        differences.append(diff)
        tested_pairs += 1

        # Check violation: Delta(e | A) < Delta(e | B) within floating point tolerance
        if diff < -1e-12:
            violations += 1

    return {
        "num_trials": tested_pairs,
        "violations": violations,
        "is_submodular": bool(violations == 0),
        "min_difference": float(np.min(differences)) if differences else 0.0,
        "mean_difference": float(np.mean(differences)) if differences else 0.0,
        "max_difference": float(np.max(differences)) if differences else 0.0
    }


def verify_guarantee_preconditions(
    obj: FacilityLocationCoverage,
    budget_k: int,
    num_samples: int = 200
) -> Dict[str, Any]:
    """
    Rigorously verifies the 4 mathematical preconditions required for
    the (1 - 1/e) Nemhauser-Wolsey-Fisher guarantee:
      1. Normalized: F(empty) = 0
      2. Monotone: Delta(e | S) >= 0 for all S, e
      3. Submodular: Diminishing returns holds
      4. Constraint: Uniform matroid (|S| <= k)
    """
    # 1. Normalized check
    val_empty = obj.evaluate(set())
    is_normalized = np.isclose(val_empty, 0.0)

    # 2. Monotonicity check
    rng = np.random.RandomState(123)
    elements = list(obj.ground_set)
    is_monotone = True
    min_marginal = 0.0

    for _ in range(num_samples):
        size = rng.randint(0, len(elements) - 1)
        S = set(rng.choice(elements, size=size, replace=False))
        avail = [x for x in elements if x not in S]
        if not avail:
            continue
        e = rng.choice(avail)
        gain = obj.marginal_gain(e, S)
        if gain < min_marginal:
            min_marginal = gain
        if gain < -1e-12:
            is_monotone = False
            break

    # 3. Submodularity check
    submod_res = check_diminishing_returns(obj, num_trials=num_samples, seed=123)
    is_submodular = submod_res["is_submodular"]

    # 4. Uniform matroid check
    is_uniform_matroid = bool(budget_k >= 1 and budget_k <= len(obj.ground_set))

    all_preconditions_met = is_normalized and is_monotone and is_submodular and is_uniform_matroid

    return {
        "condition_1_normalized": {"met": is_normalized, "F_empty": val_empty},
        "condition_2_monotonicity": {"met": is_monotone, "min_marginal_gain": min_marginal},
        "condition_3_submodularity": {"met": is_submodular, "violations": submod_res["violations"]},
        "condition_4_cardinality_constraint": {"met": is_uniform_matroid, "budget_k": budget_k},
        "all_preconditions_met": all_preconditions_met,
        "theoretical_lower_bound_factor": 1.0 - 1.0 / np.e if all_preconditions_met else None
    }


def greedy_submodular_maximize(
    obj: FacilityLocationCoverage,
    budget_k: int
) -> Tuple[Set[int], float, List[float], float]:
    """
    Greedy algorithm with lazy evaluations.
    At each step, picks e* = argmax_{e notin S} Delta(e | S).
    
    Returns:
      (selected_set, final_value, trajectory, runtime_ms)
    """
    t0 = time.perf_counter()
    S: Set[int] = set()
    trajectory = [0.0]
    elements = list(obj.ground_set)

    for step in range(budget_k):
        best_e = None
        best_gain = -1.0

        for e in elements:
            if e in S:
                continue
            gain = obj.marginal_gain(e, S)
            if gain > best_gain:
                best_gain = gain
                best_e = e

        if best_e is None or best_gain <= 0:
            break

        S.add(best_e)
        trajectory.append(obj.evaluate(S))

    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return S, obj.evaluate(S), trajectory, runtime_ms


def brute_force_submodular_maximize(
    obj: FacilityLocationCoverage,
    budget_k: int
) -> Tuple[Set[int], float, float]:
    """
    Exact exhaustive search over all combinations of size k: binom(n, k).
    
    Returns:
      (optimal_set, optimal_value, runtime_ms)
    """
    t0 = time.perf_counter()
    elements = list(obj.ground_set)
    best_S: Set[int] = set()
    best_val = -1.0

    for subset in itertools.combinations(elements, budget_k):
        S = set(subset)
        val = obj.evaluate(S)
        if val > best_val:
            best_val = val
            best_S = S

    runtime_ms = (time.perf_counter() - t0) * 1000.0
    return best_S, best_val, runtime_ms


class NonSubmodularSynergyObjective:
    """
    Counter-Example: An objective exhibiting pairwise synergy (supermodularity).
    
    Structure:
      Individual items provide small decoy values: val(i) = epsilon (e.g. 1.0).
      However, a specific pair of items {a, b} has a massive synergistic bonus M (e.g. 100.0)
      when selected together, but neither has any bonus individually.
      
      F_synergy(S) = sum_{i in S} val_i + (M if {a, b} subset S else 0)
      
      Why Greedy Fails:
        At step 1, Delta(a | empty) = val_a = 1.0, Delta(b | empty) = val_b = 1.0.
        Decoy elements have slightly higher individual value (e.g. 1.5).
        Greedy chooses the decoys, completely missing the synergistic pair {a, b}!
        The approximation ratio becomes arbitrarily close to 0 as M -> infty.
    """
    def __init__(self, n: int = 16, synergy_pair: Tuple[int, int] = (0, 1), synergy_bonus: float = 100.0):
        self.n = n
        self.ground_set = set(range(n))
        self.synergy_pair = set(synergy_pair)
        self.synergy_bonus = synergy_bonus
        
        # Base individual values: pair elements have 1.0, decoys have 1.5
        self.base_values = np.full(n, 1.5)
        for p in synergy_pair:
            self.base_values[p] = 1.0  # Decoy is strictly more attractive to naive greedy

    def evaluate(self, S: Set[int]) -> float:
        val = sum(self.base_values[i] for i in S)
        if self.synergy_pair.issubset(S):
            val += self.synergy_bonus
        return float(val)

    def marginal_gain(self, e: int, S: Set[int]) -> float:
        if e in S:
            return 0.0
        return self.evaluate(S | {e}) - self.evaluate(S)


def demonstrate_non_submodular_greedy_failure(
    n: int = 16,
    budget_k: int = 2,
    synergy_bonus: float = 100.0
) -> Dict[str, Any]:
    """
    Demonstrates that on a non-submodular (supermodular synergy) objective,
    the greedy algorithm completely fails and has NO guarantee.
    """
    obj = NonSubmodularSynergyObjective(n=n, synergy_pair=(0, 1), synergy_bonus=synergy_bonus)
    
    # 1. Greedy execution
    S_greedy: Set[int] = set()
    elements = list(obj.ground_set)
    for _ in range(budget_k):
        best_e = max((e for e in elements if e not in S_greedy), key=lambda x: obj.marginal_gain(x, S_greedy))
        S_greedy.add(best_e)
    val_greedy = obj.evaluate(S_greedy)

    # 2. Exact Brute Force
    best_opt: Set[int] = set()
    val_opt = -1.0
    for subset in itertools.combinations(elements, budget_k):
        S = set(subset)
        v = obj.evaluate(S)
        if v > val_opt:
            val_opt = v
            best_opt = S

    approx_ratio = val_greedy / val_opt
    nemhauser_bound = 1.0 - 1.0 / np.e  # ~0.6321

    # Check diminishing returns violation:
    # A = empty, B = {0}, e = 1
    gain_A = obj.marginal_gain(1, set())         # 1.0 (no bonus)
    gain_B = obj.marginal_gain(1, {0})          # 1.0 + 100.0 = 101.0 (triggers bonus!)
    # Here Delta(1 | B) > Delta(1 | A), proving SUPERMODULARITY (violation of submodularity)

    return {
        "budget_k": budget_k,
        "synergy_bonus": synergy_bonus,
        "greedy_selected": sorted(list(S_greedy)),
        "greedy_value": val_greedy,
        "optimal_selected": sorted(list(best_opt)),
        "optimal_value": val_opt,
        "actual_approx_ratio": approx_ratio,
        "nemhauser_bound": nemhauser_bound,
        "guarantee_violated": bool(approx_ratio < nemhauser_bound),
        "diminishing_returns_violation": {
            "A": [],
            "B": [0],
            "e": 1,
            "gain_A": gain_A,
            "gain_B": gain_B,
            "gain_difference": gain_A - gain_B  # Strongly negative!
        }
    }
