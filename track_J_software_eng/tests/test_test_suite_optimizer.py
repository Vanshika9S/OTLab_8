"""
test_test_suite_optimizer.py
----------------------------
Unit tests for Track J test-suite optimization algorithms:
- Greedy Set Cover correctness & coverage preservation.
- Exact ILP optimality & coverage preservation.
- Mutation kill score preservation.
- Budget prioritization coverage monotonicity.
- Chvatal approximation ratio guarantee.
"""

import math
import numpy as np
import pytest

from track_J_software_eng.code.test_suite_model import RegressionTestSuiteModel
from track_J_software_eng.code.test_suite_optimizer import TestSuiteOptimizer


@pytest.fixture
def test_setup():
    model = RegressionTestSuiteModel(seed=42)
    optimizer = TestSuiteOptimizer(model)
    return model, optimizer


def test_naive_suite_covers_all_statements(test_setup):
    model, optimizer = test_setup
    res = optimizer.solve_naive_full_suite()
    assert res["num_selected"] == 25
    assert res["coverage_pct"] == 100.0
    assert res["mutation_score_pct"] == 100.0


def test_greedy_set_cover_preserves_100pct_coverage(test_setup):
    model, optimizer = test_setup
    res = optimizer.solve_greedy_set_cover()
    # Greedy must cover 100% of statements
    assert res["coverage_pct"] == 100.0
    # Must save time over full suite
    assert res["runtime_saved_pct"] > 15.0
    # Must kill 100% of mutants
    assert res["mutation_score_pct"] == 100.0


def test_ilp_exact_set_cover_preserves_100pct_coverage(test_setup):
    model, optimizer = test_setup
    res = optimizer.solve_ilp_exact_set_cover()
    assert res["coverage_pct"] == 100.0
    assert res["runtime_saved_pct"] > 25.0
    assert res["mutation_score_pct"] == 100.0


def test_ilp_achieves_better_or_equal_runtime_than_greedy(test_setup):
    model, optimizer = test_setup
    greedy = optimizer.solve_greedy_set_cover()
    ilp = optimizer.solve_ilp_exact_set_cover()
    # ILP is mathematically exact minimum cost
    assert ilp["suite_runtime_ms"] <= greedy["suite_runtime_ms"] + 1e-6
    assert ilp["num_selected"] <= greedy["num_selected"]


def test_chvatal_harmonic_approximation_bound(test_setup):
    model, optimizer = test_setup
    greedy = optimizer.solve_greedy_set_cover()
    ilp = optimizer.solve_ilp_exact_set_cover()
    
    # Chvatal theorem: Cost(Greedy) <= H(|S|) * Cost(ILP)
    num_s = optimizer.num_statements
    h_s = sum(1.0 / k for k in range(1, num_s + 1))
    
    ratio = greedy["suite_runtime_ms"] / ilp["suite_runtime_ms"]
    assert ratio <= h_s


def test_budget_prioritization_monotonicity(test_setup):
    model, optimizer = test_setup
    b30 = optimizer.solve_budget_constrained_prioritization(0.30)
    b50 = optimizer.solve_budget_constrained_prioritization(0.50)
    b80 = optimizer.solve_budget_constrained_prioritization(0.80)
    
    # Larger budget must cover >= statements
    assert b50["statements_covered"] >= b30["statements_covered"]
    assert b80["statements_covered"] >= b50["statements_covered"]
    assert b80["coverage_pct"] == 100.0


def test_mutation_score_preservation(test_setup):
    model, optimizer = test_setup
    naive = optimizer.solve_naive_full_suite()
    greedy = optimizer.solve_greedy_set_cover()
    ilp = optimizer.solve_ilp_exact_set_cover()
    
    assert naive["mutants_killed"] == 10
    assert greedy["mutants_killed"] == 10
    assert ilp["mutants_killed"] == 10
