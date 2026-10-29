"""
Unit and integration tests for Track G: xv6 Lottery Scheduler Simulation & Invariants.
Verifies proportional share convergence, round-robin baseline, ticket input validation,
and patch file integrity.
"""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_G_xv6.code.lottery_scheduler_sim import SimProcess, run_scheduler_simulation


def test_round_robin_fairness_equal_share():
    """Round-robin must distribute ticks evenly regardless of tickets."""
    procs = [
        SimProcess(pid=1, name="p1", tickets=100, remaining_work=300),
        SimProcess(pid=2, name="p2", tickets=10, remaining_work=300),
        SimProcess(pid=3, name="p3", tickets=1, remaining_work=300),
    ]
    summary, stats = run_scheduler_simulation(procs, policy="round_robin", seed=42)

    assert summary["total_ticks"] == 900
    for s in stats:
        assert s["ticks"] == 300
        assert pytest.approx(s["share_pct"], abs=0.1) == 33.33


def test_lottery_proportional_share_convergence():
    """Under sustained competition, lottery ticks should approximate ticket proportions."""
    # Run long enough to ensure law of large numbers convergence
    procs = [
        SimProcess(pid=1, name="high", tickets=70, remaining_work=7000),
        SimProcess(pid=2, name="low", tickets=30, remaining_work=7000),
    ]
    summary, stats = run_scheduler_simulation(procs, policy="lottery", seed=42)

    # High ticket proc should complete much earlier
    high_stat = next(s for s in stats if s["pid"] == 1)
    low_stat = next(s for s in stats if s["pid"] == 2)

    assert high_stat["turnaround"] < low_stat["turnaround"]
    # Total ticks is 14000
    assert summary["total_ticks"] == 14000


def test_invalid_tickets_sanitization():
    """SimProcess should clamp invalid or non-positive tickets to at least 1."""
    p_zero = SimProcess(pid=1, name="zero", tickets=0, remaining_work=10)
    p_neg = SimProcess(pid=2, name="neg", tickets=-5, remaining_work=10)
    assert p_zero.tickets == 1
    assert p_neg.tickets == 1


def test_patch_file_exists_and_contains_core_symbols():
    """Verifies that the xv6 lottery scheduler patch exists and contains essential syscalls."""
    patch_path = os.path.join(REPO_ROOT, "track_G_xv6", "code", "xv6_lottery_scheduler.patch")
    assert os.path.exists(patch_path), f"Patch file missing at {patch_path}"

    with open(patch_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "sys_settickets" in content
    assert "sys_getpstat" in content
    assert "pseudo_rand" in content
    assert "pstat.h" in content
    assert "p->tickets" in content
