"""
Track G: xv6 Operating-System Scheduler Simulation & Verification Harness.
Accurately models xv6 RISC-V process scheduler behavior:
- Baseline: Default Round-Robin FIFO ring-buffer dispatch.
- Optimized: Proportional-Share Lottery Scheduling (Waldspurger & Weihl).

Evaluates three user workloads from Track G:
1. bench_cpu: Compute-bound processes with tickets [30, 20, 10].
2. bench_io: I/O-bound responsive processes yielding via sleep/disk I/O.
3. bench_mixed: Coexisting CPU hogs and interactive tasks.

Measures:
- Ticks allocated & CPU share percentage
- Turnaround time and response latency
- Jain's Fairness Index
"""

import os
import sys
import random
import csv
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


class SimProcess:
    def __init__(self, pid: int, name: str, tickets: int, remaining_work: int, io_frequency: int = 0, io_duration: int = 0):
        self.pid = pid
        self.name = name
        self.tickets = max(1, tickets)
        self.remaining_work = remaining_work
        self.total_work = remaining_work
        self.io_frequency = io_frequency  # Ticks between I/O bursts
        self.io_duration = io_duration    # Ticks spent sleeping in I/O
        self.ticks_since_io = 0
        self.io_remaining = 0
        self.ticks_received = 0
        self.arrival_time = 0
        self.completion_time = 0
        self.wait_ticks = 0
        self.response_time = -1

    @property
    def is_runnable(self) -> bool:
        return self.remaining_work > 0 and self.io_remaining <= 0

    @property
    def is_sleeping(self) -> bool:
        return self.io_remaining > 0

    @property
    def is_finished(self) -> bool:
        return self.remaining_work <= 0


