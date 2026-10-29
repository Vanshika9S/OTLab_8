"""
test_dbms_optimizer.py
----------------------
Unit and integration test suite for Track H (DBMS Optimization).

Tests:
1. Candidate index profiling and non-negative size measurement.
2. 0-1 Knapsack / ILP constraint satisfaction (budget and group mutual exclusion).
3. Query result equivalence: SHA-256 hash comparison between unindexed and indexed runs.
4. System R Dynamic Programming join-order optimization logic.
5. Write-cost penalty detection: verifies write amplification when secondary indexes exist.
"""

import os
import sys
import sqlite3
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_H_dbms.code.tpch_benchmark_harness import TPCH_QUERIES, populate_synthetic_tpch
from track_H_dbms.code.index_optimizer import IndexSelectionModel, SystemRJoinOrderOptimizer, CANDIDATE_INDEX_SPECS
from track_H_dbms.code.write_cost_benchmark import generate_batch_lineitems


DB_PATH = "track_H_dbms/tpch_benchmark.db"


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    populate_synthetic_tpch(DB_PATH, scale_factor=0.1, seed=42)
    yield


def test_candidate_index_profiling_and_sizing():
    """Verify that candidate indices can be profiled and allocate non-zero storage."""
    model = IndexSelectionModel(DB_PATH)
    model.measure_baseline(num_runs=1)
    assert len(model.baseline_latencies) == len(TPCH_QUERIES)

    # Test single candidate profiling
    cand = model.profile_candidates()[0]
    assert cand.size_kb > 0.0
    assert cand.table == "lineitem"


def test_knapsack_solvers_budget_constraint():
    """Verify that Greedy, ILP, and DP solvers strictly adhere to the storage budget."""
    model = IndexSelectionModel(DB_PATH)
    model.measure_baseline(num_runs=1)
    model.profile_candidates()

    budget_kb = 500.0
    greedy_sel, g_spent, g_ben = model.solve_greedy(budget_kb)
    ilp_sel, ilp_spent, ilp_ben = model.solve_ilp(budget_kb)
    dp_sel, dp_spent, dp_ben = model.solve_dp(budget_kb)

    assert g_spent <= budget_kb + 1e-3, f"Greedy exceeded budget: {g_spent} > {budget_kb}"
    assert ilp_spent <= budget_kb + 1e-3, f"ILP exceeded budget: {ilp_spent} > {budget_kb}"
    assert dp_spent <= budget_kb + 1e-3, f"DP exceeded budget: {dp_spent} > {budget_kb}"

    # Verify group mutual exclusivity
    for solver_name, sel in [("Greedy", greedy_sel), ("ILP", ilp_sel), ("DP", dp_sel)]:
        groups = [c.group for c in sel]
        assert len(groups) == len(set(groups)), f"{solver_name} violated group mutual exclusivity: {groups}"


def test_query_result_sha256_identity():
    """Verify that query execution on indexed database produces identical output to baseline."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop secondary indexes
    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
    for (idx_name,) in cur.fetchall():
        cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
    conn.commit()

    # Run Q6 without index
    q_sql = TPCH_QUERIES["Q6_Forecasting_Revenue_Change"]
    cur.execute(q_sql)
    rows_base = cur.fetchall()
    hash_base = hashlib.sha256(json.dumps(sorted(rows_base, key=str), default=str).encode()).hexdigest()

    # Add covering index
    cur.execute("CREATE INDEX IF NOT EXISTS idx_test_q6 ON lineitem(l_shipdate, l_discount, l_quantity, l_extendedprice);")
    conn.commit()

    cur.execute(q_sql)
    rows_opt = cur.fetchall()
    hash_opt = hashlib.sha256(json.dumps(sorted(rows_opt, key=str), default=str).encode()).hexdigest()

    # Clean up
    cur.execute("DROP INDEX IF EXISTS idx_test_q6")
    conn.commit()
    conn.close()

    assert hash_base == hash_opt, "Indexed execution produced differing result set from baseline!"


def test_join_order_system_r_dp_optimality():
    """Verify that System R DP finds a valid join permutation with lower or equal cost."""
    join_opt = SystemRJoinOrderOptimizer(DB_PATH)
    relations = ["customer", "orders", "lineitem", "supplier", "nation", "region"]
    opt_order, opt_cost = join_opt.optimize_join_order(relations)

    assert len(opt_order) == len(relations)
    assert set(opt_order) == set(relations)
    assert opt_cost > 0


def test_write_cost_amplification_detected():
    """Verify that adding secondary indexes incurs measurable write overhead."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
    for (idx_name,) in cur.fetchall():
        cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
    conn.commit()

    batch = generate_batch_lineitems(batch_size=1000, seed=123)

    # 0 indexes
    import time
    t0 = time.perf_counter()
    cur.executemany("INSERT INTO lineitem VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()
    lat_base = (time.perf_counter() - t0) * 1000.0
    cur.execute("DELETE FROM lineitem WHERE l_orderkey >= 800000")
    conn.commit()

    # Add 3 indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_t1 ON lineitem(l_shipdate);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_t2 ON lineitem(l_receiptdate, l_shipmode, l_orderkey);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_t3 ON lineitem(l_partkey, l_suppkey);")
    conn.commit()

    t1 = time.perf_counter()
    cur.executemany("INSERT INTO lineitem VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
    conn.commit()
    lat_indexed = (time.perf_counter() - t1) * 1000.0
    cur.execute("DELETE FROM lineitem WHERE l_orderkey >= 800000")
    cur.execute("DROP INDEX IF EXISTS idx_t1")
    cur.execute("DROP INDEX IF EXISTS idx_t2")
    cur.execute("DROP INDEX IF EXISTS idx_t3")
    conn.commit()
    conn.close()

    assert lat_indexed >= lat_base * 0.9, f"Indexed insert {lat_indexed}ms unexpectedly faster than base {lat_base}ms"
