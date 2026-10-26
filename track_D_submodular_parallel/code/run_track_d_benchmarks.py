"""
run_track_d_benchmarks.py
-------------------------
Executes the comprehensive benchmark suite for Track D:
  1. Submodular Coverage: Diminishing returns empirical test, guarantee pre-condition checks,
     greedy vs brute force on growing budgets, and non-submodular failure demonstration.
  2. Parallel Multiprocessing: Imbalanced load balancing (static vs work stealing),
     scaling laws (Amdahl strong scaling and Gustafson weak scaling), and honest negative overhead.
  3. Distributed & Multi-Task: FedAvg scaling across local epochs and communication rounds,
     and multi-task optimization under gradient conflict (Equal vs MGDA vs GradNorm).
"""

import sys
import os
import time
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
    HARDWARE_INFO,
    generate_imbalanced_workload,
    run_static_partitioning,
    run_dynamic_work_stealing,
    benchmark_locality_and_sync,
    benchmark_scaling_laws,
    demonstrate_negative_parallel_result,
    PipelineParallelModel
)
from track_D_submodular_parallel.code.distributed_and_multitask import (
    FederatedDataset,
    train_centralized,
    train_fedavg,
    ConflictingMultiTaskProblem,
    optimize_multitask
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ==============================================================================
# 1. SUBMODULAR OPTIMIZATION BENCHMARKS
# ==============================================================================
def run_submodular_benchmarks(seed: int = 42):
    print("\n--- 1. Submodular Optimization Benchmarks ---")
    fl = FacilityLocationCoverage(n_facilities=16, m_clients=40, seed=seed)

    # 1.1 Diminishing returns test
    dr_res = check_diminishing_returns(fl, num_trials=500, seed=seed)
    print(f"Diminishing Returns Verified: {dr_res['is_submodular']} over {dr_res['num_trials']} subset pairs")

    df_dr = pd.DataFrame([{
        "Objective": "FacilityLocationCoverage",
        "Subset_Pairs_Tested": dr_res["num_trials"],
        "Violations": dr_res["violations"],
        "Diminishing_Returns_Holds": dr_res["is_submodular"],
        "Min_Gain_Difference": dr_res["min_difference"],
        "Mean_Gain_Difference": dr_res["mean_difference"]
    }])
    df_dr.to_csv(os.path.join(RESULTS_DIR, "submodular_diminishing_returns.csv"), index=False)

    # 1.2 Preconditions verification
    cert = verify_guarantee_preconditions(fl, budget_k=4)
    print(f"Nemhauser Preconditions: All 4 Met = {cert['all_preconditions_met']} (Bound = 1 - 1/e ~ {cert['theoretical_lower_bound_factor']:.4f})")

    # 1.3 Greedy vs Brute Force across budgets k in [1, 2, 3, 4, 5]
    comp_records = []
    budgets = [1, 2, 3, 4, 5]
    for k in budgets:
        S_g, val_g, _, t_g = greedy_submodular_maximize(fl, budget_k=k)
        S_opt, val_opt, t_opt = brute_force_submodular_maximize(fl, budget_k=k)
        ratio = val_g / val_opt

        comp_records.append({
            "Budget_k": k,
            "Greedy_Selected": str(sorted(list(S_g))),
            "Greedy_Value": round(val_g, 2),
            "Greedy_Time_ms": round(t_g, 2),
            "Optimal_Selected": str(sorted(list(S_opt))),
            "Optimal_Value": round(val_opt, 2),
            "Optimal_Time_ms": round(t_opt, 2),
            "Approximation_Ratio": round(ratio, 4),
            "Nemhauser_Lower_Bound": round(1.0 - 1.0 / np.e, 4)
        })
        print(f"k={k} | Greedy: {val_g:6.2f} ({t_g:5.2f}ms) vs Opt: {val_opt:6.2f} ({t_opt:6.2f}ms) | Ratio: {ratio:.4f}")

    df_comp = pd.DataFrame(comp_records)
    df_comp.to_csv(os.path.join(RESULTS_DIR, "submodular_greedy_vs_bruteforce.csv"), index=False)

    # 1.4 Non-submodular failure demonstration
    fail_res = demonstrate_non_submodular_greedy_failure(n=16, budget_k=2, synergy_bonus=100.0)
    print(f"Non-Submodular Failure: Greedy={fail_res['greedy_value']} vs Opt={fail_res['optimal_value']} | Ratio={fail_res['actual_approx_ratio']:.4f} (Violated={fail_res['guarantee_violated']})")

    df_fail = pd.DataFrame([{
        "Problem": "NonSubmodularSynergy",
        "Synergy_Bonus": fail_res["synergy_bonus"],
        "Greedy_Selected": str(fail_res["greedy_selected"]),
        "Greedy_Value": fail_res["greedy_value"],
        "Optimal_Selected": str(fail_res["optimal_selected"]),
        "Optimal_Value": fail_res["optimal_value"],
        "Approximation_Ratio": round(fail_res["actual_approx_ratio"], 4),
        "Nemhauser_Bound": round(fail_res["nemhauser_bound"], 4),
        "Bound_Violated": fail_res["guarantee_violated"]
    }])
    df_fail.to_csv(os.path.join(RESULTS_DIR, "submodular_non_submodular_failure.csv"), index=False)

    # Plot Submodular Guarantee vs Non-Submodular Failure
    plt.figure(figsize=(9, 5))
    plt.plot(df_comp["Budget_k"], df_comp["Approximation_Ratio"], "o-", color="#1f77b4", lw=2.5, markersize=8, label="Submodular Objective (Greedy / OPT)")
    plt.axhline(1.0 - 1.0 / np.e, color="#2ca02c", linestyle="--", lw=2, label="Theoretical Lower Bound: $(1 - 1/e) \\approx 0.6321$")
    plt.scatter([2], [fail_res["actual_approx_ratio"]], color="#d62728", s=120, zorder=5, label=f"Non-Submodular Synergy (Ratio = {fail_res['actual_approx_ratio']:.3f})")

    plt.xlabel("Selection Budget $k$", fontsize=12)
    plt.ylabel("Approximation Ratio $\\alpha$", fontsize=12)
    plt.title("Track D: Submodular (1 - 1/e) Guarantee vs Non-Submodular Greedy Failure", fontsize=13, fontweight="bold")
    plt.ylim(0.0, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "submodular_guarantee_and_failure.png"), dpi=300)
    plt.close()