def run_scheduler_simulation(
    processes: List[SimProcess],
    policy: str = "lottery",
    seed: int = 42
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Simulates xv6 scheduler step-by-step.
    policy: 'round_robin' or 'lottery'
    """
    rng = random.Random(seed)
    current_tick = 0
    rr_index = 0

    procs = [
        SimProcess(
            p.pid, p.name, p.tickets, p.remaining_work, p.io_frequency, p.io_duration
        )
        for p in processes
    ]

    while any(not p.is_finished for p in procs):
        # Update I/O timers
        for p in procs:
            if p.is_sleeping:
                p.io_remaining -= 1

        runnable_procs = [p for p in procs if p.is_runnable]

        if not runnable_procs:
            current_tick += 1
            continue

        selected_proc = None
        if policy == "round_robin":
            rr_index = rr_index % len(runnable_procs)
            selected_proc = runnable_procs[rr_index]
            rr_index = (rr_index + 1) % len(runnable_procs)
        elif policy == "lottery":
            total_tickets = sum(p.tickets for p in runnable_procs)
            winning_ticket = rng.randint(0, total_tickets - 1)
            counter = 0
            for p in runnable_procs:
                counter += p.tickets
                if counter > winning_ticket:
                    selected_proc = p
                    break
        else:
            raise ValueError(f"Unknown policy: {policy}")

        assert selected_proc is not None

        # Dispatch selected process for 1 tick
        if selected_proc.response_time < 0:
            selected_proc.response_time = current_tick - selected_proc.arrival_time

        selected_proc.ticks_received += 1
        selected_proc.remaining_work -= 1
        selected_proc.ticks_since_io += 1

        # Check for I/O burst
        if selected_proc.io_frequency > 0 and selected_proc.ticks_since_io >= selected_proc.io_frequency:
            selected_proc.ticks_since_io = 0
            selected_proc.io_remaining = selected_proc.io_duration

        if selected_proc.is_finished and selected_proc.completion_time == 0:
            selected_proc.completion_time = current_tick + 1

        # Track waiting ticks for other runnable procs
        for p in runnable_procs:
            if p.pid != selected_proc.pid:
                p.wait_ticks += 1

        current_tick += 1

    total_ticks = current_tick
    proc_stats = []
    for p in procs:
        turnaround = p.completion_time - p.arrival_time
        share_pct = (p.ticks_received / total_ticks) * 100.0 if total_ticks > 0 else 0.0
        proc_stats.append({
            "pid": p.pid,
            "name": p.name,
            "tickets": p.tickets,
            "ticks": p.ticks_received,
            "share_pct": share_pct,
            "turnaround": turnaround,
            "response_time": p.response_time,
            "wait_ticks": p.wait_ticks
        })

    # Calculate Jain's Fairness Index on CPU allocation relative to tickets
    # Ratio r_i = actual_ticks_i / tickets_i
    ratios = [stat["ticks"] / stat["tickets"] for stat in proc_stats]
    sum_r = sum(ratios)
    sum_sq_r = sum(r * r for r in ratios)
    n = len(proc_stats)
    jains_index = (sum_r ** 2) / (n * sum_sq_r) if sum_sq_r > 0 else 1.0

    summary = {
        "policy": policy,
        "total_ticks": total_ticks,
        "jains_fairness_index": jains_index,
        "avg_turnaround": sum(s["turnaround"] for s in proc_stats) / n,
        "avg_response": sum(s["response_time"] for s in proc_stats) / n
    }

    return summary, proc_stats


def run_all_xv6_benchmarks() -> Dict[str, Any]:
    print("=" * 70)
    print("TRACK G: xv6 SCHEDULER EMPIRICAL BENCHMARKS (Round-Robin vs Lottery)")
    print("=" * 70)

    # 1. Workload 1: CPU-bound (3 workers, tickets [30, 20, 10], work=600 ticks each)
    w1_procs = [
        SimProcess(pid=1, name="cpu_high_30", tickets=30, remaining_work=600),
        SimProcess(pid=2, name="cpu_med_20", tickets=20, remaining_work=600),
        SimProcess(pid=3, name="cpu_low_10", tickets=10, remaining_work=600),
    ]

    rr_summary1, rr_stats1 = run_scheduler_simulation(w1_procs, policy="round_robin", seed=100)
    lot_summary1, lot_stats1 = run_scheduler_simulation(w1_procs, policy="lottery", seed=100)

    print("\n--- Workload 1: CPU-Bound Compute Intensive (Tickets 30 : 20 : 10) ---")
    print(f"Policy: Round-Robin | Total Ticks: {rr_summary1['total_ticks']} | Jain's Fairness: {rr_summary1['jains_fairness_index']:.4f}")
    for s in rr_stats1:
        print(f"  PID {s['pid']} ({s['name']}): Ticks={s['ticks']}, Share={s['share_pct']:.2f}%, Turnaround={s['turnaround']}")

    print(f"\nPolicy: Lottery     | Total Ticks: {lot_summary1['total_ticks']} | Jain's Fairness (ticket-weighted): {lot_summary1['jains_fairness_index']:.4f}")
    for s in lot_stats1:
        print(f"  PID {s['pid']} ({s['name']}): Ticks={s['ticks']}, Share={s['share_pct']:.2f}%, Turnaround={s['turnaround']}")

    # 2. Workload 2: I/O-bound (Interactive task 20 tickets vs CPU hog 10 tickets)
    w2_procs = [
        SimProcess(pid=1, name="io_interactive_20", tickets=20, remaining_work=100, io_frequency=5, io_duration=2),
        SimProcess(pid=2, name="cpu_hog_10", tickets=10, remaining_work=500),
    ]
    rr_summary2, rr_stats2 = run_scheduler_simulation(w2_procs, policy="round_robin", seed=200)
    lot_summary2, lot_stats2 = run_scheduler_simulation(w2_procs, policy="lottery", seed=200)

    # 3. Workload 3: Mixed (2 CPU workers + 2 I/O workers)
    w3_procs = [
        SimProcess(pid=1, name="cpu_worker_1", tickets=30, remaining_work=400),
        SimProcess(pid=2, name="cpu_worker_2", tickets=10, remaining_work=400),
        SimProcess(pid=3, name="io_worker_3", tickets=30, remaining_work=150, io_frequency=10, io_duration=3),
        SimProcess(pid=4, name="io_worker_4", tickets=10, remaining_work=150, io_frequency=10, io_duration=3),
    ]
    rr_summary3, rr_stats3 = run_scheduler_simulation(w3_procs, policy="round_robin", seed=300)
    lot_summary3, lot_stats3 = run_scheduler_simulation(w3_procs, policy="lottery", seed=300)

    # Save to CSV
    csv_path = os.path.join(RESULTS_DIR, "lottery_vs_roundrobin_results.csv")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workload", "policy", "pid", "name", "tickets", "ticks", "share_pct", "turnaround", "response_time"])
        for s in rr_stats1:
            writer.writerow(["workload_1_cpu", "round_robin", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])
        for s in lot_stats1:
            writer.writerow(["workload_1_cpu", "lottery", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])
        for s in rr_stats2:
            writer.writerow(["workload_2_io", "round_robin", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])
        for s in lot_stats2:
            writer.writerow(["workload_2_io", "lottery", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])
        for s in rr_stats3:
            writer.writerow(["workload_3_mixed", "round_robin", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])
        for s in lot_stats3:
            writer.writerow(["workload_3_mixed", "lottery", s["pid"], s["name"], s["tickets"], s["ticks"], f"{s['share_pct']:.2f}", s["turnaround"], s["response_time"]])

    print(f"\n[Artifact] Results saved to: {csv_path}")

    # Generate Visualization Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Subplot 1: Workload 1 CPU Share Comparison
    pids = [s["name"] for s in lot_stats1]
    rr_shares = [s["share_pct"] for s in rr_stats1]
    lot_shares = [s["share_pct"] for s in lot_stats1]
    expected_shares = [50.0, 33.33, 16.67]

    x = range(len(pids))
    width = 0.25
    axes[0].bar([i - width for i in x], rr_shares, width=width, label="Round-Robin", color="#64748b")
    axes[0].bar(x, lot_shares, width=width, label="Lottery (Simulated)", color="#0ea5e9")
    axes[0].bar([i + width for i in x], expected_shares, width=width, label="Analytical (Ideal)", color="#10b981", alpha=0.7)
    axes[0].set_ylabel("CPU Execution Share (%)")
    axes[0].set_title("Workload 1: Proportional Share Convergence (30:20:10 Tickets)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(["PID 1 (30 tix)", "PID 2 (20 tix)", "PID 3 (10 tix)"])
    axes[0].legend()
    axes[0].grid(axis="y", linestyle="--", alpha=0.5)

    # Subplot 2: Workload 1 Turnaround Time Comparison
    rr_turnaround = [s["turnaround"] for s in rr_stats1]
    lot_turnaround = [s["turnaround"] for s in lot_stats1]
    axes[1].bar([i - width/2 for i in x], rr_turnaround, width=width, label="Round-Robin", color="#64748b")
    axes[1].bar([i + width/2 for i in x], lot_turnaround, width=width, label="Lottery", color="#f59e0b")
    axes[1].set_ylabel("Turnaround Time (Ticks)")
    axes[1].set_title("Workload 1: Process Turnaround Time")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(["PID 1 (30 tix)", "PID 2 (20 tix)", "PID 3 (10 tix)"])
    axes[1].legend()
    axes[1].grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "xv6_scheduling_performance.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[Artifact] Performance plot saved to: {plot_path}")

    return {
        "csv_path": csv_path,
        "plot_path": plot_path,
        "w1_rr": rr_summary1,
        "w1_lot": lot_summary1
    }


if __name__ == "__main__":
    run_all_xv6_benchmarks()
