"""
test_quantum_algorithms.py
--------------------------
Unit and integration test suite for Track I: Quantum Algorithms and QML Advantage.
Tests all 7 core algorithms, hand-crafted circuits, noise models, QML training,
and Grover vs linear search metrics.
"""

import math
import numpy as np
import pytest

from track_I_quantum_advantage.code.quantum_algorithms import (
    DeutschJozsa, BernsteinVazirani, GroverSearch,
    QuantumFourierTransform, QuantumPhaseEstimation,
    ShorAlgorithmSmallN, QuantumAnnealingEmbeddingSimulator
)
from track_I_quantum_advantage.code.noise_experiment import (
    build_hardware_noise_model, run_noise_degradation_sweep
)
from track_I_quantum_advantage.code.qml_benchmark import VariationalQuantumClassifier
from track_I_quantum_advantage.code.grover_vs_linear_search import run_classical_linear_search


# =====================================================================
# 1. DEUTSCH-JOZSA TESTS
# =====================================================================

def test_deutsch_jozsa_constant():
    dj0 = DeutschJozsa(n=3, oracle_type="constant_0").run_simulation(shots=512, seed=42)
    assert dj0["prediction"] == "constant"
    assert dj0["correct"] is True
    assert dj0["prob_all_zeros"] >= 0.95

    dj1 = DeutschJozsa(n=3, oracle_type="constant_1").run_simulation(shots=512, seed=42)
    assert dj1["prediction"] == "constant"
    assert dj1["correct"] is True


def test_deutsch_jozsa_balanced():
    dj_first = DeutschJozsa(n=3, oracle_type="balanced_first").run_simulation(shots=512, seed=42)
    assert dj_first["prediction"] == "balanced"
    assert dj_first["correct"] is True

    dj_parity = DeutschJozsa(n=4, oracle_type="balanced_parity").run_simulation(shots=512, seed=42)
    assert dj_parity["prediction"] == "balanced"
    assert dj_parity["correct"] is True


def test_deutsch_jozsa_numpy_reference():
    dj_np = DeutschJozsa(n=2, oracle_type="balanced_first").run_numpy_reference()
    assert dj_np["prediction"] == "balanced"
    assert dj_np["correct"] is True


# =====================================================================
# 2. BERNSTEIN-VAZIRANI TESTS
# =====================================================================

def test_bernstein_vazirani_secret_recovery():
    for secret in ["101", "1101", "0110", "11111"]:
        bv = BernsteinVazirani(secret=secret)
        res = bv.run_simulation(shots=512, seed=42)
        assert res["correct"] is True
        assert res["measured_secret"] == secret
        assert res["success_prob"] >= 0.99


# =====================================================================
# 3. GROVER'S SEARCH TESTS
# =====================================================================

def test_grover_search_target_recovery():
    # n=2, N=4, target='10'
    gr2 = GroverSearch(n=2, target_bitstring="10").run_simulation(shots=1024, seed=42)
    assert gr2["correct"] is True
    assert gr2["top_measured_state"] == "10"
    assert gr2["simulated_success_prob"] > 0.90

    # n=3, N=8, target='101'
    gr3 = GroverSearch(n=3, target_bitstring="101").run_simulation(shots=1024, seed=42)
    assert gr3["correct"] is True
    assert gr3["top_measured_state"] == "101"
    assert gr3["simulated_success_prob"] > 0.90


# =====================================================================
# 4. QUANTUM FOURIER TRANSFORM TESTS
# =====================================================================

def test_qft_dft_matrix_equivalence():
    for n in [2, 3]:
        qft = QuantumFourierTransform(n=n)
        res = qft.verify_against_dft_matrix()
        assert res["is_exact"] is True
        assert res["frobenius_error"] < 1e-10


def test_qft_inverse_unitarity():
    for n in [2, 3]:
        qft = QuantumFourierTransform(n=n)
        u_fwd = qft.circuit
        u_inv = qft.inverse_circuit
        from qiskit.quantum_info import Operator
        op_fwd = Operator(u_fwd).data
        op_inv = Operator(u_inv).data
        prod = op_fwd @ op_inv
        diff = np.linalg.norm(prod - np.eye(2**n))
        assert diff < 1e-10


# =====================================================================
# 5. QUANTUM PHASE ESTIMATION TESTS
# =====================================================================

