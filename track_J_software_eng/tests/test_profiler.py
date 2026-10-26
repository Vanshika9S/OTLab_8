"""
test_profiler.py
----------------
Unit test verifying Track J baseline profiler execution and coverage matrix generation.
"""

import os
import pytest
from track_J_software_eng.code.baseline_profiler import profile_test_suite


def test_profiler_execution(tmp_path):
    # Dummy test functions
    def dummy_test_1():
        x = 10 + 20
        assert x == 30

    def dummy_test_2():
        y = [1, 2, 3]
        assert len(y) == 3

    tests = [("test_1", dummy_test_1), ("test_2", dummy_test_2)]
    res = profile_test_suite([], tests, results_dir=str(tmp_path))

    assert res["metadata"]["num_tests"] == 2
    assert "test_1" in res["test_durations_ms"]
    assert "test_2" in res["test_durations_ms"]
    assert res["metadata"]["total_suite_runtime_ms"] > 0