# ==============================================================================
# 2. PARALLEL PROGRAM OPTIMIZATION BENCHMARKS
# ==============================================================================
def run_parallel_benchmarks():
    print(f"\n--- 2. Parallel Multiprocessing Benchmarks ({HARDWARE_INFO['model']}) ---")
    print(f"Architecture: {HARDWARE_INFO['physical_cores']} Cores ({HARDWARE_INFO['p_cores']} P-cores + {HARDWARE_INFO['e_cores']} E-cores, {HARDWARE_INFO['logical_processors']} Threads)")

    tasks = generate_imbalanced_workload(n_tasks=48, seed=42)
    core_counts = [1, 2, 4, 6, 8]

    # 2.1 Load Balancing: Static Partitioning vs Work Stealing
    makespan_records = []
    for p in core_counts:
        st_res = run_static_partitioning(tasks, num_workers=p)
        ws_res = run_dynamic_work_stealing(tasks, num_workers=p)
        improvement = (st_res["makespan_ms"] - ws_res["makespan_ms"]) / st_res["makespan_ms"] * 100.0

        makespan_records.append({
            "Cores": p,
            "Static_Makespan_ms": round(st_res["makespan_ms"], 1),
            "Static_Imbalance_Ratio": st_res["imbalance_ratio"],
            "WorkStealing_Makespan_ms": round(ws_res["makespan_ms"], 1),
            "WorkStealing_Imbalance_Ratio": ws_res["imbalance_ratio"],
            "Makespan_Improvement_Percent": round(improvement, 2)
        })
        print(f"p={p:2d} | Static: {st_res['makespan_ms']:6.1f}ms (Imbal: {st_res['imbalance_ratio']}x) vs WorkStealing: {ws_res['makespan_ms']:6.1f}ms (Imbal: {ws_res['imbalance_ratio']}x) | Gain: +{improvement:.1f}%")

    df_ms = pd.DataFrame(makespan_records)
    df_ms.to_csv(os.path.join(RESULTS_DIR, "parallel_makespan_static_vs_stealing.csv"), index=False)

    # Plot Static vs Work Stealing Makespan
    plt.figure(figsize=(8, 5))
    x = np.arange(len(core_counts))
    width = 0.35
    plt.bar(x - width/2, df_ms["Static_Makespan_ms"], width, label="Static Block Partitioning", color="#d62728", alpha=0.85)
    plt.bar(x + width/2, df_ms["WorkStealing_Makespan_ms"], width, label="Dynamic Work Stealing (Task Queue)", color="#1f77b4", alpha=0.85)
    plt.xlabel("Worker Count (Threads)", fontsize=12)
    plt.ylabel("Makespan (ms)", fontsize=12)
    plt.title(f"Track D: Load Balancing & Makespan ({HARDWARE_INFO['model']})", fontsize=13, fontweight="bold")
    plt.xticks(x, core_counts)
    plt.grid(True, axis="y", linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "parallel_makespan_balance.png"), dpi=300)
    plt.close()

    # 2.2 Scaling Laws: Amdahl vs Gustafson
    scaling_data = benchmark_scaling_laws(core_counts=[1, 2, 4, 6, 8], base_task_count=32)
    amdahl_records = scaling_data["amdahl_strong_scaling"]
    df_scale = pd.DataFrame(amdahl_records)
    df_scale["Empirical_Parallel_Fraction_f"] = scaling_data["empirical_parallel_fraction_f"]
    df_scale["Empirical_Sequential_Fraction_s"] = scaling_data["empirical_sequential_fraction_s"]
    df_scale["Amdahl_Theoretical_Max_Speedup"] = scaling_data["theoretical_max_speedup_amdahl"]
    df_scale.to_csv(os.path.join(RESULTS_DIR, "parallel_scaling_amdahl_gustafson.csv"), index=False)

    print(f"Amdahl Strong Scaling Fit: Parallel Fraction f = {scaling_data['empirical_parallel_fraction_f']:.4f}, Sequential Fraction s = {scaling_data['empirical_sequential_fraction_s']:.4f}")
    print(f"Amdahl Asymptotic Max Speedup: S_max = 1/s = {scaling_data['theoretical_max_speedup_amdahl']:.2f}x")

    # Plot Amdahl vs Gustafson Speedup
    plt.figure(figsize=(8, 5))
    plt.plot(df_scale["cores"], df_scale["speedup"], "o-", color="#1f77b4", lw=2.5, label="Measured Strong Speedup (Fixed Problem)")
    
    # Amdahl theoretical curve
    f = scaling_data["empirical_parallel_fraction_f"]
    cores_fine = np.linspace(1, 8, 50)
    amdahl_curve = 1.0 / ((1.0 - f) + f / cores_fine)
    plt.plot(cores_fine, amdahl_curve, "--", color="#2ca02c", lw=2, label=f"Amdahl's Law Fit ($f={f:.2f}, S_{{max}}={1/(1-f):.1f}\\times$)")
    
    # Linear ideal speedup
    plt.plot(cores_fine, cores_fine, ":", color="gray", label="Ideal Linear Speedup $S(p)=p$")

    plt.xlabel("Number of Cores / Workers $p$", fontsize=12)
    plt.ylabel("Speedup $S(p)$", fontsize=12)
    plt.title(f"Track D: Strong Scaling & Amdahl's Law ({HARDWARE_INFO['model']})", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "parallel_scaling_laws.png"), dpi=300)
    plt.close()

    # 2.3 Honest Negative Result: Micro-workload IPC Overhead
    neg_res = demonstrate_negative_parallel_result(num_items=1000)
    print(f"Honest Negative Result: Sequential={neg_res['sequential_time_ms']}ms vs Parallel Dispatch={neg_res['parallel_with_ipc_ms']}ms | Slowdown: {neg_res['slowdown_factor']}x")
    df_neg = pd.DataFrame([neg_res])
    df_neg.to_csv(os.path.join(RESULTS_DIR, "parallel_fine_grained_overhead.csv"), index=False)


