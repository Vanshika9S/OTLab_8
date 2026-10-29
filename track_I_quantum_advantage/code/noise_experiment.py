"""
noise_experiment.py
-------------------
Evaluates the impact of physical hardware noise models on quantum algorithm fidelity.

Components:
1. Depolarizing gate error (single-qubit and two-qubit CX gates).
2. Readout assignment error on measurement.
3. Benchmark sweeps across noise probabilities on Bernstein-Vazirani and Grover Search.
4. Repeated trials (10 seeds, mean +- std) demonstrating fidelity degradation.

Track I: Quantum Algorithms and QML Advantage
Course: Optimization Techniques
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

from track_I_quantum_advantage.code.quantum_algorithms import BernsteinVazirani, GroverSearch


def build_hardware_noise_model(
    p1_error: float,
    p2_error_factor: float = 10.0,
    readout_error_factor: float = 2.0
) -> NoiseModel:
    """
    Constructs a calibrated NISQ-like hardware noise model.
    - Single-qubit depolarizing error: p1_error
    - Two-qubit CX depolarizing error: p2_error = p1_error * p2_error_factor
    - Readout bit-flip error: p_ro = p1_error * readout_error_factor
    """
    noise_model = NoiseModel()
    
    if p1_error > 0.0:
        # 1-qubit gate error on 'h', 'x', 'z', 'p', 'sx'
        error_1q = depolarizing_error(p1_error, 1)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'x', 'z', 'p', 'sx'])
        
        # 2-qubit gate error on 'cx', 'cz', 'cp', 'swap'
        p2_error = min(0.5, p1_error * p2_error_factor)
        error_2q = depolarizing_error(p2_error, 2)
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cz', 'cp', 'swap'])
        
        # Readout error on measurement
        p_ro = min(0.4, p1_error * readout_error_factor)
        # Probability matrix: P(meas=j | prep=i)
        ro_matrix = [[1.0 - p_ro, p_ro], [p_ro, 1.0 - p_ro]]
        readout_err = ReadoutError(ro_matrix)
        noise_model.add_all_qubit_readout_error(readout_err)
        
    return noise_model


def run_noise_degradation_sweep(
    error_rates: List[float] = [0.0, 0.001, 0.003, 0.005, 0.01, 0.02, 0.03, 0.05],
    num_seeds: int = 10,
    shots: int = 2048
) -> pd.DataFrame:
    """
    Sweeps hardware noise levels over 10 seeds, measuring state fidelity and success probability
    on Bernstein-Vazirani (secret '1101') and 3-qubit Grover Search (target '101').
    """
    records = []
    
    # 1. Bernstein-Vazirani benchmark (secret '1101')
    bv_algo = BernsteinVazirani(secret="1101")
    bv_qc = bv_algo.circuit
    
    # 2. Grover Search benchmark (n=3, target '101')
    grover_algo = GroverSearch(n=3, target_bitstring="101")
    grover_qc = grover_algo.circuit

    for p in error_rates:
        noise_model = build_hardware_noise_model(p)
        
        bv_succ_list = []
        gr_succ_list = []
        
        for seed in range(42, 42 + num_seeds):
            sim = AerSimulator(noise_model=noise_model, seed_simulator=seed)
            
            # BV run
            t_bv = transpile(bv_qc, sim)
            res_bv = sim.run(t_bv, shots=shots).result()
            counts_bv = res_bv.get_counts()
            bv_succ = counts_bv.get("1101", 0) / shots
            bv_succ_list.append(bv_succ)
            
            # Grover run
            t_gr = transpile(grover_qc, sim)
            res_gr = sim.run(t_gr, shots=shots).result()
            counts_gr = res_gr.get_counts()
            gr_succ = counts_gr.get("101", 0) / shots
            gr_succ_list.append(gr_succ)
            
        bv_mean = float(np.mean(bv_succ_list))
        bv_std = float(np.std(bv_succ_list))
        gr_mean = float(np.mean(gr_succ_list))
        gr_std = float(np.std(gr_succ_list))
        
        records.append({
            "single_qubit_error_p1": p,
            "two_qubit_error_p2": min(0.5, p * 10.0),
            "readout_error": min(0.4, p * 2.0),
            "bv_fidelity_mean": bv_mean,
            "bv_fidelity_std": bv_std,
            "grover_fidelity_mean": gr_mean,
            "grover_fidelity_std": gr_std,
        })
        
    df = pd.DataFrame(records)
    return df
