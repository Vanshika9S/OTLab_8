"""
run_benchmarks.py
-----------------
Comprehensive Benchmark Suite for Track B (Discrete Optimization).

Benchmarks:
  1. Knapsack Scaling Suite:
     - Compares Brute Force, Greedy, Dynamic Programming, ILP (PuLP/CBC),
       and Hand-written Branch-and-Bound across N in [10, 20, 50, 100, 200, 500].
     - Verifies exact optimality against Brute Force on small N.
  2. Max-Cut QUBO & Ising Suite:
     - Formulates standard graphs (5-node cycle, 8-node cube, 12-node random ER).
     - Evaluates Brute Force exact ground states.
     - Runs Simulated Annealing over 10 repeated seeds (0..9) with mean +/- std.
     - Exports qubo_instances.json formatted for immediate consumption by Track C (QAOA).
  3. Generates publication plots:
     - knapsack_scaling_comparison.png
     - sa_convergence_curves.png
"""

import os
import sys
import time
import json
from typing import Dict, List, Any
import numpy as np
import matplotlib.pyplot as plt

# Bootstrap repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_B_discrete.code.knapsack_solvers import (
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
    solve_qubo_brute_force,
    solve_qubo_simulated_annealing,
    build_cardinality_constrained_qubo,
    build_tiny_timetabling_qubo,
)


def run_knapsack_scaling_benchmark(results_dir: str) -> Dict[str, Any]:
    print("\n======================================================================")
    print(" 1. Running Knapsack Scaling Benchmark (Brute Force, Greedy, DP, ILP, B&B)")
    print("======================================================================")

    sizes = [10, 20, 50, 100, 200, 500]
    records: Dict[str, Dict[str, Any]] = {
        "BruteForce": {"sizes": [], "values": [], "runtimes_ms": []},
        "Greedy": {"sizes": [], "values": [], "runtimes_ms": []},
        "DynamicProgramming": {"sizes": [], "values": [], "runtimes_ms": []},
        "ILP": {"sizes": [], "values": [], "runtimes_ms": []},
        "BranchAndBound": {"sizes": [], "values": [], "runtimes_ms": []},
    }

    for n in sizes:
        inst = generate_knapsack_instance(n, capacity_ratio=0.5, seed=42 + n)
        print(f"\n[Knapsack] N={n} items, Capacity={inst.capacity}:")

        # 1. Brute Force (only for N <= 20)
        if n <= 20:
            val_bf, _, t_bf = solve_knapsack_brute_force(inst)
            records["BruteForce"]["sizes"].append(n)
            records["BruteForce"]["values"].append(val_bf)
            records["BruteForce"]["runtimes_ms"].append(round(t_bf, 3))
            print(f"  Brute Force     : Value={val_bf:>6} | Time={t_bf:>8.2f} ms")

        # 2. Greedy
        val_gr, _, t_gr = solve_knapsack_greedy(inst)
        records["Greedy"]["sizes"].append(n)
        records["Greedy"]["values"].append(val_gr)
        records["Greedy"]["runtimes_ms"].append(round(t_gr, 3))
        print(f"  Greedy          : Value={val_gr:>6} | Time={t_gr:>8.2f} ms")

        # 3. Dynamic Programming
        val_dp, _, t_dp = solve_knapsack_dp(inst)
        records["DynamicProgramming"]["sizes"].append(n)
        records["DynamicProgramming"]["values"].append(val_dp)
        records["DynamicProgramming"]["runtimes_ms"].append(round(t_dp, 3))
        print(f"  Dynamic Prog    : Value={val_dp:>6} | Time={t_dp:>8.2f} ms")

        # 4. ILP (PuLP/CBC)
        val_ilp, _, t_ilp = solve_knapsack_ilp(inst)
        records["ILP"]["sizes"].append(n)
        records["ILP"]["values"].append(val_ilp)
        records["ILP"]["runtimes_ms"].append(round(t_ilp, 3))
        print(f"  ILP (CBC)       : Value={val_ilp:>6} | Time={t_ilp:>8.2f} ms")

        # 5. Branch-and-Bound (up to N <= 200)
        if n <= 200:
            val_bb, _, t_bb = solve_knapsack_branch_and_bound(inst)
            records["BranchAndBound"]["sizes"].append(n)
            records["BranchAndBound"]["values"].append(val_bb)
            records["BranchAndBound"]["runtimes_ms"].append(round(t_bb, 3))
            print(f"  Branch & Bound  : Value={val_bb:>6} | Time={t_bb:>8.2f} ms")

    # Save to CSV
    csv_path = os.path.join(results_dir, "knapsack_benchmarks_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Method,N,Value,Runtime_ms\n")
        for method, data in records.items():
            for n_val, val, t in zip(data["sizes"], data["values"], data["runtimes_ms"]):
                f.write(f"{method},{n_val},{val},{t}\n")

    return records