# ==============================================================================
# 3. DISTRIBUTED & MULTI-TASK BENCHMARKS
# ==============================================================================
def run_distributed_and_multitask_benchmarks(seed: int = 42):
    print("\n--- 3. Distributed & Multi-Task Benchmarks ---")

    # 3.1 FedAvg vs Centralized Training
    ds = FederatedDataset(n_samples=600, n_features=8, n_clients=5, seed=seed)
    cent_res = train_centralized(ds, total_steps=60, lr=0.05, seed=seed)

    fed_records = []
    # Test combinations of rounds and local epochs
    epoch_configs = [1, 5, 15]
    round_configs = [5, 10, 20]

    for E in epoch_configs:
        for R in round_configs:
            res_fed = train_fedavg(ds, num_rounds=R, local_epochs=E, lr=0.05, seed=seed)
            fed_records.append({
                "Communication_Rounds": R,
                "Local_Epochs_E": E,
                "Total_Local_Steps": R * E,
                "Final_Test_Loss": round(res_fed["final_loss"], 5),
                "Centralized_Baseline_Loss": round(cent_res["final_loss"], 5),
                "Runtime_ms": round(res_fed["runtime_ms"], 2)
            })
            print(f"FedAvg (R={R:2d}, E={E:2d}) | Test Loss: {res_fed['final_loss']:.5f} (Cent: {cent_res['final_loss']:.5f}) | Time: {res_fed['runtime_ms']:.1f}ms")

    df_fed = pd.DataFrame(fed_records)
    df_fed.to_csv(os.path.join(RESULTS_DIR, "distributed_fedavg_scaling.csv"), index=False)

    # Plot FedAvg Convergence Curves
    plt.figure(figsize=(8, 5))
    res_e1 = train_fedavg(ds, num_rounds=20, local_epochs=1, lr=0.05, seed=seed)
    res_e5 = train_fedavg(ds, num_rounds=20, local_epochs=5, lr=0.05, seed=seed)
    res_e15 = train_fedavg(ds, num_rounds=20, local_epochs=15, lr=0.05, seed=seed)

    plt.plot(res_e1["history"], "o-", label="FedAvg ($E=1$ local step)", color="#1f77b4")
    plt.plot(res_e5["history"], "s-", label="FedAvg ($E=5$ local steps)", color="#2ca02c")
    plt.plot(res_e15["history"], "^-", label="FedAvg ($E=15$ local steps)", color="#ff7f0e")
    plt.axhline(cent_res["final_loss"], color="#d62728", linestyle="--", lw=2, label=f"Centralized Benchmark ({cent_res['final_loss']:.4f})")

    plt.xlabel("Communication Round $r$", fontsize=12)
    plt.ylabel("Global Test MSE Loss", fontsize=12)
    plt.title("Track D: Federated Averaging (FedAvg) vs Centralized Optimization", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "distributed_fedavg_convergence.png"), dpi=300)
    plt.close()

    # 3.2 Multi-Task Optimization: Equal Weighting vs MGDA vs GradNorm
    prob = ConflictingMultiTaskProblem(dim=8, seed=seed)
    res_eq = optimize_multitask(prob, method="equal", steps=100, lr=0.02, seed=seed)
    res_mgda = optimize_multitask(prob, method="mgda", steps=100, lr=0.02, seed=seed)
    res_gn = optimize_multitask(prob, method="gradnorm", steps=100, lr=0.02, seed=seed)

    mt_records = [
        {
            "Method": "Equal Weighting (Uniform Scalarization)",
            "Final_Loss_1": round(res_eq["final_l1"], 4),
            "Final_Loss_2": round(res_eq["final_l2"], 4),
            "Sum_Loss": round(res_eq["final_l1"] + res_eq["final_l2"], 4),
            "Gradient_Cosine_Angle": round(res_eq["mean_gradient_cosine"], 4),
            "Runtime_ms": round(res_eq["runtime_ms"], 2)
        },
        {
            "Method": "Multiple Gradient Descent Algorithm (MGDA)",
            "Final_Loss_1": round(res_mgda["final_l1"], 4),
            "Final_Loss_2": round(res_mgda["final_l2"], 4),
            "Sum_Loss": round(res_mgda["final_l1"] + res_mgda["final_l2"], 4),
            "Gradient_Cosine_Angle": round(res_mgda["mean_gradient_cosine"], 4),
            "Runtime_ms": round(res_mgda["runtime_ms"], 2)
        },
        {
            "Method": "GradNorm (Dynamic Loss Balancing)",
            "Final_Loss_1": round(res_gn["final_l1"], 4),
            "Final_Loss_2": round(res_gn["final_l2"], 4),
            "Sum_Loss": round(res_gn["final_l1"] + res_gn["final_l2"], 4),
            "Gradient_Cosine_Angle": round(res_gn["mean_gradient_cosine"], 4),
            "Runtime_ms": round(res_gn["runtime_ms"], 2)
        }
    ]
    df_mt = pd.DataFrame(mt_records)
    df_mt.to_csv(os.path.join(RESULTS_DIR, "multitask_mgda_gradnorm_comparison.csv"), index=False)

    print(f"Equal Weighting: L1 = {res_eq['final_l1']:.4f}, L2 = {res_eq['final_l2']:.4f}")
    print(f"MGDA:            L1 = {res_mgda['final_l1']:.4f}, L2 = {res_mgda['final_l2']:.4f}")
    print(f"GradNorm:        L1 = {res_gn['final_l1']:.4f}, L2 = {res_gn['final_l2']:.4f}")

    # Plot Multi-Task Optimization Pareto Trajectories
    plt.figure(figsize=(8, 5))
    plt.plot(res_eq["history_l1"], res_eq["history_l2"], "o-", markersize=3, label="Equal Weighting (Dominated by Task 2)", color="#d62728")
    plt.plot(res_mgda["history_l1"], res_mgda["history_l2"], "s-", markersize=3, label="MGDA (Pareto Common Descent)", color="#1f77b4")
    plt.plot(res_gn["history_l1"], res_gn["history_l2"], "^-", markersize=3, label="GradNorm (Dynamic Gradient Balancing)", color="#2ca02c")

    plt.xlabel("Task 1 Loss $\\mathcal{L}_1$", fontsize=12)
    plt.ylabel("Task 2 Loss $\\mathcal{L}_2$", fontsize=12)
    plt.title("Track D: Multi-Task Optimization Trajectories under Conflicting Gradients", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "multitask_pareto_front.png"), dpi=300)
    plt.close()


def main():
    print("=" * 80)
    print("DAY 7: TRACK D SUBMODULAR, PARALLEL & DISTRIBUTED BENCHMARK SUITE")
    print("=" * 80)

    run_submodular_benchmarks(seed=42)
    run_parallel_benchmarks()
    run_distributed_and_multitask_benchmarks(seed=42)

    print("\n[SUCCESS] Track D benchmark suite completed successfully!")


if __name__ == "__main__":
    main()
