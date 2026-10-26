"""
test_discrete_solvers.py
------------------------
Unit Tests for Track B (Discrete Optimization & QUBO/Ising).

Verifies:
  1. Hand-written Branch-and-Bound equals Brute Force and DP on small knapsack instances.
  2. QUBO energy exactly equals -Cut(x) for all possible binary state vectors.
  3. Binary-to-Spin and Spin-to-Binary round-trip conversions preserve states.
  4. Ising Hamiltonian energy matches QUBO energy up to constant offset.
  5. Constraint penalty terms enforce exact cardinality in feature selection QUBO.
"""

import numpy as np
import pytest

from track_B_discrete.code.knapsack_solvers import (
    KnapsackInstance,
    generate_knapsack_instance,
    solve_knapsack_brute_force,
    solve_knapsack_greedy,
    solve_knapsack_dp,
    solve_knapsack_ilp,
    solve_knapsack_branch_and_bound,
)
from track_B_discrete.code.qubo_ising import (
    GraphMaxCut,
    build_maxcut_qubo,
    build_maxcut_ising,
    binary_to_spin,
    spin_to_binary,
    evaluate_qubo_energy,
    evaluate_ising_energy,
    solve_qubo_brute_force,
    build_cardinality_constrained_qubo,
    build_tiny_timetabling_qubo,
)


def test_branch_and_bound_matches_brute_force_and_dp():
    """
    Verifies that the hand-written Branch-and-Bound solver finds the exact
    same global maximum value as Brute Force and Dynamic Programming.
    """
    inst = generate_knapsack_instance(n=12, capacity_ratio=0.5, seed=777)

    val_bf, sol_bf, _ = solve_knapsack_brute_force(inst)
    val_dp, sol_dp, _ = solve_knapsack_dp(inst)
    val_ilp, sol_ilp, _ = solve_knapsack_ilp(inst)
    val_bb, sol_bb, _ = solve_knapsack_branch_and_bound(inst)

    assert val_bf == val_dp, f"DP mismatch: BF={val_bf}, DP={val_dp}"
    assert val_bf == val_ilp, f"ILP mismatch: BF={val_bf}, ILP={val_ilp}"
    assert val_bf == val_bb, f"Branch & Bound mismatch: BF={val_bf}, BB={val_bb}"

    # Verify feasibility of BB solution
    weight_bb = sum(w * x for w, x in zip(inst.weights, sol_bb))
    assert weight_bb <= inst.capacity


def test_qubo_energy_equals_negative_cut_value():
    """
    Verifies that for any random binary configuration x in {0, 1}^N:
      x^T Q x == - Cut(x)
    """
    g = GraphMaxCut(5, [(0, 1, 2.0), (1, 2, 1.5), (2, 3, 3.0), (3, 4, 1.0), (4, 0, 2.5), (1, 4, 0.8)])
    Q = build_maxcut_qubo(g)

    rng = np.random.RandomState(42)
    # Test on 30 random binary state vectors
    for _ in range(30):
        x = rng.randint(0, 2, size=5)
        cut = g.compute_cut_value(x)
        qubo_energy = evaluate_qubo_energy(Q, x)
        assert np.isclose(qubo_energy, -cut), f"Mismatch: Q energy={qubo_energy}, -Cut={-cut} for x={x}"


def test_spin_conversion_round_trip():
    """
    Verifies that binary-to-spin and spin-to-binary conversions are exact inverses:
      x -> s -> x
    """
    rng = np.random.RandomState(42)
    for _ in range(10):
        x = rng.randint(0, 2, size=8)
        s = binary_to_spin(x)
        # Check spins are strictly in {-1, +1}
        assert set(np.unique(s)).issubset({-1, 1})
        x_recon = spin_to_binary(s)
        np.testing.assert_array_equal(x, x_recon)


def test_ising_hamiltonian_matches_qubo_energy():
    """
    Verifies that H_QUBO(x) == H_Ising(s) + offset.
    """
    g = GraphMaxCut(4, [(0, 1, 1.0), (1, 2, 2.0), (2, 3, 1.0), (3, 0, 2.0), (0, 2, 1.5)])
    Q = build_maxcut_qubo(g)
    J, h, offset = build_maxcut_ising(g)

    # Test all 2^4 = 16 states
    for mask in range(16):
        x = np.array([(mask >> i) & 1 for i in range(4)])
        s = binary_to_spin(x)

        e_qubo = evaluate_qubo_energy(Q, x)
        e_ising = evaluate_ising_energy(J, h, s, offset=offset)

        assert np.isclose(e_qubo, e_ising), f"QUBO energy {e_qubo} != Ising energy {e_ising} for x={x}, s={s}"


def test_cardinality_constraint_penalty_enforcement():
    """
    Verifies that adding penalty lambda * (sum x_i - K)^2 enforces the cardinality constraint sum x_i = K.
    """
    # 5 items with linear costs [10, 5, 8, 2, 6]; seek to pick exactly K=2 items minimizing cost
    costs = np.array([10.0, 5.0, 8.0, 2.0, 6.0])
    K = 2
    Q, offset = build_cardinality_constrained_qubo(costs, K=K, penalty_lambda=50.0)

    best_energy, best_x, _ = solve_qubo_brute_force(Q)

    # The two lowest cost items are index 3 (cost 2) and index 1 (cost 5)
    assert np.sum(best_x) == K, f"Cardinality violated! Chosen count={np.sum(best_x)}"
    assert best_x[3] == 1 and best_x[1] == 1, f"Failed to pick minimal cost items: {best_x}"


def test_tiny_timetabling_qubo_clash_penalty():
    """
    Verifies that the tiny 4-variable exam timetabling QUBO prevents scheduling
    conflicting exams in the same time slot.
    """
    Q = build_tiny_timetabling_qubo(penalty_lambda=50.0)
    best_energy, best_x, _ = solve_qubo_brute_force(Q)

    # Expected valid assignment: e1 in slot 0, e2 in slot 1 (or vice versa)
    # x = [x11, x12, x21, x22]
    # e1 in 1 slot: x[0] + x[1] == 1
    # e2 in 1 slot: x[2] + x[3] == 1
    # no clash in slot 1: not (x[0]==1 and x[2]==1)
    # no clash in slot 2: not (x[1]==1 and x[3]==1)
    assert best_x[0] + best_x[1] == 1
    assert best_x[2] + best_x[3] == 1
    assert not (best_x[0] == 1 and best_x[2] == 1)
    assert not (best_x[1] == 1 and best_x[3] == 1)