def test_quantum_phase_estimation():
    # T gate has phase 1/8 = 0.125
    qpe_t = QuantumPhaseEstimation(counting_qubits=3, gate_type="T").run_simulation()
    assert qpe_t["is_exact"] is True
    assert abs(qpe_t["estimated_phase"] - 0.125) < 1e-6

    # S gate has phase 1/4 = 0.250
    qpe_s = QuantumPhaseEstimation(counting_qubits=3, gate_type="S").run_simulation()
    assert qpe_s["is_exact"] is True
    assert abs(qpe_s["estimated_phase"] - 0.250) < 1e-6

    # Z gate has phase 1/2 = 0.500
    qpe_z = QuantumPhaseEstimation(counting_qubits=3, gate_type="Z").run_simulation()
    assert qpe_z["is_exact"] is True
    assert abs(qpe_z["estimated_phase"] - 0.500) < 1e-6


# =====================================================================
# 6. SHOR'S ALGORITHM TESTS
# =====================================================================

def test_shor_algorithm_factoring_15():
    shor = ShorAlgorithmSmallN(N=15, a=7).run_simulation(shots=512, seed=42)
    assert shor["factored_successfully"] is True
    assert sorted(shor["factors"]) == [3, 5]
    assert shor["recovered_period"] == 4


# =====================================================================
# 7. QUANTUM ANNEALING & MINOR EMBEDDING TESTS
# =====================================================================

def test_quantum_annealing_embedding_quadratic_blowup():
    sim = QuantumAnnealingEmbeddingSimulator(logical_vars=16)
    chimera = sim.compute_embedding_overhead("chimera")
    pegasus = sim.compute_embedding_overhead("pegasus")
    
    # Complete graph K_16 requires significantly more than 16 physical qubits
    assert chimera["physical_qubits_required"] > 16
    assert pegasus["physical_qubits_required"] > 16
    assert chimera["overhead_ratio"] > 1.0
    # Pegasus has higher connectivity (degree 15 vs 6) so overhead is smaller
    assert pegasus["physical_qubits_required"] < chimera["physical_qubits_required"]


def test_chain_break_probability():
    p_unbroken = QuantumAnnealingEmbeddingSimulator.simulate_chain_break_probability(
        chain_length=1, j_chain=1.0, temperature=0.5
    )
    assert p_unbroken == 0.0

    p_broken_weak = QuantumAnnealingEmbeddingSimulator.simulate_chain_break_probability(
        chain_length=5, j_chain=0.5, temperature=0.5
    )
    p_broken_strong = QuantumAnnealingEmbeddingSimulator.simulate_chain_break_probability(
        chain_length=5, j_chain=3.0, temperature=0.5
    )
    # Stronger coupling reduces chain break probability
    assert p_broken_strong < p_broken_weak


# =====================================================================
# 8. NOISE MODEL TESTS
# =====================================================================

def test_hardware_noise_degradation():
    # Sweep zero vs high noise
    df = run_noise_degradation_sweep(error_rates=[0.0, 0.03], num_seeds=2, shots=500)
    ideal_fid = df.loc[df["single_qubit_error_p1"] == 0.0, "bv_fidelity_mean"].values[0]
    noisy_fid = df.loc[df["single_qubit_error_p1"] == 0.03, "bv_fidelity_mean"].values[0]
    assert ideal_fid == 1.0
    assert noisy_fid < 0.60


# =====================================================================
# 9. QML VQC TESTS
# =====================================================================

def test_vqc_forward_pass_and_predict():
    vqc = VariationalQuantumClassifier(num_qubits=2, num_layers=1, seed=42)
    X = np.array([[0.5, -0.5], [-0.8, 0.8]])
    exp_vals = vqc.predict_expectations(X)
    assert len(exp_vals) == 2
    # Expectation values of Z must lie in [-1, 1]
    assert np.all(exp_vals >= -1.0) and np.all(exp_vals <= 1.0)
    preds = vqc.predict(X)
    assert len(preds) == 2
    assert set(preds).issubset({0, 1})


# =====================================================================
# 10. GROVER VS LINEAR SEARCH TESTS
# =====================================================================

def test_classical_linear_search():
    queries, elapsed = run_classical_linear_search(N=100, target_idx=42)
    assert queries == 43
    assert elapsed >= 0.0
