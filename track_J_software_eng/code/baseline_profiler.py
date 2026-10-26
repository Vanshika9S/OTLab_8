"""
baseline_profiler.py
--------------------
Baseline Test-Suite Profiler & Coverage Matrix Collector for Track J.

Measures:
  1. Total execution time of the unoptimized test suite.
  2. Individual runtime duration (ms) for each test case.
  3. Binary Test-to-Code Coverage Matrix A[i, j] (which test i covers code statement j).
  4. Aggregate statement coverage percentage.

Outputs:
  - track_J_software_eng/results/baseline_profile.json
  - track_J_software_eng/results/baseline_profile_summary.csv

This provides the exact empirical input matrix required for Chapter 6 optimization
(Weighted Set Cover via Greedy vs ILP) on Day 13.
"""

import os
import sys
import time
import json
import inspect
from typing import Dict, List, Set, Any
import coverage

# Ensure repo root is accessible
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def profile_test_suite(
    target_module_paths: List[str],
    test_functions: List[tuple],
    results_dir: str = "track_J_software_eng/results",
) -> Dict[str, Any]:
    """
    Executes a list of test functions under fine-grained line coverage instrumentation.

    Parameters:
    -----------
    target_module_paths : Absolute paths to source code files under test.
    test_functions : List of (test_name, callable_func) pairs.
    results_dir : Output directory to store profile results.

    Returns:
    --------
    Dict containing total suite duration, individual test runtimes, and coverage matrix.
    """
    os.makedirs(results_dir, exist_ok=True)

    print(f"\n[Track J Profiler] Profiling test suite ({len(test_functions)} tests) against target codebase...")

    test_durations_ms: Dict[str, float] = {}
    coverage_matrix: Dict[str, List[int]] = {}  # test_name -> list of covered line numbers
    all_covered_lines: Set[int] = set()

    suite_start = time.perf_counter()

    for t_name, t_func in test_functions:
        # Spin up fresh coverage instance per test to isolate individual line footprints
        cov = coverage.Coverage(include=["*validator.py*"])
        cov.start()

        t0 = time.perf_counter()
        try:
            t_func()
            duration_ms = (time.perf_counter() - t0) * 1000.0
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            print(f"  Warning: Test {t_name} failed: {e}")
        finally:
            cov.stop()

        test_durations_ms[t_name] = round(duration_ms, 3)

        # Collect covered lines across target modules
        covered_for_this_test = set()
        cov_data = cov.get_data()
        for f in cov_data.measured_files():
            lines = cov_data.lines(f)
            if lines:
                # Store relative line identifiers
                for ln in lines:
                    covered_for_this_test.add(ln)
                    all_covered_lines.add(ln)

        coverage_matrix[t_name] = sorted(list(covered_for_this_test))

    total_suite_time_ms = (time.perf_counter() - suite_start) * 1000.0

    profile_results = {
        "metadata": {
            "num_tests": len(test_functions),
            "total_statements_covered": len(all_covered_lines),
            "total_suite_runtime_ms": round(total_suite_time_ms, 3),
            "hardware_labeled": "[Hardware-Measured]",
        },
        "test_durations_ms": test_durations_ms,
        "coverage_matrix": coverage_matrix,
        "all_covered_lines": sorted(list(all_covered_lines)),
    }

    # Persist JSON
    json_path = os.path.join(results_dir, "baseline_profile.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile_results, f, indent=2)

    # Persist CSV Summary
    csv_path = os.path.join(results_dir, "baseline_profile_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Test_Name,Runtime_ms,Lines_Covered\n")
        for t_name, dur in test_durations_ms.items():
            lines_count = len(coverage_matrix.get(t_name, []))
            f.write(f"{t_name},{dur},{lines_count}\n")

    print(f"[Track J Profiler] Suite execution complete:")
    print(f"  Total Wall-Clock Time: {total_suite_time_ms:.2f} ms")
    print(f"  Total Unique Statements Covered: {len(all_covered_lines)}")
    print(f"  Results saved to: {json_path} and {csv_path}")

    return profile_results


if __name__ == "__main__":
    # Self-test using Track E validator as sample target codebase
    from track_E_case_study.code.validator import TimetableValidator
    from track_E_case_study.tests.test_validator import (
        tiny_instance,
        test_feasible_schedule_and_exact_metrics,
        test_hard_student_clash_detection,
        test_capacity_violation_detection,
        test_three_plus_per_day_detection,
        test_incomplete_assignment_detection,
    )

    validator_file = os.path.abspath(
        os.path.join(REPO_ROOT, "track_E_case_study", "code", "validator.py")
    )

    inst = {
        "metadata": {
            "name": "tiny_handcrafted",
            "num_students": 2,
            "num_courses": 3,
            "num_slots": 4,
            "slots_per_day": 2,
            "num_days": 2,
            "total_room_capacity_per_slot": 5,
        },
        "course_enrollment_counts": {0: 1, 1: 2, 2: 1},
        "student_enrollments": {0: [0, 1], 1: [1, 2]},
        "conflicts": {"0,1": 1, "1,2": 1},
    }
    tests = [
        ("test_feasible_metrics", lambda: test_feasible_schedule_and_exact_metrics(inst)),
        ("test_clash_detection", lambda: test_hard_student_clash_detection(inst)),
        ("test_capacity_violation", lambda: test_capacity_violation_detection(inst)),
        ("test_three_plus_detection", lambda: test_three_plus_per_day_detection()),
        ("test_incomplete_assignment", lambda: test_incomplete_assignment_detection(inst)),
    ]

    profile_test_suite([validator_file], tests)
