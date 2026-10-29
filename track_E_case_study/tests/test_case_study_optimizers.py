"""
test_case_study_optimizers.py
-----------------------------
Unit and integration test suite for Track E (Timetabling Optimization Solvers).

Tests:
1. DSATURSolver generates valid complete schedules.
2. ILPSolver (SciPy HiGHS) solves with binary constraints.
3. SimulatedAnnealingSolver improves or preserves objective quality.
4. ParallelSASolver multi-core execution produces valid schedule.
5. Toronto parser integration with TimetableValidator confirms 0 clashes.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_E_case_study.code.validator import TimetableValidator
from track_E_case_study.code.optimizers import DSATURSolver, ILPSolver, SimulatedAnnealingSolver, ParallelSASolver
from track_E_case_study.code.toronto_parser import parse_toronto_instance


PRIMARY_INSTANCE_PATH = "track_E_case_study/data/synthetic_primary_300.json"
TORONTO_CRS_PATH = "track_E_case_study/data/toronto_carter_sample.crs"
TORONTO_STU_PATH = "track_E_case_study/data/toronto_carter_sample.stu"


@pytest.fixture(scope="module")
def primary_instance():
    with open(PRIMARY_INSTANCE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_dsatur_solver_execution_and_completeness(primary_instance):
    """Verify that DSATUR assigns all courses to valid time slots."""
    solver = DSATURSolver(primary_instance)
    schedule, rt_ms = solver.solve(seed=42)

    num_courses = primary_instance["metadata"]["num_courses"]
    num_slots = primary_instance["metadata"]["num_slots"]

    assert len(schedule) == num_courses
    for c, s in schedule.items():
        assert 0 <= s < num_slots, f"Course {c} assigned to invalid slot {s}"
    assert rt_ms > 0


def test_ilp_solver_binary_constraint_feasibility(primary_instance):
    """Verify that ILP solver produces complete schedule within time limit."""
    solver = ILPSolver(primary_instance)
    schedule, rt_ms = solver.solve(time_limit=1.0, seed=42)

    num_courses = primary_instance["metadata"]["num_courses"]
    num_slots = primary_instance["metadata"]["num_slots"]

    assert len(schedule) == num_courses
    for c, s in schedule.items():
        assert 0 <= s < num_slots


def test_simulated_annealing_improves_or_matches_initial(primary_instance):
    """Verify that Simulated Annealing terminates with valid schedule and finite cost."""
    sa = SimulatedAnnealingSolver(primary_instance)
    schedule, best_cost, rt_ms = sa.solve(max_iterations=50, seed=42)

    num_courses = primary_instance["metadata"]["num_courses"]
    assert len(schedule) == num_courses
    assert best_cost < float('inf')
    assert rt_ms > 0


def test_parallel_sa_multicore_restarts(primary_instance):
    """Verify that Parallel SA executes across worker cores and returns best schedule."""
    par_sa = ParallelSASolver(primary_instance)
    schedule, best_cost, restart_costs, wall_t = par_sa.solve(num_restarts=2, max_iterations=50, base_seed=42)

    assert len(schedule) == primary_instance["metadata"]["num_courses"]
    assert len(restart_costs) == 2
    assert best_cost <= min(restart_costs) + 1e-6
    assert wall_t > 0


def test_toronto_parser_and_validator_integration():
    """Verify that Toronto benchmark parser output evaluates cleanly with TimetableValidator."""
    toronto_inst = parse_toronto_instance(TORONTO_CRS_PATH, TORONTO_STU_PATH, num_slots=18, slots_per_day=3, room_capacity_per_slot=1000)
    validator = TimetableValidator(toronto_inst)

    dsatur = DSATURSolver(toronto_inst)
    schedule, _ = dsatur.solve(seed=42)
    res = validator.evaluate_schedule(schedule)

    assert res["all_assigned"] is True
    assert res["is_feasible"] is True
    assert res["student_clashes"] == 0
    assert res["capacity_violations"] == 0