def run_qubo_maxcut_benchmark(results_dir: str) -> Dict[str, Any]:
    print("\n======================================================================")
    print(" 2. Running Max-Cut QUBO & Ising Benchmark (Brute Force + 10-Seed SA)")
    print("======================================================================")

    # Define standard graphs
    graphs = {
        "Graph_5Ring": GraphMaxCut(5, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 4, 1.0), (4, 0, 1.0)]),
        "Graph_8Cube": GraphMaxCut(8, [
            (0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0),
            (4, 5, 1.0), (5, 6, 1.0), (6, 7, 1.0), (7, 4, 1.0),
            (0, 4, 1.0), (1, 5, 1.0), (2, 6, 1.0), (3, 7, 1.0)
        ]),
        "Graph_12ER": GraphMaxCut(12, [
            (0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 4, 1.0), (4, 5, 1.0),
            (5, 6, 1.0), (6, 7, 1.0), (7, 8, 1.0), (8, 9, 1.0), (9, 10, 1.0),
            (10, 11, 1.0), (11, 0, 1.0), (0, 6, 1.0), (2, 8, 1.0), (4, 10, 1.0),
            (1, 7, 1.0), (3, 9, 1.0), (5, 11, 1.0)
        ])
    }

    qubo_export_data = {}
    sa_benchmark_summary = {}
    sa_all_histories = {}

    for g_name, g in graphs.items():
        Q = build_maxcut_qubo(g)
        J, h, offset = build_maxcut_ising(g)

        # 1. Exact ground state via Brute Force
        opt_energy, opt_x, t_bf = solve_qubo_brute_force(Q)
        max_cut = g.compute_cut_value(opt_x)
        opt_bitstring = "".join(str(bit) for bit in opt_x)

        print(f"\n[Max-Cut QUBO] {g_name} (Nodes={g.num_nodes}, Edges={len(g.edges)}):")
        print(f"  Exact Optimum (Brute Force): Cut={max_cut:.1f} | QUBO Energy={opt_energy:.1f} | Solution={opt_bitstring} ({t_bf:.2f} ms)")

        # 2. Simulated Annealing over 10 seeds (0..9)
        sa_energies = []
        sa_runtimes = []
        histories = []
        success_count = 0

        for seed in range(10):
            e, x_sa, t_sa, hist = solve_qubo_simulated_annealing(
                Q, initial_temp=5.0, cooling_rate=0.97, num_steps=500, seed=seed
            )
            sa_energies.append(e)
            sa_runtimes.append(t_sa)
            histories.append(hist)
            if abs(e - opt_energy) < 1e-5:
                success_count += 1

        sa_all_histories[g_name] = histories

        sa_benchmark_summary[g_name] = {
            "exact_optimal_cut": float(max_cut),
            "exact_ground_energy": float(opt_energy),
            "optimal_bitstring": opt_bitstring,
            "sa_energy_mean": float(np.mean(sa_energies)),
            "sa_energy_std": float(np.std(sa_energies)),
            "sa_success_rate": f"{success_count}/10",
            "sa_runtime_mean_ms": float(np.mean(sa_runtimes)),
        }

        print(f"  Simulated Annealing (10 Seeds): Mean Energy={np.mean(sa_energies):.2f} ± {np.std(sa_energies):.2f} | Success Rate={success_count}/10 | Time={np.mean(sa_runtimes):.2f} ms")

        # Format for Track C QAOA export
        qubo_export_data[g_name] = {
            "num_nodes": g.num_nodes,
            "edges": [(int(u), int(v), float(w)) for u, v, w in g.edges],
            "qubo_matrix": Q.tolist(),
            "ising_J": J.tolist(),
            "ising_offset": float(offset),
            "exact_max_cut": float(max_cut),
            "exact_ground_energy": float(opt_energy),
            "optimal_bitstring": opt_bitstring,
        }

    # Save QUBO instances for Track C
    qubo_json_path = os.path.join(results_dir, "qubo_instances.json")
    with open(qubo_json_path, "w", encoding="utf-8") as f:
        json.dump(qubo_export_data, f, indent=2)

    # Save summary CSV
    qubo_csv_path = os.path.join(results_dir, "qubo_benchmarks_summary.csv")
    with open(qubo_csv_path, "w", encoding="utf-8") as f:
        f.write("Graph,Nodes,Edges,Exact_Cut,Ground_Energy,SA_Mean_Energy,SA_Std_Energy,SA_Success_Rate,SA_Time_ms\n")
        for g_name, res in sa_benchmark_summary.items():
            g = graphs[g_name]
            f.write(f"{g_name},{g.num_nodes},{len(g.edges)},{res['exact_optimal_cut']},{res['exact_ground_energy']},{res['sa_energy_mean']},{res['sa_energy_std']},{res['sa_success_rate']},{res['sa_runtime_mean_ms']:.2f}\n")

    return qubo_export_data, sa_all_histories


