"""
grover_vs_linear_search.py
--------------------------
Empirical comparison of Grover's Quantum Search vs Classical Linear Search
across database sizes N = 2^n for n in [2..9].

Metrics Compared:
1. Oracle Queries: Theoretical vs Empirical.
2. Gate Counts & Circuit Depth (Transpiled into standard gate basis).
3. Wall-Clock Execution Time: Classical linear search vs Quantum simulation on classical CPU.

Key Takeaway:
Demonstrates the critical distinction between theoretical query complexity O(sqrt(N))
and physical simulation reality, where classical simulation overhead O(N * sqrt(N))
completely reverses any wall-clock advantage.

Track I: Quantum Algorithms and QML Advantage
Course: Optimization Techniques
"""

import time
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from track_I_quantum_advantage.code.quantum_algorithms import GroverSearch


def run_classical_linear_search(N: int, target_idx: int) -> Tuple[int, float]:
    """
    Executes classical linear search over an unstructured list of N items.
    Returns (queries_performed, wall_clock_time_seconds).
    """
    db = list(range(N))
    t0 = time.perf_counter()
    queries = 0
    found = False
    for i in range(N):
        queries += 1
        if db[i] == target_idx:
            found = True
            break
    elapsed = time.perf_counter() - t0
    return queries, elapsed


def run_grover_vs_linear_scaling_benchmark(
    n_qubit_range: List[int] = [2, 3, 4, 5, 6, 7, 8],
    num_trials: int = 10
) -> pd.DataFrame:
    """
    Sweeps database sizes N = 2^n, recording theoretical queries, empirical queries,
    circuit gate counts, and physical wall-clock runtime for both classical and quantum search.
    """
    records = []
    sim = AerSimulator()
    
    for n in n_qubit_range:
        N = 2**n
        
        # --- 1. Classical Linear Search ---
        classical_query_list = []
        classical_time_list = []
        for trial in range(num_trials):
            np.random.seed(42 + trial)
            target_idx = np.random.randint(0, N)
            q, t = run_classical_linear_search(N, target_idx)
            classical_query_list.append(q)
            classical_time_list.append(t)
            
        c_queries_mean = float(np.mean(classical_query_list))
        c_time_mean_ms = float(np.mean(classical_time_list)) * 1000.0  # ms
        c_time_std_ms = float(np.std(classical_time_list)) * 1000.0
        c_queries_theory = (N + 1) / 2.0
        
        # --- 2. Quantum Grover Search ---
        # Target bitstring: target 3 in binary
        target_int = min(3, N - 1)
        target_bitstring = format(target_int, f"0{n}b")
        grover_algo = GroverSearch(n=n, target_bitstring=target_bitstring)
        grover_qc = grover_algo.circuit
        t_qc = transpile(grover_qc, sim)
        
        # Gate counts
        gate_counts = t_qc.count_ops()
        total_gates = sum(gate_counts.values())
        cx_gates = gate_counts.get("cx", 0) + gate_counts.get("cz", 0)
        depth = t_qc.depth()
        
        # Grover simulation wall-clock time
        grover_time_list = []
        for trial in range(num_trials):
            t0 = time.perf_counter()
            _ = sim.run(t_qc, shots=512, seed_simulator=42 + trial).result()
            elapsed = time.perf_counter() - t0
            grover_time_list.append(elapsed)
            
        q_time_mean_ms = float(np.mean(grover_time_list)) * 1000.0  # ms
        q_time_std_ms = float(np.std(grover_time_list)) * 1000.0
        q_queries_theory = grover_algo.optimal_iterations
        
        # Speedup or Slowdown ratio (Classical Time / Quantum Time)
        # Ratio < 1 means quantum simulation is SLOWER than classical linear search!
        wall_clock_ratio = c_time_mean_ms / max(1e-9, q_time_mean_ms)
        theoretical_query_speedup = c_queries_theory / max(1e-9, q_queries_theory)
        
        records.append({
            "num_qubits": n,
            "database_size_N": N,
            "classical_theoretical_queries": c_queries_theory,
            "classical_empirical_queries": c_queries_mean,
            "classical_wall_clock_ms": c_time_mean_ms,
            "classical_wall_clock_std_ms": c_time_std_ms,
            "grover_theoretical_queries": q_queries_theory,
            "grover_circuit_total_gates": total_gates,
            "grover_circuit_cx_gates": cx_gates,
            "grover_circuit_depth": depth,
            "grover_simulated_wall_clock_ms": q_time_mean_ms,
            "grover_simulated_wall_clock_std_ms": q_time_std_ms,
            "theoretical_query_speedup": theoretical_query_speedup,
            "wall_clock_speedup_ratio": wall_clock_ratio,
        })
        
    df = pd.DataFrame(records)
    return df
