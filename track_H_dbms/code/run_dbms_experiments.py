"""
run_dbms_experiments.py
-----------------------
Master execution script for Track H (DBMS Optimization).

Executes:
1. Default Optimizer Baseline (0 secondary indexes) with Cold/Warm caching.
2. Candidate Index Profiling (measuring size in KB and per-query benefits).
3. Index Selection via:
   - Greedy by Benefit/Size Ratio (Dantzig heuristic)
   - Exact 0-1 Knapsack / ILP (scipy.optimize.milp)
   - Dynamic Programming
   Across multiple storage budgets (B = 600 KB, B = 1200 KB).
4. Full EXPLAIN QUERY PLAN inspection and SHA-256 result hash validation (100% correctness).
5. Join-Order Dynamic Programming Optimization (System R).
6. Write-Cost Benchmark (insert latency & write amplification factor across 10 trials).
7. Exports publication-grade CSVs, JSON, and speedup plots to track_H_dbms/results/.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_H_dbms.code.tpch_benchmark_harness import TPCH_QUERIES, populate_synthetic_tpch
from track_H_dbms.code.index_optimizer import IndexSelectionModel, SystemRJoinOrderOptimizer
from track_H_dbms.code.write_cost_benchmark import run_write_cost_evaluation


def run_full_dbms_suite(
    db_path: str = "track_H_dbms/tpch_benchmark.db",
    results_dir: str = "track_H_dbms/results",
    seed: int = 42
):
    os.makedirs(results_dir, exist_ok=True)
    print("=" * 80)
    print("TRACK H: DBMS OPTIMIZATION EXPERIMENTAL SUITE (TPC-H SF 0.1)")
    print("=" * 80)

    # 1. Ensure database is populated with Scale Factor 0.1
    populate_synthetic_tpch(db_path, scale_factor=0.1, seed=seed)

    # 2. Profile Candidate Indices and Baseline
    model = IndexSelectionModel(db_path)
    model.measure_baseline(num_runs=5)
    candidates = model.profile_candidates()

    # Export candidate index specifications and profiling metrics
    cand_csv_path = os.path.join(results_dir, "dbms_candidate_indices.csv")
    with open(cand_csv_path, "w", encoding="utf-8") as f:
        f.write("Index_ID,Table,Columns,Size_KB,Total_Benefit_ms,Benefit_Size_Ratio,Targeted_Queries\n")
        for c in candidates:
            cols_str = ";".join(c.columns)
            queries_str = ";".join(c.targeted_queries)
            f.write(f"{c.idx_id},{c.table},{cols_str},{c.size_kb},{c.total_benefit_ms},{c.benefit_to_size_ratio},{queries_str}\n")
    print(f"[Results] Candidate indices exported to {cand_csv_path}")

    # 3. Formulate and Solve Index Selection under Storage Budgets
    budgets = [600.0, 1200.0]
    selection_experiments = []

    # Configurations to evaluate:
    # - Default (No indices)
    # - Greedy (B = 600 KB, B = 1200 KB)
    # - ILP (B = 600 KB, B = 1200 KB)
    # - DP (B = 600 KB, B = 1200 KB)

    configurations = [
        {"name": "Default_No_Secondary_Indexes", "method": "default", "budget_kb": 0.0, "selected": []}
    ]

    for b in budgets:
        greedy_cands, g_spent, g_ben = model.solve_greedy(b)
        ilp_cands, ilp_spent, ilp_ben = model.solve_ilp(b)
        dp_cands, dp_spent, dp_ben = model.solve_dp(b)

        configurations.append({
            "name": f"Greedy_Budget_{int(b)}KB",
            "method": "greedy",
            "budget_kb": b,
            "selected": greedy_cands,
            "spent_kb": g_spent,
            "predicted_benefit_ms": g_ben
        })
        configurations.append({
            "name": f"ILP_Exact_Budget_{int(b)}KB",
            "method": "ilp",
            "budget_kb": b,
            "selected": ilp_cands,
            "spent_kb": ilp_spent,
            "predicted_benefit_ms": ilp_ben
        })
        configurations.append({
            "name": f"DP_Knapsack_Budget_{int(b)}KB",
            "method": "dp",
            "budget_kb": b,
            "selected": dp_cands,
            "spent_kb": dp_spent,
            "predicted_benefit_ms": dp_ben
        })

    # 4. Benchmark Workload for each configuration
    print("\n[DBMS Benchmark] Evaluating Workload Configurations...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    config_results = []
    per_query_latencies = {}

    for cfg in configurations:
        cfg_name = cfg["name"]
        selected_cands = cfg["selected"]

        # Drop old indices
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
        for (idx_name,) in cur.fetchall():
            cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
        conn.commit()

        # Build selected indices
        for c in selected_cands:
            cur.execute(c.sql)
        conn.commit()

        # Measure storage
        cur.execute("PRAGMA page_size")
        page_size = cur.fetchone()[0]
        cur.execute("PRAGMA page_count")
        total_pages = cur.fetchone()[0]
        db_size_kb = (total_pages * page_size) / 1024.0

        # Benchmark queries
        total_cold_ms = 0.0
        total_warm_ms = 0.0
        all_results_match = True
        query_lat_map = {}
        plan_map = {}

        for q_name, q_sql in TPCH_QUERIES.items():
            # Plan
            cur.execute(f"EXPLAIN QUERY PLAN {q_sql}")
            plan_map[q_name] = [row[3] for row in cur.fetchall()]

            # Cold run
            cold_conn = sqlite3.connect(db_path)
            cold_cur = cold_conn.cursor()
            t0 = time.perf_counter()
            cold_cur.execute(q_sql)
            cold_rows = cold_cur.fetchall()
            cold_ms = (time.perf_counter() - t0) * 1000.0
            total_cold_ms += cold_ms
            cold_conn.close()

            # Warm runs
            warm_runs = []
            for _ in range(5):
                t0 = time.perf_counter()
                cur.execute(q_sql)
                rows = cur.fetchall()
                warm_runs.append((time.perf_counter() - t0) * 1000.0)

            mean_warm_ms = float(np.mean(warm_runs))
            total_warm_ms += mean_warm_ms
            query_lat_map[q_name] = round(mean_warm_ms, 3)

            # Check result correctness
            canonical_repr = json.dumps(sorted(rows, key=lambda x: str(x)), default=str)
            h = hashlib.sha256(canonical_repr.encode()).hexdigest()
            if h != model.baseline_hashes[q_name]:
                all_results_match = False
                print(f"  [ERROR] Output mismatch on {q_name} in {cfg_name}!")

        per_query_latencies[cfg_name] = query_lat_map
        qps = (len(TPCH_QUERIES) / (total_warm_ms / 1000.0))

        baseline_warm_ms = sum(model.baseline_latencies.values())
        speedup = baseline_warm_ms / total_warm_ms if total_warm_ms > 0 else 1.0

        res_entry = {
            "Configuration": cfg_name,
            "Method": cfg["method"],
            "Budget_KB": cfg["budget_kb"],
            "Indices_Count": len(selected_cands),
            "Indices_List": ";".join([c.idx_id for c in selected_cands]),
            "Storage_KB": round(db_size_kb, 1),
            "Total_Cold_Latency_ms": round(total_cold_ms, 2),
            "Total_Warm_Latency_ms": round(total_warm_ms, 2),
            "Workload_Speedup_Factor": round(speedup, 2),
            "Throughput_QPS": round(qps, 1),
            "Results_Verified_Identical": all_results_match
        }
        config_results.append(res_entry)
        print(f"  {cfg_name}: Latency={total_warm_ms:.2f}ms | Speedup={speedup:.2f}x | QPS={qps:.1f} | Storage={db_size_kb:.0f}KB | Verified={all_results_match}")

    conn.close()

    # Save summary CSV
    summary_csv_path = os.path.join(results_dir, "dbms_index_selection_summary.csv")
    with open(summary_csv_path, "w", encoding="utf-8") as f:
        headers = list(config_results[0].keys())
        f.write(",".join(headers) + "\n")
        for row in config_results:
            f.write(",".join(str(row[h]) for h in headers) + "\n")
    print(f"[Results] Index selection summary exported to {summary_csv_path}")

    # Save per-query latency CSV
    per_query_csv_path = os.path.join(results_dir, "dbms_query_latency_comparison.csv")
    with open(per_query_csv_path, "w", encoding="utf-8") as f:
        q_cols = list(TPCH_QUERIES.keys())
        f.write("Configuration," + ",".join(q_cols) + "\n")
        for cfg_name, lat_dict in per_query_latencies.items():
            vals = [str(lat_dict.get(q, 0.0)) for q in q_cols]
            f.write(cfg_name + "," + ",".join(vals) + "\n")
    print(f"[Results] Per-query latencies exported to {per_query_csv_path}")

    # 5. Dynamic Programming Join-Order Optimization (System R)
    print("\n[DBMS Join-Order] Running System R Dynamic Programming Join-Order Optimizer...")
    join_opt = SystemRJoinOrderOptimizer(db_path)
    join_workloads = {
        "Q3_Join_3_Tables": ["customer", "orders", "lineitem"],
        "Q5_Join_6_Tables": ["customer", "orders", "lineitem", "supplier", "nation", "region"],
        "Q9_Join_6_Tables": ["part", "supplier", "lineitem", "partsupp", "orders", "nation"]
    }
    join_results = []
    for jw_name, rels in join_workloads.items():
        opt_order, opt_cost = join_opt.optimize_join_order(rels)
        # Default syntactic order is as written in SQL query
        # Evaluate syntactic cost
        _, syn_cost = join_opt.estimate_join_cost(1000, 1000) # baseline reference
        join_results.append({
            "Query": jw_name,
            "Tables_Count": len(rels),
            "Default_Syntactic_Order": " -> ".join(rels),
            "DP_Optimal_Left_Deep_Order": " -> ".join(opt_order),
            "Estimated_DP_Cost": opt_cost
        })
        print(f"  {jw_name} ({len(rels)} tables):")
        print(f"    Syntactic Order : {' -> '.join(rels)}")
        print(f"    DP Optimal Order: {' -> '.join(opt_order)} (Cost: {opt_cost})")

    join_csv_path = os.path.join(results_dir, "dbms_join_order_comparison.csv")
    with open(join_csv_path, "w", encoding="utf-8") as f:
        headers = list(join_results[0].keys())
        f.write(",".join(headers) + "\n")
        for row in join_results:
            f.write(",".join(str(row[h]) for h in headers) + "\n")
    print(f"[Results] Join order comparison exported to {join_csv_path}")

    # 6. Write Cost Benchmark Evaluation
    write_results = run_write_cost_evaluation(db_path=db_path, batch_size=3000, num_trials=10, seed=seed)
    write_csv_path = os.path.join(results_dir, "dbms_write_cost_benchmark.csv")
    with open(write_csv_path, "w", encoding="utf-8") as f:
        headers = list(write_results[0].keys())
        f.write(",".join(headers) + "\n")
        for row in write_results:
            f.write(",".join(str(row[h]) for h in headers) + "\n")
    print(f"[Results] Write cost benchmark exported to {write_csv_path}")

    # 7. Generate Visualization Plot
    plot_path = os.path.join(results_dir, "dbms_optimization_speedup.png")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Read Latency & Speedup
    names = [r["Configuration"].replace("Default_No_Secondary_Indexes", "Default").replace("Exact_", "").replace("_Budget_", " ") for r in config_results]
    latencies = [r["Total_Warm_Latency_ms"] for r in config_results]
    speedups = [r["Workload_Speedup_Factor"] for r in config_results]

    ax1 = axes[0]
    bars = ax1.bar(names, latencies, color=["#7f7f7f", "#1f77b4", "#2ca02c", "#9467bd", "#1f77b4", "#2ca02c", "#9467bd"], alpha=0.85, edgecolor='black')
    ax1.set_ylabel("Workload Execution Latency (ms)", fontsize=11, fontweight='bold')
    ax1.set_title("Read Workload Latency vs Index Configuration", fontsize=12, fontweight='bold')
    ax1.set_xticklabels(names, rotation=35, ha='right', fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.4, axis='y')

    for bar, sp in zip(bars, speedups):
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0, f"{sp}x", ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Subplot 2: Write Cost & Amplification Factor
    ax2 = axes[1]
    cfg_labels = [f"{w['num_secondary_indexes']} Indexes" for w in write_results]
    write_lats = [w["insert_latency_mean_ms"] for w in write_results]
    write_amps = [w["write_amplification_factor"] for w in write_results]

    bars2 = ax2.bar(cfg_labels, write_lats, color="#d62728", alpha=0.85, edgecolor='black')
    ax2.set_ylabel("Batch Insert Latency (ms for 3,000 rows)", fontsize=11, fontweight='bold')
    ax2.set_title("Write Cost Penalty: Insert Latency Amplification", fontsize=12, fontweight='bold')
    ax2.set_xticklabels(cfg_labels, rotation=20, ha='right', fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.4, axis='y')

    for bar, amp in zip(bars2, write_amps):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.8, f"{amp}x", ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"[Results] Visualization plot exported to {plot_path}")

    print("\n" + "=" * 80)
    print("TRACK H EXPERIMENTAL SUITE COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_full_dbms_suite()
