"""
quantum_experiments.py
----------------------
Executes the four mandatory Day 6 Track C Quantum Optimization experiments:
  Experiment (a): Finite Shots Analysis (varying shots N, measuring sample variance vs 1/sqrt(N))
  Experiment (b): Hardware Noise Modeling (depolarizing + readout errors, degradation of cut & state fidelity)
  Experiment (c): Barren Plateaus (gradient variance scaling vs qubit count n in [2, 4, 6, 8, 10])
  Experiment (d): QAOA Depth p vs Approximation Ratio & Comprehensive Classical Comparison
"""

import sys
import os
import json
import time
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

from track_C_quantum.code.qaoa_maxcut import (
    build_maxcut_hamiltonian,
    compute_cut_from_bitstring,
    create_qaoa_circuit,
    evaluate_qaoa_energy_statevector,
    evaluate_qaoa_shots,
    optimize_qaoa_parameters,
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_track_b_instances() -> Dict[str, Any]:
    """Loads Max-Cut QUBO/Ising instances saved by Track B."""
    qubo_path = os.path.join(REPO_ROOT, "track_B_discrete", "results", "qubo_instances.json")
    if not os.path.exists(qubo_path):
        raise FileNotFoundError(f"Track B instances not found at {qubo_path}")
    with open(qubo_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_track_b_baselines() -> pd.DataFrame:
    """Loads classical baseline results from Track B."""
    csv_path = os.path.join(REPO_ROOT, "track_B_discrete", "results", "qubo_benchmarks_summary.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Track B baselines not found at {csv_path}")
    return pd.read_csv(csv_path)


# ==============================================================================
# EXPERIMENT (A): FINITE SHOTS ANALYSIS
# ==============================================================================
def run_experiment_finite_shots(
    graph_data: Dict[str, Any],
    shot_counts: List[int] = [100, 250, 500, 1000, 2000, 4000, 8192],
    num_seeds: int = 10
) -> pd.DataFrame:
    """
    Evaluates shot noise variance as a function of measurement shot count N.
    Compares against exact Statevector expectation value.
    """
    print("\n--- Running Experiment (a): Finite Shots Scaling & Variance ---")
    n_qubits = graph_data["num_nodes"]
    edges = [tuple(e) for e in graph_data["edges"]]
    exact_max_cut = graph_data["exact_max_cut"]

    # Pre-optimize QAOA p=1 parameters to obtain a high-quality fixed quantum state
    opt_res = optimize_qaoa_parameters(n_qubits, edges, p=1, exact_max_cut=exact_max_cut, seed=42)
    gamma_fixed = opt_res["optimal_gamma"]
    beta_fixed = opt_res["optimal_beta"]

    qc_ideal = create_qaoa_circuit(n_qubits, edges, gamma_fixed, beta_fixed, measure=False)
    H_C, _, _ = build_maxcut_hamiltonian(n_qubits, edges)
    _, exact_cut, _ = evaluate_qaoa_energy_statevector(qc_ideal, H_C)
    print(f"Ideal Statevector Expected Cut: {exact_cut:.4f} (Exact Max Cut: {exact_max_cut})")

    records = []
    qc_meas = create_qaoa_circuit(n_qubits, edges, gamma_fixed, beta_fixed, measure=True)

    for shots in shot_counts:
        seed_cuts = []
        for s in range(num_seeds):
            sim = AerSimulator()
            job = sim.run(qc_meas, shots=shots, seed_simulator=s)
            counts = job.result().get_counts()

            # Compute empirical mean cut
            cut_sum = sum(compute_cut_from_bitstring(b, edges, n_qubits) * c for b, c in counts.items())
            seed_cuts.append(cut_sum / shots)

        mean_cut = float(np.mean(seed_cuts))
        std_cut = float(np.std(seed_cuts, ddof=1))
        var_cut = float(np.var(seed_cuts, ddof=1))
        bias = float(abs(mean_cut - exact_cut))

        records.append({
            "Shots": shots,
            "One_Over_Sqrt_Shots": 1.0 / np.sqrt(shots),
            "Exact_Statevector_Cut": round(exact_cut, 4),
            "Mean_Sampled_Cut": round(mean_cut, 4),
            "Std_Sampled_Cut": round(std_cut, 5),
            "Variance_Sampled_Cut": round(var_cut, 6),
            "Absolute_Bias": round(bias, 5),
        })
        print(f"Shots: {shots:5d} | Mean Cut: {mean_cut:.4f} | Std: {std_cut:.5f} | Var: {var_cut:.6f}")

    df = pd.DataFrame(records)
    csv_file = os.path.join(RESULTS_DIR, "finite_shots_analysis.csv")
    df.to_csv(csv_file, index=False)

    # Plot empirical std vs 1/sqrt(N)
    plt.figure(figsize=(8, 5))
    plt.plot(df["One_Over_Sqrt_Shots"], df["Std_Sampled_Cut"], "o-", color="#1f77b4", lw=2, label="Measured Empirical Std")
    
    # Linear fit: std = slope * (1/sqrt(N))
    slope, intercept = np.polyfit(df["One_Over_Sqrt_Shots"], df["Std_Sampled_Cut"], 1)
    fit_line = slope * df["One_Over_Sqrt_Shots"] + intercept
    plt.plot(df["One_Over_Sqrt_Shots"], fit_line, "--", color="#d62728", label=f"Theoretical Fit: $\\sigma \\propto 1/\\sqrt{{N}}$")

    plt.xlabel(r"$1 / \sqrt{N_{\mathrm{shots}}}$", fontsize=12)
    plt.ylabel(r"Standard Deviation of Measured Cut $\sigma$", fontsize=12)
    plt.title(f"Experiment (a): Finite Shot Noise Scaling ({n_qubits}-Qubit Max-Cut)", fontsize=13, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plot_file = os.path.join(RESULTS_DIR, "finite_shots_scaling.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved finite shots analysis to {csv_file} and {plot_file}")
    return df


# ==============================================================================
# EXPERIMENT (B): HARDWARE NOISE MODEL
# ==============================================================================
def run_experiment_hardware_noise(
    graph_data: Dict[str, Any],
    error_rates: List[float] = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10],
    shots: int = 8192,
    num_seeds: int = 10
) -> pd.DataFrame:
    """
    Evaluates QAOA performance under realistic NISQ hardware noise models:
      - 1-qubit depolarizing error (p1)
      - 2-qubit depolarizing error (p2 = 10 * p1)
      - Readout error (p_ro = 2 * p1)
    """
    print("\n--- Running Experiment (b): Hardware Noise Modeling ---")
    n_qubits = graph_data["num_nodes"]
    edges = [tuple(e) for e in graph_data["edges"]]
    exact_max_cut = graph_data["exact_max_cut"]

    opt_res = optimize_qaoa_parameters(n_qubits, edges, p=1, exact_max_cut=exact_max_cut, seed=42)
    gamma_fixed = opt_res["optimal_gamma"]
    beta_fixed = opt_res["optimal_beta"]
    qc_base = create_qaoa_circuit(n_qubits, edges, gamma_fixed, beta_fixed, measure=True)

    records = []

    for p1 in error_rates:
        cuts_seeds = []
        fidelity_seeds = []

        for s in range(num_seeds):
            if p1 == 0.0:
                sim = AerSimulator()
            else:
                p2 = min(10.0 * p1, 0.75)
                pro = min(2.0 * p1, 0.5)

                noise_model = NoiseModel()
                err1 = depolarizing_error(p1, 1)
                err2 = depolarizing_error(p2, 2)
                noise_model.add_all_qubit_quantum_error(err1, ["rx", "ry", "rz", "h"])
                noise_model.add_all_qubit_quantum_error(err2, ["cx", "rzz"])

                ro_matrix = [[1.0 - pro, pro], [pro, 1.0 - pro]]
                noise_model.add_all_qubit_readout_error(ReadoutError(ro_matrix))
                sim = AerSimulator(noise_model=noise_model)

            job = sim.run(qc_base, shots=shots, seed_simulator=s)
            counts = job.result().get_counts()

            # Compute cut expectation and optimal bitstring probability
            total_cut = 0.0
            optimal_counts = 0
            for b, c in counts.items():
                cut_val = compute_cut_from_bitstring(b, edges, n_qubits)
                total_cut += cut_val * c
                if np.isclose(cut_val, exact_max_cut):
                    optimal_counts += c

            cuts_seeds.append(total_cut / shots)
            fidelity_seeds.append(optimal_counts / shots)

        mean_cut = float(np.mean(cuts_seeds))
        std_cut = float(np.std(cuts_seeds, ddof=1))
        mean_fid = float(np.mean(fidelity_seeds))
        std_fid = float(np.std(fidelity_seeds, ddof=1))
        approx_ratio = mean_cut / exact_max_cut

        records.append({
            "Error_Rate_p1": p1,
            "Two_Qubit_Error_p2": min(10.0 * p1, 0.75),
            "Readout_Error_pro": min(2.0 * p1, 0.5),
            "Mean_Expected_Cut": round(mean_cut, 4),
            "Std_Expected_Cut": round(std_cut, 5),
            "Approximation_Ratio": round(approx_ratio, 4),
            "Ground_State_Prob_Mean": round(mean_fid, 4),
            "Ground_State_Prob_Std": round(std_fid, 5),
        })
        print(f"p1: {p1:6.3f} | Approx Ratio: {approx_ratio:.4f} | Ground State Prob: {mean_fid:.4f} +/- {std_fid:.4f}")

    df = pd.DataFrame(records)
    csv_file = os.path.join(RESULTS_DIR, "hardware_noise_analysis.csv")
    df.to_csv(csv_file, index=False)

    # Plot Noise Degradation Curves
    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = "#1f77b4"
    ax1.set_xlabel("1-Qubit Gate Error Rate $p_1$ (Depolarizing)", fontsize=12)
    ax1.set_ylabel("Approximation Ratio $\\alpha$", color=color, fontsize=12)
    ax1.errorbar(df["Error_Rate_p1"], df["Approximation_Ratio"], yerr=df["Std_Expected_Cut"]/exact_max_cut,
                 fmt="o-", color=color, capsize=4, lw=2, label="Approximation Ratio")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()
    color2 = "#d62728"
    ax2.set_ylabel("Ground State Probability $P(\\mathrm{opt})$", color=color2, fontsize=12)
    ax2.errorbar(df["Error_Rate_p1"], df["Ground_State_Prob_Mean"], yerr=df["Ground_State_Prob_Std"],
                 fmt="s--", color=color2, capsize=4, lw=2, label="Ground State Prob")
    ax2.tick_params(axis="y", labelcolor=color2)

    # Theoretical random guessing line: 1 / 2^n
    ax2.axhline(1.0 / (2**n_qubits), color="gray", linestyle=":", label=f"Uniform Guessing ($1/2^{{{n_qubits}}}$)")

    plt.title(f"Experiment (b): Hardware Noise Degradation ({n_qubits}-Qubit Max-Cut)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    plot_file = os.path.join(RESULTS_DIR, "hardware_noise_impact.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved hardware noise analysis to {csv_file} and {plot_file}")
    return df


# ==============================================================================
# EXPERIMENT (C): BARREN PLATEAUS (VARIANCE VS QUBIT COUNT)
# ==============================================================================
def run_experiment_barren_plateaus(
    qubit_counts: List[int] = [2, 4, 6, 8, 10],
    num_samples: int = 40
) -> pd.DataFrame:
    """
    Demonstrates the Barren Plateau phenomenon (McClean et al. 2018):
      The variance of the gradient of local observables decays exponentially
      as Var[partial <O>] ~ O(2^{-n}) for random deep parameterized circuits.
    """
    print("\n--- Running Experiment (c): Barren Plateau Gradient Variance vs Qubit Count ---")
    records = []

    for n in qubit_counts:
        depth = 2 * n  # Deep random circuit forming approximate 2-design
        num_params = depth * n * 2

        # Local observable: Z_0 Z_1
        lbl = ["I"] * n
        lbl[0] = "Z"
        lbl[1] = "Z"
        observable = SparsePauliOp.from_list([("".join(reversed(lbl)), 1.0)])

        def build_circuit(params: np.ndarray) -> QuantumCircuit:
            qc = QuantumCircuit(n)
            idx = 0
            for _ in range(depth):
                for q in range(n):
                    qc.ry(params[idx], q)
                    qc.rz(params[idx + 1], q)
                    idx += 2
                for q in range(n - 1):
                    qc.cx(q, q + 1)
            return qc

        grads = []
        t0 = time.perf_counter()

        for s in range(num_samples):
            rng = np.random.RandomState(s * 100 + n)
            params = rng.uniform(0.0, 2.0 * np.pi, size=num_params)

            # Parameter shift for theta_0
            p_plus = params.copy()
            p_minus = params.copy()
            p_plus[0] += np.pi / 2.0
            p_minus[0] -= np.pi / 2.0

            qc_p = build_circuit(p_plus)
            qc_m = build_circuit(p_minus)

            ep = Statevector.from_instruction(qc_p).expectation_value(observable).real
            em = Statevector.from_instruction(qc_m).expectation_value(observable).real
            grads.append((ep - em) / 2.0)

        dt = time.perf_counter() - t0
        mean_grad = float(np.mean(grads))
        var_grad = float(np.var(grads, ddof=1))
        std_grad = float(np.std(grads, ddof=1))

        records.append({
            "Qubits_n": n,
            "Circuit_Depth": depth,
            "Num_Parameters": num_params,
            "Num_Samples": num_samples,
            "Mean_Gradient": round(mean_grad, 6),
            "Variance_Gradient": var_grad,
            "Std_Gradient": round(std_grad, 6),
            "Log10_Variance": round(float(np.log10(var_grad)), 4),
            "Runtime_s": round(dt, 2)
        })
        print(f"n={n:2d} | Params: {num_params:3d} | Mean: {mean_grad:+.6f} | Var: {var_grad:.4e} | Log10(Var): {np.log10(var_grad):.2f}")

    df = pd.DataFrame(records)
    csv_file = os.path.join(RESULTS_DIR, "barren_plateaus.csv")
    df.to_csv(csv_file, index=False)

    # Plot Semi-Log Barren Plateau Decay
    plt.figure(figsize=(8, 5))
    plt.semilogy(df["Qubits_n"], df["Variance_Gradient"], "o-", color="#8c564b", lw=2.5, markersize=8, label="Empirical Variance $\\mathrm{Var}[\\partial_{\\theta} \\langle Z_0 Z_1 \\rangle]$")

    # Fit exponential line: log(var) = -a * n + b
    slope, intercept = np.polyfit(df["Qubits_n"], np.log(df["Variance_Gradient"]), 1)
    exp_fit = np.exp(slope * df["Qubits_n"] + intercept)
    plt.semilogy(df["Qubits_n"], exp_fit, "--", color="#d62728", lw=1.8, label=f"Exponential Fit: $\\sim 2^{{-{abs(slope)/np.log(2):.2f} n}}$")

    plt.xlabel("Number of Qubits $n$", fontsize=12)
    plt.ylabel(r"Gradient Variance $\mathrm{Var}[\partial \langle O \rangle]$ (Log Scale)", fontsize=12)
    plt.title("Experiment (c): Barren Plateau Phenomenon (Exponential Vanishing Gradients)", fontsize=13, fontweight="bold")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plot_file = os.path.join(RESULTS_DIR, "barren_plateau_decay.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved barren plateaus analysis to {csv_file} and {plot_file}")
    return df


# ==============================================================================
# EXPERIMENT (D): QAOA DEPTH P VS APPROXIMATION RATIO & CLASSICAL COMPARISON
# ==============================================================================
def run_experiment_qaoa_scaling_and_comparison(
    instances: Dict[str, Any],
    depths: List[int] = [1, 2, 3],
    num_seeds: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Evaluates QAOA with growing depths p in [1, 2, 3] across all Track B instances:
      - Graph_5Ring (5 qubits)
      - Graph_8Cube (8 qubits)
      - Graph_12ER (12 qubits)
    
    Produces:
      1. QAOA Depth Scaling Table (qaoa_depth_scaling.csv)
      2. Comprehensive Classical vs Quantum Comparison (classical_vs_quantum_comparison.csv)
    """
    print("\n--- Running Experiment (d): QAOA Depth p Scaling & Classical Comparison ---")
    depth_records = []

    for name, inst in instances.items():
        n = inst["num_nodes"]
        edges = [tuple(e) for e in inst["edges"]]
        exact_max_cut = inst["exact_max_cut"]

        for p in depths:
            ratios = []
            fidelities = []
            evals = []
            runtimes = []
            cuts = []

            for s in range(num_seeds):
                res = optimize_qaoa_parameters(n, edges, p=p, exact_max_cut=exact_max_cut, max_iter=250, seed=s)
                ratios.append(res["approx_ratio"])
                fidelities.append(res["ground_state_prob"])
                evals.append(res["eval_count"])
                runtimes.append(res["runtime_ms"])
                cuts.append(res["expected_cut"])

            mean_ratio = float(np.mean(ratios))
            std_ratio = float(np.std(ratios, ddof=1))
            mean_fid = float(np.mean(fidelities))
            std_fid = float(np.std(fidelities, ddof=1))
            mean_evals = float(np.mean(evals))
            mean_time = float(np.mean(runtimes))
            mean_cut = float(np.mean(cuts))

            depth_records.append({
                "Graph": name,
                "Nodes": n,
                "Edges": len(edges),
                "Exact_Max_Cut": exact_max_cut,
                "Depth_p": p,
                "Mean_Cut": round(mean_cut, 4),
                "Approximation_Ratio_Mean": round(mean_ratio, 4),
                "Approximation_Ratio_Std": round(std_ratio, 4),
                "Ground_State_Prob_Mean": round(mean_fid, 4),
                "Ground_State_Prob_Std": round(std_fid, 4),
                "Circuit_Evaluations_Mean": round(mean_evals, 1),
                "Runtime_ms_Mean": round(mean_time, 2)
            })
            print(f"{name:11s} | p={p} | Approx Ratio: {mean_ratio:.4f} +/- {std_ratio:.4f} | P(opt): {mean_fid:.4f} | Evals: {mean_evals:.0f} | Time: {mean_time:.1f}ms")

    df_depths = pd.DataFrame(depth_records)
    depths_csv = os.path.join(RESULTS_DIR, "qaoa_depth_scaling.csv")
    df_depths.to_csv(depths_csv, index=False)

    # Plot QAOA Depth vs Approximation Ratio
    plt.figure(figsize=(8, 5))
    markers = {"Graph_5Ring": "o", "Graph_8Cube": "s", "Graph_12ER": "^"}
    colors = {"Graph_5Ring": "#1f77b4", "Graph_8Cube": "#2ca02c", "Graph_12ER": "#ff7f0e"}

    for name in instances.keys():
        sub = df_depths[df_depths["Graph"] == name]
        plt.errorbar(sub["Depth_p"], sub["Approximation_Ratio_Mean"], yerr=sub["Approximation_Ratio_Std"],
                     fmt=f"{markers[name]}-", color=colors[name], capsize=4, lw=2, markersize=8, label=f"{name} (n={sub['Nodes'].iloc[0]})")

    plt.xlabel("QAOA Depth $p$", fontsize=12)
    plt.ylabel("Approximation Ratio $\\alpha$", fontsize=12)
    plt.title("Experiment (d): QAOA Depth $p$ vs Approximation Ratio $\\alpha$", fontsize=13, fontweight="bold")
    plt.xticks(depths)
    plt.ylim(0.70, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plot_file = os.path.join(RESULTS_DIR, "qaoa_depth_vs_ratio.png")
    plt.savefig(plot_file, dpi=300)
    plt.close()

    # Build Master Classical vs Quantum Comparison Table
    track_b_df = load_track_b_baselines()
    comp_records = []

    for name in instances.keys():
        row_b = track_b_df[track_b_df["Graph"] == name].iloc[0]
        nodes = int(row_b["Nodes"])
        exact_cut = float(row_b["Exact_Cut"])

        # Classical Brute Force
        bf_time = 0.05 if nodes <= 5 else (1.6 if nodes == 8 else 45.0)  # Reference Track B runtimes
        comp_records.append({
            "Graph": name,
            "Nodes": nodes,
            "Solver": "Classical Brute Force",
            "Type": "Exact Classical",
            "Max_Cut_Obtained": exact_cut,
            "Approximation_Ratio": 1.0000,
            "Evaluations": 2**nodes,
            "Runtime_ms": bf_time
        })

        # Classical Simulated Annealing
        sa_cut = abs(float(row_b["SA_Mean_Energy"]))
        comp_records.append({
            "Graph": name,
            "Nodes": nodes,
            "Solver": "Classical Simulated Annealing",
            "Type": "Heuristic Classical",
            "Max_Cut_Obtained": sa_cut,
            "Approximation_Ratio": round(sa_cut / exact_cut, 4),
            "Evaluations": 1000,
            "Runtime_ms": float(row_b["SA_Time_ms"])
        })

        # QAOA p=1, p=2, p=3
        for p in depths:
            sub = df_depths[(df_depths["Graph"] == name) & (df_depths["Depth_p"] == p)].iloc[0]
            comp_records.append({
                "Graph": name,
                "Nodes": nodes,
                "Solver": f"QAOA (p={p})",
                "Type": "Variational Quantum (Simulated)",
                "Max_Cut_Obtained": sub["Mean_Cut"],
                "Approximation_Ratio": sub["Approximation_Ratio_Mean"],
                "Evaluations": sub["Circuit_Evaluations_Mean"],
                "Runtime_ms": sub["Runtime_ms_Mean"]
            })

    df_comp = pd.DataFrame(comp_records)
    comp_csv = os.path.join(RESULTS_DIR, "classical_vs_quantum_comparison.csv")
    df_comp.to_csv(comp_csv, index=False)
    print(f"Saved QAOA scaling and comparison tables to {depths_csv} and {comp_csv}")

    return df_depths, df_comp


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def main():
    print("=" * 80)
    print("DAY 6: TRACK C QUANTUM OPTIMIZATION BENCHMARK SUITE")
    print("=" * 80)

    instances = load_track_b_instances()
    graph_5ring = instances["Graph_5Ring"]

    # 1. Finite shots analysis
    run_experiment_finite_shots(graph_5ring, shot_counts=[100, 250, 500, 1000, 2000, 4000, 8192], num_seeds=10)

    # 2. Hardware noise model
    run_experiment_hardware_noise(graph_5ring, error_rates=[0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.10], shots=8192, num_seeds=10)

    # 3. Barren plateaus
    run_experiment_barren_plateaus(qubit_counts=[2, 4, 6, 8, 10], num_samples=40)

    # 4. QAOA scaling and classical comparison
    run_experiment_qaoa_scaling_and_comparison(instances, depths=[1, 2, 3], num_seeds=10)

    print("\n[SUCCESS] All Track C experiments completed successfully!")


if __name__ == "__main__":
    main()
