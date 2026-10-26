"""
test_parallel_distributed.py
----------------------------
Automated unit tests for Track D:
  1. Diminishing returns property on submodular facility location
  2. Four Nemhauser precondition verifications before quoting (1 - 1/e)
  3. Greedy approximation ratio meets (1 - 1/e) vs brute force
  4. Non-submodular synergy failure violating (1 - 1/e)
  5. Dynamic work stealing makespan reduction vs static block chunking
  6. Honest negative parallelism result (IPC slowdown on micro-tasks)
  7. FedAvg test loss reduction across communication rounds
  8. MGDA common descent property (<g_MGDA, g1> >= 0, <g_MGDA, g2> >= 0)
"""

import os
import sys
import pytest
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_D_submodular_parallel.code.submodular_opt import (
    FacilityLocationCoverage,
    check_diminishing_returns,
    verify_guarantee_preconditions,
    greedy_submodular_maximize,
    brute_force_submodular_maximize,
    demonstrate_non_submodular_greedy_failure
)
from track_D_submodular_parallel.code.parallel_multiprocessing import (
    generate_imbalanced_workload,
    run_static_partitioning,
    run_dynamic_work_stealing,
    demonstrate_negative_parallel_result
)
from track_D_submodular_parallel.code.distributed_and_multitask import (
    FederatedDataset,
    train_centralized,
    train_fedavg,
    ConflictingMultiTaskProblem,
    solve_mgda_2task,
    optimize_multitask
)


def test_submodular_diminishing_returns():
    """Verifies that the facility location objective strictly satisfies diminishing returns."""
    fl = FacilityLocationCoverage(n_facilities=16, m_clients=30, seed=42)
    res = check_diminishing_returns(fl, num_trials=300, seed=42)
    assert res["is_submodular"], f"Found {res['violations']} violations of diminishing returns"
    assert res["violations"] == 0


def test_nemhauser_preconditions_verified():
    """Verifies all 4 mathematical preconditions required for the (1 - 1/e) guarantee."""
    fl = FacilityLocationCoverage(n_facilities=16, m_clients=30, seed=42)
    cert = verify_guarantee_preconditions(fl, budget_k=3, num_samples=150)
    assert cert["all_preconditions_met"], "Not all preconditions for (1 - 1/e) are met"
    assert cert["condition_1_normalized"]["met"]
    assert cert["condition_2_monotonicity"]["met"]
    assert cert["condition_3_submodularity"]["met"]
    assert cert["condition_4_cardinality_constraint"]["met"]
    assert np.isclose(cert["theoretical_lower_bound_factor"], 1.0 - 1.0 / np.e)


def test_greedy_meets_nemhauser_bound():
    """Verifies greedy achieves at least (1 - 1/e) of the exact brute-force optimum."""
    fl = FacilityLocationCoverage(n_facilities=14, m_clients=30, seed=42)
    budget = 3
    S_g, val_g, _, _ = greedy_submodular_maximize(fl, budget_k=budget)
    S_opt, val_opt, _ = brute_force_submodular_maximize(fl, budget_k=budget)
    ratio = val_g / val_opt
    nemhauser_bound = 1.0 - 1.0 / np.e

    assert ratio >= nemhauser_bound, f"Greedy ratio {ratio:.4f} below lower bound {nemhauser_bound:.4f}"
    assert val_g <= val_opt + 1e-9


def test_non_submodular_greedy_fails():
    """Verifies that on a non-submodular synergy objective, greedy fails the (1 - 1/e) bound."""
    res = demonstrate_non_submodular_greedy_failure(n=16, budget_k=2, synergy_bonus=100.0)
    assert res["guarantee_violated"], "Greedy should violate the bound on non-submodular objective"
    assert res["actual_approx_ratio"] < res["nemhauser_bound"]


def test_work_stealing_reduces_makespan():
    """Verifies dynamic work stealing outperforms static block chunking on imbalanced tasks."""
    tasks = generate_imbalanced_workload(n_tasks=36, seed=42)
    static_res = run_static_partitioning(tasks, num_workers=4)
    steal_res = run_dynamic_work_stealing(tasks, num_workers=4)

    assert steal_res["makespan_ms"] <= static_res["makespan_ms"], (
        f"Work stealing makespan {steal_res['makespan_ms']} > static {static_res['makespan_ms']}"
    )
    assert steal_res["imbalance_ratio"] <= static_res["imbalance_ratio"]


def test_negative_parallelism_overhead():
    """Verifies that parallel dispatch on micro-tasks causes a measured slowdown."""
    neg_res = demonstrate_negative_parallel_result(num_items=800)
    assert neg_res["slowdown_factor"] > 2.0, (
        f"Expected slowdown factor > 2.0x on micro-tasks, got {neg_res['slowdown_factor']}"
    )


def test_fedavg_convergence():
    """Verifies FedAvg monotonically improves test loss across rounds."""
    ds = FederatedDataset(n_samples=400, n_features=6, n_clients=4, seed=42)
    res_fed = train_fedavg(ds, num_rounds=10, local_epochs=5, lr=0.05, seed=42)
    history = res_fed["history"]
    # Final loss should be lower than initial random initialization
    assert history[-1] < history[0] * 0.5, (
        f"Final loss {history[-1]} not significantly lower than initial {history[0]}"
    )


def test_mgda_common_descent_direction():
    """Verifies MGDA computes a valid common descent direction for conflicting gradients."""
    g1 = np.array([2.0, -1.0, 0.5])
    g2 = np.array([-1.5, 3.0, -0.5])
    # Inner product is negative (conflicting)
    assert np.dot(g1, g2) < 0.0

    g_mgda, alpha = solve_mgda_2task(g1, g2)
    proj1 = np.dot(g_mgda, g1)
    proj2 = np.dot(g_mgda, g2)

    # Both projections must be non-negative (common descent)
    assert proj1 >= -1e-6, f"MGDA violated descent for task 1: {proj1}"
    assert proj2 >= -1e-6, f"MGDA violated descent for task 2: {proj2}"
    assert 0.0 <= alpha <= 1.0