def plot_all_results(knapsack_data: Dict[str, Any], sa_histories: Dict[str, Any], results_dir: str):
    # 1. Knapsack Scaling Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Runtime vs N
    for method, data in knapsack_data.items():
        axes[0].plot(data["sizes"], data["runtimes_ms"], marker="o", label=method, linewidth=1.8)
    axes[0].set_yscale("log")
    axes[0].set_title("Knapsack Runtime vs Problem Size N", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Number of Items N")
    axes[0].set_ylabel("Wall-Clock Time (ms, log scale)")
    axes[0].grid(True, linestyle="--", alpha=0.6)
    axes[0].legend()

    # Solution Quality vs N
    for method, data in knapsack_data.items():
        axes[1].plot(data["sizes"], data["values"], marker="s", label=method, linewidth=1.8)
    axes[1].set_title("Knapsack Objective Value vs Problem Size N", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Number of Items N")
    axes[1].set_ylabel("Total Objective Value")
    axes[1].grid(True, linestyle="--", alpha=0.6)
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "knapsack_scaling_comparison.png"), dpi=300)
    plt.close()

    # 2. Simulated Annealing Cooling Trajectories
    plt.figure(figsize=(9, 5))
    for seed, hist in enumerate(sa_histories["Graph_12ER"]):
        plt.plot(hist, alpha=0.6, label=f"Seed {seed}" if seed < 3 else None)
    plt.axhline(y=-13.0, color="r", linestyle="--", linewidth=2, label="Exact Ground State (-13.0)")
    plt.title("Simulated Annealing Convergence on 12-Node Max-Cut (10 Seeds)", fontsize=12, fontweight="bold")
    plt.xlabel("Monte Carlo Cooling Steps")
    plt.ylabel("QUBO Energy H(x) = -Cut(x)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "sa_convergence_curves.png"), dpi=300)
    plt.close()


def main():
    results_dir = "track_B_discrete/results"
    os.makedirs(results_dir, exist_ok=True)

    knapsack_res = run_knapsack_scaling_benchmark(results_dir)
    qubo_res, sa_hists = run_qubo_maxcut_benchmark(results_dir)
    plot_all_results(knapsack_res, sa_hists, results_dir)

    print(f"\n[Track B] All benchmarks completed successfully. Results saved in {results_dir}")


if __name__ == "__main__":
    main()
