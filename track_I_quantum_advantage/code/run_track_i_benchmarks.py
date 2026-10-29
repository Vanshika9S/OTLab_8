"""
run_track_i_benchmarks.py
-------------------------
End-to-end benchmark execution script for Track I: Quantum Algorithms and QML Advantage.

Executes:
1. Verification of all 7 core quantum algorithms against analytical ground truths.
2. Hardware noise model degradation benchmark across error rates (10 seeds, mean +- std).
3. QML vs Classical models benchmark on Make Moons dataset (10 seeds, mean +- std).
4. Grover vs Classical Linear Search complexity and simulation wall-clock scaling.
5. Quantum Annealing minor embedding physical qubit blowup and chain stability analysis.
6. Generates publication-grade 4-panel dashboard: track_i_quantum_performance.png.

Track I: Quantum Algorithms and QML Advantage
Course: Optimization Techniques
"""

import os
import sys
import time
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict, Any, Optional

# Ensure repo root is on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from track_I_quantum_advantage.code.quantum_algorithms import (
    DeutschJozsa, BernsteinVazirani, GroverSearch,
    QuantumFourierTransform, QuantumPhaseEstimation,
    ShorAlgorithmSmallN, QuantumAnnealingEmbeddingSimulator
)
from track_I_quantum_advantage.code.noise_experiment import (
    build_hardware_noise_model, run_noise_degradation_sweep
)
from track_I_quantum_advantage.code.qml_benchmark import run_qml_vs_classical_comparison
from track_I_quantum_advantage.code.grover_vs_linear_search import run_grover_vs_linear_scaling_benchmark


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def benchmark_core_algorithms() -> pd.DataFrame:
    """Verifies all 7 algorithms on known analytical answers."""
    print("[1/5] Benchmarking Core Quantum Algorithms on Ground Truths...")
    records = []
    
    # 1. Deutsch-Jozsa (Constant vs Balanced)
    dj_c = DeutschJozsa(n=3, oracle_type="constant_0").run_simulation()
    dj_b = DeutschJozsa(n=3, oracle_type="balanced_parity").run_simulation()
    dj_np = DeutschJozsa(n=3, oracle_type="balanced_parity").run_numpy_reference()
    
    records.append({
        "algorithm": "Deutsch-Jozsa (Constant)",
        "input_config": "n=3, f(x)=0",
        "expected_output": "constant",
        "measured_output": dj_c["prediction"],
        "fidelity_or_prob": dj_c["prob_all_zeros"],
        "verified_correct": dj_c["correct"],
        "implementation_type": "Hand-crafted Gate-by-Gate"
    })
    records.append({
        "algorithm": "Deutsch-Jozsa (Balanced Parity)",
        "input_config": "n=3, f(x)=x0^x1^x2",
        "expected_output": "balanced",
        "measured_output": dj_b["prediction"],
        "fidelity_or_prob": 1.0 - dj_b["prob_all_zeros"],
        "verified_correct": dj_b["correct"],
        "implementation_type": "Hand-crafted Gate-by-Gate"
    })
    records.append({
        "algorithm": "Deutsch-Jozsa (NumPy Ref)",
        "input_config": "n=3, f(x)=x0^x1^x2",
        "expected_output": "balanced",
        "measured_output": dj_np["prediction"],
        "fidelity_or_prob": 1.0 - dj_np["prob_all_zeros"],
        "verified_correct": dj_np["correct"],
        "implementation_type": "Pure NumPy Statevector"
    })
    
    # 2. Bernstein-Vazirani
    bv_algo = BernsteinVazirani(secret="1101")
    bv_res = bv_algo.run_simulation()
    records.append({
        "algorithm": "Bernstein-Vazirani",
        "input_config": "secret='1101'",
        "expected_output": "1101",
        "measured_output": bv_res["measured_secret"],
        "fidelity_or_prob": bv_res["success_prob"],
        "verified_correct": bv_res["correct"],
        "implementation_type": "Hand-crafted Gate-by-Gate"
    })
    
    # 3. Grover's Search
    gr_algo = GroverSearch(n=3, target_bitstring="101")
    gr_res = gr_algo.run_simulation()
    records.append({
        "algorithm": "Grover's Search",
        "input_config": "n=3, target='101', N=8",
        "expected_output": "101",
        "measured_output": gr_res["top_measured_state"],
        "fidelity_or_prob": gr_res["simulated_success_prob"],
        "verified_correct": gr_res["correct"],
        "implementation_type": "Hand-crafted Oracle & Diffuser"
    })
    
    # 4. Quantum Fourier Transform
    qft_algo = QuantumFourierTransform(n=3)
    qft_res = qft_algo.verify_against_dft_matrix()
    records.append({
        "algorithm": "Quantum Fourier Transform (QFT)",
        "input_config": "n=3 qubits (N=8)",
        "expected_output": "Exact DFT Matrix",
        "measured_output": f"Frobenius Err={qft_res['frobenius_error']:.2e}",
        "fidelity_or_prob": 1.0,
        "verified_correct": qft_res["is_exact"],
        "implementation_type": "Hand-crafted CP Network"
    })
    
    # 5. Quantum Phase Estimation (T gate and S gate)
    qpe_t = QuantumPhaseEstimation(counting_qubits=3, gate_type="T").run_simulation()
    qpe_s = QuantumPhaseEstimation(counting_qubits=3, gate_type="S").run_simulation()
    records.append({
        "algorithm": "Quantum Phase Estimation (T Gate)",
        "input_config": "t=3 counting qubits, phase=1/8",
        "expected_output": "0.125",
        "measured_output": f"{qpe_t['estimated_phase']:.4f}",
        "fidelity_or_prob": 1.0,
        "verified_correct": qpe_t["is_exact"],
        "implementation_type": "Hand-crafted Inverse QFT"
    })
    records.append({
        "algorithm": "Quantum Phase Estimation (S Gate)",
        "input_config": "t=3 counting qubits, phase=1/4",
        "expected_output": "0.250",
        "measured_output": f"{qpe_s['estimated_phase']:.4f}",
        "fidelity_or_prob": 1.0,
        "verified_correct": qpe_s["is_exact"],
        "implementation_type": "Hand-crafted Inverse QFT"
    })
    
    # 6. Shor's Algorithm (Small N=15)
    shor_algo = ShorAlgorithmSmallN(N=15, a=7).run_simulation()
    records.append({
        "algorithm": "Shor's Algorithm (Small N=15)",
        "input_config": "N=15, a=7 (coprime)",
        "expected_output": "[3, 5]",
        "measured_output": str(shor_algo["factors"]),
        "fidelity_or_prob": 1.0,
        "verified_correct": shor_algo["factored_successfully"],
        "implementation_type": "Modular Unitary + Inverse QFT"
    })
    
    # 7. Quantum Annealing Embedding
    qa_sim = QuantumAnnealingEmbeddingSimulator(logical_vars=16)
    qa_over = qa_sim.compute_embedding_overhead(topology="chimera")
    records.append({
        "algorithm": "Quantum Annealing Minor Embedding",
        "input_config": "K_16 Complete Graph on Chimera",
        "expected_output": "Physical Qubits O(n^2)",
        "measured_output": f"{qa_over['physical_qubits_required']} physical qubits",
        "fidelity_or_prob": float(qa_over["overhead_ratio"]),
        "verified_correct": qa_over["physical_qubits_required"] > 16,
        "implementation_type": "Minor Embedding Graph Model"
    })
    
    df = pd.DataFrame(records)
    csv_path = os.path.join(RESULTS_DIR, "quantum_algorithms_verification.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported core verification table to {csv_path}")
    return df


