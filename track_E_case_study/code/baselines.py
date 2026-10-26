"""
baselines.py
------------
Baseline Scheduling Algorithms for University Exam Timetabling.

Implements:
  1. RandomSchedule: Uncoordinated uniform stochastic assignment.
  2. FirstFitSchedule: Greedy constructive first-fit heuristic.

Evaluates both heuristics over 10 repeated runs with deterministic fixed seeds (0..9)
on the primary synthetic benchmark instance (300 students, 40 courses, 12 slots).
Reports feasibility rate, clashes, back-to-back count, 3+ exams/day, slots used,
and wall-clock runtime (mean +/- std).
"""

import json
import os
import random
import time
from typing import Dict, List, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt

import sys

# Ensure repository root is on sys.path for direct script execution
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_E_case_study.code.validator import TimetableValidator


class RandomScheduler:
    """
    Baseline 1: Random Schedule.
    Assigns each course to a randomly chosen slot uniformly.
    """

    def __init__(self, instance: Dict[str, Any], seed: int = 42):
        self.instance = instance
        self.num_courses = instance["metadata"]["num_courses"]
        self.num_slots = instance["metadata"]["num_slots"]
        self.rng = random.Random(seed)

    def solve(self) -> Tuple[Dict[int, int], float]:
        start_time = time.perf_counter()
        schedule = {}
        for c in range(self.num_courses):
            schedule[c] = self.rng.randint(0, self.num_slots - 1)
        runtime_ms = (time.perf_counter() - start_time) * 1000.0
        return schedule, runtime_ms


class FirstFitScheduler:
    """
    Baseline 2: Greedy First-Fit Schedule.
    Considers courses in an order (random permutation determined by seed),
    and assigns each course to the first time slot that does not cause
    a student clash or exceed venue capacity.
    If no clash-free slot is available, it selects the slot minimizing clashes.
    """

    def __init__(self, instance: Dict[str, Any], seed: int = 42):
        self.instance = instance
        self.num_courses = instance["metadata"]["num_courses"]
        self.num_slots = instance["metadata"]["num_slots"]
        self.capacity_per_slot = instance["metadata"]["total_room_capacity_per_slot"]
        self.course_enrollments = instance["course_enrollment_counts"]
        self.student_enrollments = {
            int(k): v for k, v in instance["student_enrollments"].items()
        }
        self.conflicts = instance["conflicts"]
        self.rng = random.Random(seed)

    def has_conflict(self, c1: int, c2: int) -> bool:
        low, high = min(c1, c2), max(c1, c2)
        return f"{low},{high}" in self.conflicts

    def solve(self) -> Tuple[Dict[int, int], float]:
        start_time = time.perf_counter()

        # Arrival ordering of courses determined by seed
        courses = list(range(self.num_courses))
        self.rng.shuffle(courses)

        schedule: Dict[int, int] = {}
        slot_courses: Dict[int, List[int]] = {s: [] for s in range(self.num_slots)}
        slot_sizes: Dict[int, int] = {s: 0 for s in range(self.num_slots)}

        for c in courses:
            c_size = self.course_enrollments.get(str(c), self.course_enrollments.get(c, 0))
            best_slot = None
            min_clashes = float("inf")

            # Try to find first slot with 0 clashes and capacity headroom
            for s in range(self.num_slots):
                # Check room capacity
                if slot_sizes[s] + c_size > self.capacity_per_slot:
                    continue

                # Count clashes with courses already placed in slot s
                clashes = sum(1 for placed in slot_courses[s] if self.has_conflict(c, placed))
                if clashes == 0:
                    best_slot = s
                    break
                elif clashes < min_clashes:
                    min_clashes = clashes
                    best_slot = s

            # Fallback if all slots violate capacity or have clashes
            if best_slot is None:
                # Find slot with least capacity overflow
                best_slot = min(slot_sizes.keys(), key=lambda s: slot_sizes[s])

            schedule[c] = best_slot
            slot_courses[best_slot].append(c)
            slot_sizes[best_slot] += c_size

        runtime_ms = (time.perf_counter() - start_time) * 1000.0
        return schedule, runtime_ms


