"""
run_track_j_benchmarks.py
-------------------------
End-to-end benchmark execution script for Track J: Software-Engineering Optimization.

Executes:
1. Baseline test-suite profiling & bottleneck identification.
2. Formulation & benchmarking of Test-Suite Minimization (Naive vs Greedy vs Exact ILP).
3. Budget-constrained prioritization sweep (10% to 100% CI/CD runtime limits).
4. Mutation testing & fault-detection preservation audit (10 injected mutants).
5. Generates publication-grade 4-panel dashboard: track_j_optimization_performance.png.

Track J: Software-Engineering Optimization
Course: Optimization Techniques
"""

import os
import sys
import time
import cProfile
import pstats
import io
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure repo root is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_J_software_eng.code.test_suite_model import RegressionTestSuiteModel
from track_J_software_eng.code.test_suite_optimizer import TestSuiteOptimizer

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def profile_suite_bottlenecks(optimizer: TestSuiteOptimizer) -> Dict[str, Any]:
    """Profiles the test suite execution using cProfile to locate bottlenecks."""
    print("[1/4] Profiling Test-Suite Execution & Identifying Bottlenecks...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run naive evaluation
    _ = optimizer.solve_naive_full_suite()
    
    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(15)
    
    # Bottleneck analysis: evaluate statement overlap
    A = optimizer.A  # statements x tests
    coverage_counts = np.sum(A, axis=1)  # how many tests cover each statement
    avg_overlap = float(np.mean(coverage_counts))
    max_overlap = int(np.max(coverage_counts))
    redundant_statements = int(np.sum(coverage_counts > 1))
    redundancy_pct = (redundant_statements / optimizer.num_statements) * 100.0
    
    print(f"  -> Total Unique Statements: {optimizer.num_statements}")
    print(f"  -> Statements Covered by Multiple Tests: {redundant_statements} ({redundancy_pct:.1f}%)")
    print(f"  -> Average Coverage Overlap per Statement: {avg_overlap:.2f} tests (Max: {max_overlap})")
    
    return {
        "avg_overlap": avg_overlap,
        "max_overlap": max_overlap,
        "redundant_statements": redundant_statements,
        "redundancy_pct": redundancy_pct,
        "cprofile_output": s.getvalue()
    }


def benchmark_minimization_methods(optimizer: TestSuiteOptimizer) -> pd.DataFrame:
    """Benchmarks Naive vs Greedy vs Exact ILP set cover solvers."""
    print("[2/4] Benchmarking Test-Suite Minimization (Naive vs Greedy vs Exact ILP)...")
    naive = optimizer.solve_naive_full_suite()
    greedy = optimizer.solve_greedy_set_cover()
    ilp = optimizer.solve_ilp_exact_set_cover()
    
    records = [naive, greedy, ilp]
    df = pd.DataFrame(records)
    
    # Reorder columns for presentation
    cols = [
        "method", "num_selected", "suite_runtime_ms", "runtime_saved_pct",
        "statements_covered", "coverage_pct", "mutants_killed", "mutation_score_pct",
        "solver_overhead_ms"
    ]
    df_out = df[cols]
    csv_path = os.path.join(RESULTS_DIR, "test_suite_optimization_summary.csv")
    df_out.to_csv(csv_path, index=False)
    print(f"  -> Exported minimization summary to {csv_path}")
    return df_out


def benchmark_budget_prioritization(optimizer: TestSuiteOptimizer) -> pd.DataFrame:
    """Sweeps runtime budgets from 10% to 100% to evaluate prioritization curve."""
    print("[3/4] Sweeping Budget-Constrained Prioritization (10% to 100% time limits)...")
    budgets = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    records = []
    
    for b in budgets:
        res = optimizer.solve_budget_constrained_prioritization(budget_ratio=b)
        records.append({
            "budget_ratio": b,
            "budget_limit_ms": res["budget_limit_ms"],
            "actual_runtime_ms": res["suite_runtime_ms"],
            "num_selected": res["num_selected"],
            "statements_covered": res["statements_covered"],
            "coverage_pct": res["coverage_pct"],
            "mutants_killed": res["mutants_killed"],
            "mutation_score_pct": res["mutation_score_pct"],
            "solver_overhead_ms": res["solver_overhead_ms"],
        })
        
    df = pd.DataFrame(records)
    csv_path = os.path.join(RESULTS_DIR, "budget_prioritization_curve.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported budget prioritization curve to {csv_path}")
    return df


def audit_mutation_testing(model: RegressionTestSuiteModel, optimizer: TestSuiteOptimizer) -> pd.DataFrame:
    """Audits each individual injected mutant against selected suites."""
    print("[4/4] Auditing Mutation Testing & Fault Detection Capability...")
    naive_tests = optimizer.solve_naive_full_suite()["selected_tests"]
    greedy_tests = optimizer.solve_greedy_set_cover()["selected_tests"]
    ilp_tests = optimizer.solve_ilp_exact_set_cover()["selected_tests"]
    
    records = []
    for m in model.mutants_catalog:
        m_id = m["id"]
        m_desc = m["description"]
        targets = m["target_lines"]
        
        # Check if killed by naive, greedy, ilp
        killed_naive = any(t["id"] in naive_tests for t in model.tests_catalog if not targets.isdisjoint(t["statements"]))
        killed_greedy = any(t["id"] in greedy_tests for t in model.tests_catalog if not targets.isdisjoint(t["statements"]))
        killed_ilp = any(t["id"] in ilp_tests for t in model.tests_catalog if not targets.isdisjoint(t["statements"]))
        
        records.append({
            "mutant_id": m_id,
            "description": m_desc,
            "target_statements": str(sorted(list(targets))),
            "killed_by_full_suite": killed_naive,
            "killed_by_greedy_suite": killed_greedy,
            "killed_by_ilp_suite": killed_ilp,
        })
        
    df = pd.DataFrame(records)
    csv_path = os.path.join(RESULTS_DIR, "mutation_testing_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported mutation testing audit to {csv_path}")
    return df


def generate_publication_dashboard(
    df_opt: pd.DataFrame,
    df_budget: pd.DataFrame
):
    """Generates a 4-panel publication-grade dashboard figure."""
    print("Generating 4-panel visualization dashboard...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
    
    methods = ["Naive Full", "Greedy Set Cover", "Exact ILP (HiGHS)"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    
    # -------------------------------------------------------------
    # Panel 1: Execution Runtime & Time Saved
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    runtimes = df_opt["suite_runtime_ms"].values
    saved_pct = df_opt["runtime_saved_pct"].values
    
    x = np.arange(len(methods))
    width = 0.45
    bars = ax1.bar(x, runtimes, width, color=colors, alpha=0.85, edgecolor='black')
    ax1.set_ylabel("Suite Execution Runtime (ms)", fontsize=11, fontweight='bold')
    ax1.set_title("Panel 1: Test-Suite Execution Time & Savings\n(Target Codebase >1,000 LOC)", fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(methods, fontsize=10, fontweight='bold')
    
    for i, bar in enumerate(bars):
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, h + 3, f"{h:.1f} ms\n(-{saved_pct[i]:.1f}%)",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax1.set_ylim(0, max(runtimes) * 1.25)
    
    # -------------------------------------------------------------
    # Panel 2: Tests Selected vs Code Coverage Preserved
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    num_tests = df_opt["num_selected"].values
    cov_pct = df_opt["coverage_pct"].values
    
    b1 = ax2.bar(x - 0.18, num_tests, 0.35, color='#9467bd', alpha=0.85, label='Selected Tests Count')
    ax2.set_ylabel("Number of Tests Selected", fontsize=11, fontweight='bold', color='#9467bd')
    ax2.set_xticks(x)
    ax2.set_xticklabels(methods, fontsize=10, fontweight='bold')
    ax2.set_ylim(0, 30)
    
    ax2_twin = ax2.twinx()
    p1 = ax2_twin.plot(x, cov_pct, '-s', color='#2ca02c', lw=2.5, markersize=8, label='Statement Coverage (%)')
    ax2_twin.set_ylabel("Statement Coverage (%)", fontsize=11, fontweight='bold', color='#2ca02c')
    ax2_twin.set_ylim(80, 105)
    ax2.set_title("Panel 2: Test-Suite Reduction vs 100% Coverage Preservation", fontsize=13, fontweight='bold')
    
    # -------------------------------------------------------------
    # Panel 3: Budget Prioritization Curve
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    budgets_pct = df_budget["budget_ratio"].values * 100.0
    budget_cov = df_budget["coverage_pct"].values
    
    ax3.plot(budgets_pct, budget_cov, '-o', color='#d62728', lw=2.5, markersize=7, label='Code Coverage (%)')
    ax3.axhline(100.0, color='gray', linestyle='--', label='100% Full Coverage')
    ax3.axvline(65.6, color='#2ca02c', linestyle=':', label='ILP Minimal Bound (65.6% Time)')
    ax3.set_xlabel("CI/CD Execution Time Budget (%)", fontsize=11, fontweight='bold')
    ax3.set_ylabel("Code Statement Coverage (%)", fontsize=11, fontweight='bold', color='#d62728')
    ax3.set_title("Panel 3: Budget-Constrained Prioritization Curve\n(Maximum Coverage under Time Limits)", fontsize=13, fontweight='bold')
    ax3.set_ylim(40, 105)
    ax3.legend(loc='lower right', frameon=True)
    
    # -------------------------------------------------------------
    # Panel 4: Mutation Score vs Suite Runtime
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    mut_scores = df_opt["mutation_score_pct"].values
    
    for i, m_name in enumerate(methods):
        ax4.scatter(runtimes[i], mut_scores[i], color=colors[i], s=180, zorder=5, label=f"{m_name}")
        ax4.annotate(
            f"{m_name}\n({runtimes[i]:.1f} ms, {mut_scores[i]:.0f}%)",
            (runtimes[i], mut_scores[i]),
            textcoords="offset points", xytext=(0, -25 if i != 1 else 15), ha='center',
            fontsize=9, fontweight='bold'
        )
        
    ax4.set_xlabel("Suite Execution Runtime (ms)", fontsize=11, fontweight='bold')
    ax4.set_ylabel("Mutation Score (% Faults Killed)", fontsize=11, fontweight='bold')
    ax4.set_title("Panel 4: Fault Detection Preservation vs Execution Cost", fontsize=13, fontweight='bold')
    ax4.set_ylim(80, 115)
    ax4.set_xlim(80, 180)
    ax4.legend(loc='lower left', frameon=True)
    
    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "track_j_optimization_performance.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"  -> Saved 4-panel dashboard to {plot_path}")


def main():
    print("=" * 75)
    print("TRACK J: SOFTWARE-ENGINEERING OPTIMIZATION BENCHMARK SUITE")
    print("=" * 75)
    
    model = RegressionTestSuiteModel(seed=42)
    optimizer = TestSuiteOptimizer(model)
    
    prof_info = profile_suite_bottlenecks(optimizer)
    df_opt = benchmark_minimization_methods(optimizer)
    df_budget = benchmark_budget_prioritization(optimizer)
    df_mut = audit_mutation_testing(model, optimizer)
    
    generate_publication_dashboard(df_opt, df_budget)
    
    print("=" * 75)
    print("TRACK J BENCHMARKS COMPLETED SUCCESSFULLY.")
    print("=" * 75)


if __name__ == "__main__":
    main()