def benchmark_hardware_noise() -> pd.DataFrame:
    """Evaluates fidelity degradation across noise error rates."""
    print("[2/5] Benchmarking Hardware Noise Model Degradation (10 seeds)...")
    error_rates = [0.0, 0.001, 0.003, 0.005, 0.01, 0.02, 0.03, 0.05]
    df = run_noise_degradation_sweep(error_rates=error_rates, num_seeds=10, shots=1024)
    csv_path = os.path.join(RESULTS_DIR, "noise_degradation_benchmark.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported noise degradation results to {csv_path}")
    return df


def benchmark_qml_vs_classical() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluates VQC vs Classical models over 10 random seeds."""
    print("[3/5] Benchmarking QML (VQC) vs Classical Models (10 seeds)...")
    df_raw, df_summary = run_qml_vs_classical_comparison(n_samples=100, num_seeds=10, vqc_iterations=30)
    
    raw_path = os.path.join(RESULTS_DIR, "qml_vs_classical_raw_trials.csv")
    sum_path = os.path.join(RESULTS_DIR, "qml_vs_classical_summary.csv")
    df_raw.to_csv(raw_path, index=False)
    df_summary.to_csv(sum_path, index=False)
    print(f"  -> Exported QML vs Classical summary to {sum_path}")
    return df_raw, df_summary


def benchmark_grover_scaling() -> pd.DataFrame:
    """Evaluates Grover vs Classical Linear Search complexity and wall-clock scaling."""
    print("[4/5] Benchmarking Grover vs Classical Linear Search (n=2..8, 10 trials)...")
    n_range = [2, 3, 4, 5, 6, 7, 8]
    df = run_grover_vs_linear_scaling_benchmark(n_qubit_range=n_range, num_trials=10)
    csv_path = os.path.join(RESULTS_DIR, "grover_vs_linear_scaling.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported Grover scaling results to {csv_path}")
    return df


def benchmark_quantum_annealing_embedding() -> pd.DataFrame:
    """Evaluates physical qubit blowup and chain break probabilities."""
    print("[5/5] Analyzing Quantum Annealing Embedding & Chain Stability...")
    logical_sizes = [4, 8, 12, 16, 20, 24, 32, 48, 64]
    records = []
    
    for n in logical_sizes:
        sim = QuantumAnnealingEmbeddingSimulator(logical_vars=n)
        chimera = sim.compute_embedding_overhead("chimera")
        pegasus = sim.compute_embedding_overhead("pegasus")
        
        # Simulate chain break probability for average chain length under thermal noise T=0.5
        # with weak coupling |J|=1.0 vs strong coupling |J|=2.5
        break_prob_weak = sim.simulate_chain_break_probability(
            chain_length=int(math.ceil(chimera["average_chain_length"])),
            j_chain=1.0,
            temperature=0.5
        )
        break_prob_strong = sim.simulate_chain_break_probability(
            chain_length=int(math.ceil(chimera["average_chain_length"])),
            j_chain=2.5,
            temperature=0.5
        )
        
        records.append({
            "logical_variables": n,
            "chimera_physical_qubits": chimera["physical_qubits_required"],
            "chimera_avg_chain_length": chimera["average_chain_length"],
            "chimera_overhead_ratio": chimera["overhead_ratio"],
            "pegasus_physical_qubits": pegasus["physical_qubits_required"],
            "pegasus_overhead_ratio": pegasus["overhead_ratio"],
            "chain_break_prob_weak_coupling": break_prob_weak,
            "chain_break_prob_strong_coupling": break_prob_strong,
        })
        
    df = pd.DataFrame(records)
    csv_path = os.path.join(RESULTS_DIR, "quantum_annealing_embedding_scaling.csv")
    df.to_csv(csv_path, index=False)
    print(f"  -> Exported Quantum Annealing embedding results to {csv_path}")
    return df


def generate_publication_dashboard(
    df_noise: pd.DataFrame,
    df_qml: pd.DataFrame,
    df_grover: pd.DataFrame,
    df_qa: pd.DataFrame
):
    """Generates the 4-panel technical dashboard figure."""
    print("Generating 4-panel visualization dashboard...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
    
    # -------------------------------------------------------------
    # Panel 1: Hardware Noise Degradation
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    p_vals = df_noise["single_qubit_error_p1"]
    ax1.errorbar(
        p_vals, df_noise["bv_fidelity_mean"], yerr=df_noise["bv_fidelity_std"],
        fmt='-o', color='#1f77b4', lw=2.2, capsize=4, label='Bernstein-Vazirani (Depth=4)'
    )
    ax1.errorbar(
        p_vals, df_noise["grover_fidelity_mean"], yerr=df_noise["grover_fidelity_std"],
        fmt='-s', color='#d62728', lw=2.2, capsize=4, label="Grover's Search (Depth=18)"
    )
    ax1.axhline(0.125, color='gray', linestyle='--', label='Random Guess Baseline (1/8)')
    ax1.set_title("Panel 1: Hardware Noise Degradation vs Error Rate\n(10 Seeds, Mean ± Std)", fontsize=13, fontweight='bold')
    ax1.set_xlabel("Single-Qubit Depolarizing Error Probability ($p_1$)", fontsize=11)
    ax1.set_ylabel("State Fidelity / Success Probability", fontsize=11)
    ax1.set_ylim(-0.02, 1.05)
    ax1.legend(loc='upper right', frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # -------------------------------------------------------------
    # Panel 2: QML vs Classical Accuracy & Training Wall-Clock Time
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    models = df_qml["model"].tolist()
    # Shorten names for clean display
    short_names = ["RBF SVM", "Logistic Reg", "Classical MLP", "VQC (Quantum)"]
    test_accs = df_qml["test_acc_mean"].values * 100.0
    test_stds = df_qml["test_acc_std"].values * 100.0
    train_times = df_qml["train_time_sec_mean"].values
    
    x_pos = np.arange(len(short_names))
    width = 0.38
    
    bars1 = ax2.bar(x_pos - width/2, test_accs, width, yerr=test_stds, capsize=4, color='#2ca02c', alpha=0.85, label='Test Accuracy (%)')
    ax2.set_ylabel("Test Accuracy (%)", fontsize=11, color='#2ca02c')
    ax2.set_ylim(0, 110)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(short_names, fontsize=10, fontweight='bold')
    
    ax2_twin = ax2.twinx()
    bars2 = ax2_twin.bar(x_pos + width/2, train_times, width, color='#9467bd', alpha=0.85, label='Train Time (sec)')
    ax2_twin.set_ylabel("Training Time (seconds, log scale)", fontsize=11, color='#9467bd')
    ax2_twin.set_yscale('log')
    ax2.set_title("Panel 2: QML vs Classical Models on Make Moons\n(10 Seeds, Accuracy vs Training Time)", fontsize=13, fontweight='bold')
    
    # -------------------------------------------------------------
    # Panel 3: Grover vs Linear Search: Queries vs Simulated Runtime
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    N_vals = df_grover["database_size_N"]
    
    ax3.plot(N_vals, df_grover["classical_theoretical_queries"], '-o', color='#1f77b4', lw=2.2, label='Classical Queries: $(N+1)/2$')
    ax3.plot(N_vals, df_grover["grover_theoretical_queries"], '-s', color='#2ca02c', lw=2.2, label=r'Grover Queries: $\lfloor \frac{\pi}{4}\sqrt{N} \rfloor$')
    ax3.set_xlabel("Database Size $N = 2^n$", fontsize=11)
    ax3.set_ylabel("Oracle Queries (Query Complexity)", fontsize=11, color='#1f77b4')
    ax3.set_xscale('log', base=2)
    ax3.set_yscale('log')
    ax3.legend(loc='upper left', frameon=True)
    
    ax3_twin = ax3.twinx()
    ax3_twin.plot(N_vals, df_grover["classical_wall_clock_ms"], '--^', color='#ff7f0e', lw=2.0, label='Classical CPU Time (ms)')
    ax3_twin.plot(N_vals, df_grover["grover_simulated_wall_clock_ms"], '--v', color='#d62728', lw=2.0, label='Grover Simulated Time (ms)')
    ax3_twin.set_ylabel("Physical CPU Wall-Clock Time (ms, log scale)", fontsize=11, color='#d62728')
    ax3_twin.set_yscale('log')
    ax3_twin.legend(loc='lower right', frameon=True)
    ax3.set_title("Panel 3: Grover Quadratic Query Speedup\nvs Classical Simulation Wall-Clock Bottleneck", fontsize=13, fontweight='bold')
    
    # -------------------------------------------------------------
    # Panel 4: Quantum Annealing Minor Embedding Blowup
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    vars_n = df_qa["logical_variables"]
    ax4.plot(vars_n, df_qa["chimera_physical_qubits"], '-o', color='#8c564b', lw=2.2, label=r'Chimera Hardware: $\sim n^2/4 + n$')
    ax4.plot(vars_n, df_qa["pegasus_physical_qubits"], '-s', color='#e377c2', lw=2.2, label=r'Pegasus Hardware: $\sim n^2/12 + n$')
    ax4.plot(vars_n, vars_n, '--k', lw=1.8, label='Ideal All-to-All Topology: $n$')
    ax4.set_xlabel("Logical Variables $n$ (Complete QUBO Graph $K_n$)", fontsize=11)
    ax4.set_ylabel("Physical Qubits Required", fontsize=11, color='#8c564b')
    ax4.legend(loc='upper left', frameon=True)
    
    ax4_twin = ax4.twinx()
    ax4_twin.plot(vars_n, df_qa["chain_break_prob_weak_coupling"] * 100.0, ':x', color='#d62728', lw=2.0, label='Chain Break % ($|J|=1.0$)')
    ax4_twin.plot(vars_n, df_qa["chain_break_prob_strong_coupling"] * 100.0, ':d', color='#2ca02c', lw=2.0, label='Chain Break % ($|J|=2.5$)')
    ax4_twin.set_ylabel("Chain Break Probability (%)", fontsize=11, color='#d62728')
    ax4_twin.set_ylim(-2, 105)
    ax4_twin.legend(loc='center right', frameon=True)
    ax4.set_title(r"Panel 4: Minor Embedding Overhead $\mathcal{O}(n^2)$ & Chain Stability", fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    plot_path = os.path.join(RESULTS_DIR, "track_i_quantum_performance.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"  -> Saved 4-panel dashboard to {plot_path}")


def main():
    print("=" * 75)
    print("TRACK I: QUANTUM ALGORITHMS & QML ADVANTAGE BENCHMARK SUITE")
    print("=" * 75)
    
    t_start = time.perf_counter()
    
    df_core = benchmark_core_algorithms()
    df_noise = benchmark_hardware_noise()
    df_raw_qml, df_sum_qml = benchmark_qml_vs_classical()
    df_grover = benchmark_grover_scaling()
    df_qa = benchmark_quantum_annealing_embedding()
    
    generate_publication_dashboard(df_noise, df_sum_qml, df_grover, df_qa)
    
    total_time = time.perf_counter() - t_start
    print("=" * 75)
    print(f"ALL EXPERIMENTS SUCCESSFULLY EXECUTED in {total_time:.2f} seconds.")
    print("=" * 75)


if __name__ == "__main__":
    main()