def run_baseline_benchmark(
    instance_path: str = "track_E_case_study/data/synthetic_primary_300.json",
    num_runs: int = 10,
    results_dir: str = "track_E_case_study/results",
) -> Dict[str, Any]:
    """
    Executes 10 repeated runs of Random and First-Fit baselines with seeds 0..9.
    Measures metrics, calculates mean +/- std, and writes reports & plots.
    """
    os.makedirs(results_dir, exist_ok=True)

    with open(instance_path, "r", encoding="utf-8") as f:
        instance = json.load(f)

    validator = TimetableValidator(instance)

    schedulers = {
        "Random": RandomScheduler,
        "FirstFit": FirstFitScheduler,
    }

    experiment_records: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in schedulers.keys()
    }

    seeds = list(range(num_runs))

    for name, SchedulerClass in schedulers.items():
        for s in seeds:
            scheduler = SchedulerClass(instance, seed=s)
            schedule, runtime_ms = scheduler.solve()
            metrics = validator.evaluate_schedule(schedule)
            metrics["seed"] = s
            metrics["runtime_ms"] = runtime_ms
            metrics["is_feasible_int"] = 1 if metrics["is_feasible"] else 0
            experiment_records[name].append(metrics)

    # Compute statistical summaries (mean and std)
    summary: Dict[str, Dict[str, Any]] = {}
    metric_keys = [
        "is_feasible_int",
        "student_clashes",
        "capacity_violations",
        "back_to_back_count",
        "three_plus_day_count",
        "slots_used",
        "total_penalty",
        "runtime_ms",
    ]

    for name, records in experiment_records.items():
        summary[name] = {}
        for k in metric_keys:
            vals = [r[k] for r in records]
            summary[name][k] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
            }

    # Save raw records & summary to JSON
    output_data = {
        "metadata": {
            "instance": instance["metadata"]["name"],
            "num_runs": num_runs,
            "seeds": seeds,
            "hardware_labeled": "[Hardware-Measured]",
        },
        "summary": summary,
        "raw_records": experiment_records,
    }

    json_path = os.path.join(results_dir, "baseline_experiments.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Save summary CSV
    csv_path = os.path.join(results_dir, "baseline_summary.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Method,Metric,Mean,Std,Min,Max\n")
        for name, m_dict in summary.items():
            for k, s_dict in m_dict.items():
                f.write(
                    f"{name},{k},{s_dict['mean']:.4f},{s_dict['std']:.4f},{s_dict['min']:.4f},{s_dict['max']:.4f}\n"
                )

    # Generate Visualization Plot
    plot_path = os.path.join(results_dir, "baseline_inefficiency_comparison.png")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    methods = ["Random", "FirstFit"]
    colors = ["#e74c3c", "#3498db"]

    # 1. Student Clashes
    clash_means = [summary[m]["student_clashes"]["mean"] for m in methods]
    clash_stds = [summary[m]["student_clashes"]["std"] for m in methods]
    axes[0, 0].bar(methods, clash_means, yerr=clash_stds, capsize=6, color=colors, alpha=0.85)
    axes[0, 0].set_title("Hard Student Clashes (Target: 0)", fontsize=12, fontweight="bold")
    axes[0, 0].set_ylabel("Student-Exam Clash Instances")
    axes[0, 0].grid(axis="y", linestyle="--", alpha=0.6)

    # 2. Back-to-Back Count
    b2b_means = [summary[m]["back_to_back_count"]["mean"] for m in methods]
    b2b_stds = [summary[m]["back_to_back_count"]["std"] for m in methods]
    axes[0, 1].bar(methods, b2b_means, yerr=b2b_stds, capsize=6, color=colors, alpha=0.85)
    axes[0, 1].set_title("Back-to-Back Exams on Same Day", fontsize=12, fontweight="bold")
    axes[0, 1].set_ylabel("Penalty Count")
    axes[0, 1].grid(axis="y", linestyle="--", alpha=0.6)

    # 3. 3+ Exams in a Single Day
    tp_means = [summary[m]["three_plus_day_count"]["mean"] for m in methods]
    tp_stds = [summary[m]["three_plus_day_count"]["std"] for m in methods]
    axes[1, 0].bar(methods, tp_means, yerr=tp_stds, capsize=6, color=colors, alpha=0.85)
    axes[1, 0].set_title("3+ Exams in a Single Day (Target: 0)", fontsize=12, fontweight="bold")
    axes[1, 0].set_ylabel("Excess Instances")
    axes[1, 0].grid(axis="y", linestyle="--", alpha=0.6)

    # 4. Total Objective Penalty
    pen_means = [summary[m]["total_penalty"]["mean"] for m in methods]
    pen_stds = [summary[m]["total_penalty"]["std"] for m in methods]
    axes[1, 1].bar(methods, pen_means, yerr=pen_stds, capsize=6, color=colors, alpha=0.85)
    axes[1, 1].set_title("Overall Penalty Cost Z", fontsize=12, fontweight="bold")
    axes[1, 1].set_ylabel("Weighted Penalty Value")
    axes[1, 1].grid(axis="y", linestyle="--", alpha=0.6)

    plt.suptitle("Evidence of Inefficiency: Baseline Heuristics on 300-Student Instance (10 Seeds)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=300)
    plt.close()

    print(f"Benchmark completed successfully across 10 seeds.")
    print(f"Results saved to: {json_path}")
    print(f"Summary saved to: {csv_path}")
    print(f"Plot saved to: {plot_path}")

    return output_data


if __name__ == "__main__":
    run_baseline_benchmark()
