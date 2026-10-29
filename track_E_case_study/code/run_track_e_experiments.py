"""
run_track_e_experiments.py
--------------------------
Master benchmark and experimental harness for Track E (Timetabling Optimization).

Executes:
1. Multi-Solver Comparison on Primary Instance (300 students, 40 courses, 12 slots)
   across 10 seeds: Random, First-Fit, DSATUR, ILP (HiGHS), Single-Threaded SA, and Parallel SA.
2. Parallel SA Restarts & Variability Analysis across 1, 2, 4, and 6 cores.
3. Scaling Experiment across 100, 300, 1000, and 3000 students.
4. Toronto Carter Benchmark Evaluation (parsed via toronto_parser.py).
5. Sensitivity Analysis (slot capacity and slot count phase transitions).
6. Exports publication-grade CSVs, JSON records, and comparison plots to results/.
"""

import os
import sys
import json
import time
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_E_case_study.code.validator import TimetableValidator
from track_E_case_study.code.baselines import RandomScheduler, FirstFitScheduler
from track_E_case_study.code.optimizers import DSATURSolver, ILPSolver, SimulatedAnnealingSolver, ParallelSASolver
from track_E_case_study.code.toronto_parser import parse_toronto_instance


def run_all_track_e_benchmarks(
    data_dir: str = "track_E_case_study/data",
    results_dir: str = "track_E_case_study/results",
    num_seeds: int = 10,
    base_seed: int = 42
):
    os.makedirs(results_dir, exist_ok=True)
    print("=" * 80)
    print("TRACK E: UNIVERSITY EXAM TIMETABLING OPTIMIZATION BENCHMARK SUITE")
    print("=" * 80)

    # -----------------------------------------------------------------
    # Experiment 1: Multi-Solver Comparison on Primary Instance (300 students)
    # -----------------------------------------------------------------
    primary_path = os.path.join(data_dir, "synthetic_primary_300.json")
    with open(primary_path, "r", encoding="utf-8") as f:
        primary_inst = json.load(f)

    validator = TimetableValidator(primary_inst)
    solvers = {
        "Random": lambda seed: RandomScheduler(primary_inst, seed=seed).solve(),
        "FirstFit": lambda seed: FirstFitScheduler(primary_inst, seed=seed).solve(),
        "DSATUR": lambda seed: DSATURSolver(primary_inst).solve(seed=seed),
        "ILP_HiGHS_2s": lambda seed: ILPSolver(primary_inst).solve(time_limit=2.0, seed=seed),
        "SimulatedAnnealing": lambda seed: SimulatedAnnealingSolver(primary_inst).solve(max_iterations=500, seed=seed)[0:3:2],
        "Parallel_SA_4cores": lambda seed: (lambda res: (res[0], res[3]))(ParallelSASolver(primary_inst).solve(num_restarts=4, max_iterations=500, base_seed=seed))
    }

    print("\n[Experiment 1] Running 10-seed comparison on primary instance (300 students)...")
    exp1_records = []
    summary_rows = []

    for solver_name, solver_fn in solvers.items():
        metrics = {
            "is_feasible": [],
            "student_clashes": [],
            "capacity_violations": [],
            "back_to_back_count": [],
            "three_plus_day_count": [],
            "slots_used": [],
            "total_penalty": [],
            "runtime_ms": []
        }

        for s_idx in range(num_seeds):
            seed = base_seed + s_idx * 17
            sched, rt_ms = solver_fn(seed)
            eval_res = validator.evaluate_schedule(sched)

            metrics["is_feasible"].append(1.0 if eval_res["is_feasible"] else 0.0)
            metrics["student_clashes"].append(eval_res["student_clashes"])
            metrics["capacity_violations"].append(eval_res["capacity_violations"])
            metrics["back_to_back_count"].append(eval_res["back_to_back_count"])
            metrics["three_plus_day_count"].append(eval_res["three_plus_day_count"])
            metrics["slots_used"].append(eval_res["slots_used"])
            metrics["total_penalty"].append(eval_res["total_penalty"])
            metrics["runtime_ms"].append(rt_ms)

        for m_key, vals in metrics.items():
            summary_rows.append({
                "Solver": solver_name,
                "Metric": m_key,
                "Mean": round(float(np.mean(vals)), 4),
                "Std": round(float(np.std(vals)), 4),
                "Min": round(float(np.min(vals)), 4),
                "Max": round(float(np.max(vals)), 4)
            })

        print(f"  {solver_name:18s} | Feas: {np.mean(metrics['is_feasible'])*100:5.1f}% | Clashes: {np.mean(metrics['student_clashes']):5.1f} | Penalty: {np.mean(metrics['total_penalty']):7.1f} | Runtime: {np.mean(metrics['runtime_ms']):7.2f} ms")

    # Save summary CSV
    exp1_csv = os.path.join(results_dir, "timetable_solver_comparison_summary.csv")
    with open(exp1_csv, "w", encoding="utf-8") as f:
        headers = ["Solver", "Metric", "Mean", "Std", "Min", "Max"]
        f.write(",".join(headers) + "\n")
        for r in summary_rows:
            f.write(f"{r['Solver']},{r['Metric']},{r['Mean']},{r['Std']},{r['Min']},{r['Max']}\n")
    print(f"[Results] Exported Experiment 1 summary to {exp1_csv}")

    # -----------------------------------------------------------------
    # Experiment 2: Parallel SA Restarts & Variability Analysis
    # -----------------------------------------------------------------
    print("\n[Experiment 2] Evaluating Parallel SA restarts across core counts P in {1, 2, 4, 6}...")
    par_sa = ParallelSASolver(primary_inst)
    exp2_rows = []
    base_t_seq = None

    for p in [1, 2, 4, 6]:
        best_sched, best_cost, restart_costs, wall_t_ms = par_sa.solve(num_restarts=p, max_iterations=500, base_seed=42)
        if base_t_seq is None:
            base_t_seq = wall_t_ms
        speedup = (base_t_seq * p) / wall_t_ms if wall_t_ms > 0 else 1.0

        eval_res = validator.evaluate_schedule(best_sched)
        exp2_rows.append({
            "Worker_Cores": p,
            "Restarts_Evaluated": p,
            "Wall_Clock_ms": round(wall_t_ms, 2),
            "Parallel_Speedup_Factor": round(speedup, 2),
            "Best_Penalty": round(eval_res["total_penalty"], 2),
            "Best_Clashes": eval_res["student_clashes"],
            "Restart_Costs_Mean": round(float(np.mean(restart_costs)), 2),
            "Restart_Costs_Std": round(float(np.std(restart_costs)), 2)
        })
        print(f"  P={p} cores: WallTime={wall_t_ms:6.2f}ms | Speedup={speedup:4.2f}x | BestPenalty={eval_res['total_penalty']:6.1f} | Clashes={eval_res['student_clashes']} | RestartsMean={np.mean(restart_costs):6.1f} ± {np.std(restart_costs):4.1f}")

    exp2_csv = os.path.join(results_dir, "parallel_sa_scaling_analysis.csv")
    with open(exp2_csv, "w", encoding="utf-8") as f:
        headers = list(exp2_rows[0].keys())
        f.write(",".join(headers) + "\n")
        for r in exp2_rows:
            f.write(",".join(str(r[h]) for h in headers) + "\n")
    print(f"[Results] Exported Experiment 2 summary to {exp2_csv}")

    # -----------------------------------------------------------------
    # Experiment 3: Instance Size Scaling Experiment
    # -----------------------------------------------------------------
    print("\n[Experiment 3] Scaling experiment across student population sizes (100, 300, 1000, 3000)...")
    scale_files = [
        ("100_Students", os.path.join(data_dir, "synthetic_scale_100.json")),
        ("300_Students", os.path.join(data_dir, "synthetic_scale_300.json")),
        ("1000_Students", os.path.join(data_dir, "synthetic_scale_1000.json")),
        ("3000_Students", os.path.join(data_dir, "synthetic_scale_3000.json")),
    ]

    scale_rows = []
    for s_label, s_path in scale_files:
        with open(s_path, "r", encoding="utf-8") as f:
            inst_data = json.load(f)
        val = TimetableValidator(inst_data)

        # DSATUR
        dsatur_sched, dsatur_rt = DSATURSolver(inst_data).solve(seed=42)
        dsatur_eval = val.evaluate_schedule(dsatur_sched)

        # ILP (2s limit)
        ilp_sched, ilp_rt = ILPSolver(inst_data).solve(time_limit=2.0, seed=42)
        ilp_eval = val.evaluate_schedule(ilp_sched)

        # Parallel SA (4 restarts)
        sa_sched, sa_cost, _, sa_rt = ParallelSASolver(inst_data).solve(num_restarts=4, max_iterations=400, base_seed=42)
        sa_eval = val.evaluate_schedule(sa_sched)

        scale_rows.append({
            "Instance": s_label,
            "Students": inst_data["metadata"]["num_students"],
            "Courses": inst_data["metadata"]["num_courses"],
            "Conflict_Density": inst_data["metadata"]["conflict_graph_density"],
            "DSATUR_Penalty": round(dsatur_eval["total_penalty"], 1),
            "DSATUR_Runtime_ms": round(dsatur_rt, 2),
            "DSATUR_Feasible": dsatur_eval["is_feasible"],
            "ILP_Penalty": round(ilp_eval["total_penalty"], 1),
            "ILP_Runtime_ms": round(ilp_rt, 2),
            "ILP_Feasible": ilp_eval["is_feasible"],
            "Parallel_SA_Penalty": round(sa_eval["total_penalty"], 1),
            "Parallel_SA_Runtime_ms": round(sa_rt, 2),
            "Parallel_SA_Feasible": sa_eval["is_feasible"]
        })
        print(f"  {s_label:14s} | DSATUR: {dsatur_eval['total_penalty']:6.1f} ({dsatur_rt:5.2f}ms) | ILP: {ilp_eval['total_penalty']:6.1f} ({ilp_rt:5.2f}ms) | SA: {sa_eval['total_penalty']:6.1f} ({sa_rt:5.2f}ms)")

    scale_csv = os.path.join(results_dir, "scaling_experiment_summary.csv")
    with open(scale_csv, "w", encoding="utf-8") as f:
        headers = list(scale_rows[0].keys())
        f.write(",".join(headers) + "\n")
        for r in scale_rows:
            f.write(",".join(str(r[h]) for h in headers) + "\n")
    print(f"[Results] Exported Experiment 3 summary to {scale_csv}")

    # -----------------------------------------------------------------
    # Experiment 4: Toronto Benchmark Instance Evaluation
    # -----------------------------------------------------------------
    print("\n[Experiment 4] Evaluating Toronto Carter Benchmark Instance (toronto_carter_sample)...")
    crs_path = os.path.join(data_dir, "toronto_carter_sample.crs")
    stu_path = os.path.join(data_dir, "toronto_carter_sample.stu")
    toronto_inst = parse_toronto_instance(crs_path, stu_path, num_slots=18, slots_per_day=3, room_capacity_per_slot=1000)
    toronto_val = TimetableValidator(toronto_inst)

    tor_dsatur_sched, tor_dsatur_rt = DSATURSolver(toronto_inst).solve(seed=42)
    tor_dsatur_eval = toronto_val.evaluate_schedule(tor_dsatur_sched)

    tor_sa_sched, _, _, tor_sa_rt = ParallelSASolver(toronto_inst).solve(num_restarts=4, max_iterations=500, base_seed=42)
    tor_sa_eval = toronto_val.evaluate_schedule(tor_sa_sched)

    toronto_rows = [
        {
            "Instance": "toronto_carter_sample",
            "Courses": 30,
            "Students": 200,
            "Slots": 18,
            "Method": "DSATUR",
            "Feasible": tor_dsatur_eval["is_feasible"],
            "Clashes": tor_dsatur_eval["student_clashes"],
            "Capacity_Violations": tor_dsatur_eval["capacity_violations"],
            "Back_to_Back": tor_dsatur_eval["back_to_back_count"],
            "Three_Plus_Day": tor_dsatur_eval["three_plus_day_count"],
            "Total_Penalty": round(tor_dsatur_eval["total_penalty"], 1),
            "Runtime_ms": round(tor_dsatur_rt, 2)
        },
        {
            "Instance": "toronto_carter_sample",
            "Courses": 30,
            "Students": 200,
            "Slots": 18,
            "Method": "Parallel_SA",
            "Feasible": tor_sa_eval["is_feasible"],
            "Clashes": tor_sa_eval["student_clashes"],
            "Capacity_Violations": tor_sa_eval["capacity_violations"],
            "Back_to_Back": tor_sa_eval["back_to_back_count"],
            "Three_Plus_Day": tor_sa_eval["three_plus_day_count"],
            "Total_Penalty": round(tor_sa_eval["total_penalty"], 1),
            "Runtime_ms": round(tor_sa_rt, 2)
        }
    ]

    toronto_csv = os.path.join(results_dir, "toronto_benchmark_summary.csv")
    with open(toronto_csv, "w", encoding="utf-8") as f:
        headers = list(toronto_rows[0].keys())
        f.write(",".join(headers) + "\n")
        for r in toronto_rows:
            f.write(",".join(str(r[h]) for h in headers) + "\n")
    print(f"[Results] Exported Experiment 4 summary to {toronto_csv}")
    print(f"  Toronto DSATUR    : Feasible={tor_dsatur_eval['is_feasible']} | Clashes={tor_dsatur_eval['student_clashes']} | Penalty={tor_dsatur_eval['total_penalty']} | Runtime={tor_dsatur_rt:.2f}ms")
    print(f"  Toronto ParallelSA: Feasible={tor_sa_eval['is_feasible']} | Clashes={tor_sa_eval['student_clashes']} | Penalty={tor_sa_eval['total_penalty']} | Runtime={tor_sa_rt:.2f}ms")

    # -----------------------------------------------------------------
    # Experiment 5: Sensitivity Analysis (Phase Transitions)
    # -----------------------------------------------------------------
    print("\n[Experiment 5] Sensitivity analysis across slot counts and capacity tightness...")
    sens_rows = []
    slot_sweep = [10, 12, 14, 16, 18, 20]
    cap_sweep = [150, 250, 350]

    with open(os.path.join(data_dir, "synthetic_scale_100.json"), "r", encoding="utf-8") as f:
        base_inst = json.load(f)

    for cap in cap_sweep:
        for s_count in slot_sweep:
            mod_inst = dict(base_inst)
            mod_inst["metadata"] = dict(base_inst["metadata"])
            mod_inst["metadata"]["num_slots"] = s_count
            mod_inst["metadata"]["total_room_capacity_per_slot"] = cap
            mod_inst["metadata"]["num_days"] = max(1, s_count // 3)

            sens_val = TimetableValidator(mod_inst)
            s_sched, s_rt = DSATURSolver(mod_inst).solve(seed=42)
            s_eval = sens_val.evaluate_schedule(s_sched)

            sens_rows.append({
                "Capacity_Per_Slot": cap,
                "Slots_Available": s_count,
                "Feasible": s_eval["is_feasible"],
                "Student_Clashes": s_eval["student_clashes"],
                "Capacity_Violations": s_eval["capacity_violations"],
                "Total_Penalty": round(s_eval["total_penalty"], 1),
                "Runtime_ms": round(s_rt, 2)
            })

    sens_csv = os.path.join(results_dir, "sensitivity_analysis_summary.csv")
    with open(sens_csv, "w", encoding="utf-8") as f:
        headers = list(sens_rows[0].keys())
        f.write(",".join(headers) + "\n")
        for r in sens_rows:
            f.write(",".join(str(r[h]) for h in headers) + "\n")
    print(f"[Results] Exported Experiment 5 summary to {sens_csv}")

    # -----------------------------------------------------------------
    # Visualizations: Multi-Panel Optimization Plots
    # -----------------------------------------------------------------
    plot_path = os.path.join(results_dir, "track_e_optimization_performance.png")
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    # Panel 1: Primary Instance Multi-Solver Objective Comparison
    ax1 = axes[0, 0]
    names = ["Random", "FirstFit", "DSATUR", "ILP (2s)", "SA (1-th)", "Parallel SA (4c)"]
    means = [
        next(r["Mean"] for r in summary_rows if r["Solver"] == "Random" and r["Metric"] == "total_penalty"),
        next(r["Mean"] for r in summary_rows if r["Solver"] == "FirstFit" and r["Metric"] == "total_penalty"),
        next(r["Mean"] for r in summary_rows if r["Solver"] == "DSATUR" and r["Metric"] == "total_penalty"),
        next(r["Mean"] for r in summary_rows if r["Solver"] == "ILP_HiGHS_2s" and r["Metric"] == "total_penalty"),
        next(r["Mean"] for r in summary_rows if r["Solver"] == "SimulatedAnnealing" and r["Metric"] == "total_penalty"),
        next(r["Mean"] for r in summary_rows if r["Solver"] == "Parallel_SA_4cores" and r["Metric"] == "total_penalty"),
    ]
    stds = [
        next(r["Std"] for r in summary_rows if r["Solver"] == "Random" and r["Metric"] == "total_penalty"),
        next(r["Std"] for r in summary_rows if r["Solver"] == "FirstFit" and r["Metric"] == "total_penalty"),
        next(r["Std"] for r in summary_rows if r["Solver"] == "DSATUR" and r["Metric"] == "total_penalty"),
        next(r["Std"] for r in summary_rows if r["Solver"] == "ILP_HiGHS_2s" and r["Metric"] == "total_penalty"),
        next(r["Std"] for r in summary_rows if r["Solver"] == "SimulatedAnnealing" and r["Metric"] == "total_penalty"),
        next(r["Std"] for r in summary_rows if r["Solver"] == "Parallel_SA_4cores" and r["Metric"] == "total_penalty"),
    ]
    bars = ax1.bar(names, means, yerr=stds, capsize=5, color=["#d62728", "#ff7f0e", "#1f77b4", "#2ca02c", "#9467bd", "#8c564b"], alpha=0.85, edgecolor='black')
    ax1.set_ylabel("Weighted Objective Penalty (Lower is Better)", fontsize=10, fontweight='bold')
    ax1.set_title("Primary Instance Solver Comparison (300 Students, 10 Seeds)", fontsize=11, fontweight='bold')
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels(names, rotation=25, ha='right', fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.4, axis='y')

    # Panel 2: Parallel SA Speedup & Scaling vs Cores
    ax2 = axes[0, 1]
    p_cores = [r["Worker_Cores"] for r in exp2_rows]
    p_speedup = [r["Parallel_Speedup_Factor"] for r in exp2_rows]
    ax2.plot(p_cores, p_speedup, marker='o', linewidth=2, color="#1f77b4", label="Parallel Speedup (SA Restarts)")
    ax2.plot(p_cores, p_cores, linestyle='--', color='gray', label="Ideal Linear Speedup")
    ax2.set_xlabel("CPU Cores (Parallel Restarts)", fontsize=10, fontweight='bold')
    ax2.set_ylabel("Speedup Factor", fontsize=10, fontweight='bold')
    ax2.set_title("Parallel Restarts Scaling on Intel Alder Lake (6 Cores)", fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.4)

    # Panel 3: Instance Size Scaling Runtime
    ax3 = axes[1, 0]
    sizes = [r["Students"] for r in scale_rows]
    dsatur_rts = [r["DSATUR_Runtime_ms"] for r in scale_rows]
    ilp_rts = [r["ILP_Runtime_ms"] for r in scale_rows]
    sa_rts = [r["Parallel_SA_Runtime_ms"] for r in scale_rows]

    ax3.plot(sizes, dsatur_rts, marker='s', label="DSATUR Greedy (O(V+E))", color="#1f77b4", linewidth=2)
    ax3.plot(sizes, ilp_rts, marker='^', label="ILP HiGHS (5s Timeout Cap)", color="#2ca02c", linewidth=2)
    ax3.plot(sizes, sa_rts, marker='o', label="Parallel SA (4 Workers)", color="#d62728", linewidth=2)
    ax3.set_yscale('log')
    ax3.set_xlabel("Student Population Size", fontsize=10, fontweight='bold')
    ax3.set_ylabel("Runtime in ms (Log Scale)", fontsize=10, fontweight='bold')
    ax3.set_title("Runtime Scaling vs Problem Dimension", fontsize=11, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, linestyle="--", alpha=0.4)

    # Panel 4: Sensitivity Phase Transition (Clashes vs Slots Available)
    ax4 = axes[1, 1]
    for cap in cap_sweep:
        clashes = [r["Student_Clashes"] for r in sens_rows if r["Capacity_Per_Slot"] == cap]
        ax4.plot(slot_sweep, clashes, marker='o', label=f"Cap={cap} Seats/Slot", linewidth=2)
    ax4.axhline(0, color='green', linestyle=':', label="Feasible Boundary (0 Clashes)")
    ax4.set_xlabel("Available Exam Time Slots", fontsize=10, fontweight='bold')
    ax4.set_ylabel("Student Exam Clashes", fontsize=10, fontweight='bold')
    ax4.set_title("Feasibility Phase Transition: Clashes vs Slot Scarcity", fontsize=11, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"[Results] Visualization plots exported to {plot_path}")

    print("\n" + "=" * 80)
    print("TRACK E EXPERIMENTAL SUITE COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_all_track_e_benchmarks()
