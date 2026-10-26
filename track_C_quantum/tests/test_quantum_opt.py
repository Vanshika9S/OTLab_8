"""
test_quantum_opt.py
-------------------
Unit tests for Track C Quantum Optimization:
  1. Parameter-shift rule vs finite-difference analytical agreement
  2. QAOA Cut expectation value vs exact classical cut calculation
  3. VQE convergence to exact ground state energy of physical Hamiltonian
  4. SPSA stochastic gradient expectation alignment with true gradient
  5. Quantum Natural Gradient Fubini-Study metric positive semi-definiteness
  6. Barren plateau variance decay on scaling qubit counts
"""

import os
import sys
import pytest
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp

from track_C_quantum.code.qaoa_maxcut import (
    build_maxcut_hamiltonian,
    compute_cut_from_bitstring,
    create_qaoa_circuit,
    evaluate_qaoa_energy_statevector,
    optimize_qaoa_parameters,
)
from track_C_quantum.code.vqe_solver import (
    build_h2_hamiltonian,
    create_vqe_ansatz,
    solve_vqe,
)
from track_C_quantum.code.gradients_and_qnn import (
    compute_parameter_shift_gradient,
    compute_finite_difference_gradient,
    verify_parameter_shift_vs_fd,
    compute_spsa_gradient,
    compute_quantum_fisher_information,
    compute_quantum_natural_gradient,
    ParameterizedQNN,
)


def test_parameter_shift_vs_finite_difference():
    """Verifies that Parameter-Shift analytical gradients match Finite Differences within 1e-5."""
    qnn = ParameterizedQNN(n_qubits=2, n_layers=1, seed=42)
    x = np.array([0.5, -0.8])

    def circuit_builder(w: np.ndarray) -> QuantumCircuit:
        return qnn.build_circuit(x, w)

    res = verify_parameter_shift_vs_fd(circuit_builder, qnn.weights, qnn.observable, eps=1e-5)
    assert res["match"], f"Parameter shift mismatch: max error {res['max_abs_error']}"
    assert res["max_abs_error"] < 1e-5, f"Expected < 1e-5, got {res['max_abs_error']}"


def test_qaoa_cut_expectation():
    """Verifies QAOA Cut operator expectation value against classical cut for computational basis states."""
    n_qubits = 5
    edges = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 4, 1.0), (4, 0, 1.0)]
    H_C, C_op, _ = build_maxcut_hamiltonian(n_qubits, edges)

    # Test state |01010>: q4=0, q3=1, q2=0, q1=1, q0=0 -> string '01010'
    qc = QuantumCircuit(5)
    qc.x(1)
    qc.x(3)
    sv = Statevector.from_instruction(qc)

    exp_cut = sv.expectation_value(C_op).real
    classical_cut = compute_cut_from_bitstring("01010", edges, n_qubits)

    assert np.isclose(exp_cut, classical_cut), f"Quantum cut {exp_cut} != classical {classical_cut}"
    # In 5-ring, cutting edges (0,1), (1,2), (2,3), (3,4) gives cut = 4.0
    assert np.isclose(classical_cut, 4.0)


def test_vqe_known_ground_state():
    """Verifies VQE converges to exact minimum eigenvalue of H2 Hamiltonian within chemical accuracy (< 0.001 Ha)."""
    H, exact_energy, _ = build_h2_hamiltonian()
    res = solve_vqe(H, exact_energy, optimizer_method="COBYLA", max_iter=250, seed=42)

    assert res["converged"], f"VQE did not converge: final energy {res['vqe_energy']} vs exact {exact_energy}"
    assert res["energy_error"] < 1e-3, f"Energy error {res['energy_error']} exceeds 1e-3 threshold"
    assert res["state_fidelity"] > 0.99, f"Fidelity {res['state_fidelity']} < 0.99"


def test_spsa_gradient_approximation():
    """Verifies that average SPSA gradient aligns with true parameter-shift gradient."""
    qnn = ParameterizedQNN(n_qubits=2, n_layers=1, seed=123)
    x = np.array([0.3, 0.9])

    def circuit_builder(w: np.ndarray) -> QuantumCircuit:
        return qnn.build_circuit(x, w)

    true_grad = compute_parameter_shift_gradient(circuit_builder, qnn.weights, qnn.observable)

    # Accumulate 80 SPSA gradient estimates
    rng = np.random.RandomState(42)
    spsa_estimates = []
    for _ in range(80):
        g_est, _ = compute_spsa_gradient(circuit_builder, qnn.weights, qnn.observable, c_k=0.08, rng=rng)
        spsa_estimates.append(g_est)

    mean_spsa = np.mean(spsa_estimates, axis=0)

    # Cosine similarity
    norm_true = np.linalg.norm(true_grad)
    norm_spsa = np.linalg.norm(mean_spsa)
    cos_sim = np.dot(true_grad, mean_spsa) / (norm_true * norm_spsa)

    assert cos_sim > 0.70, f"Expected SPSA cosine similarity > 0.70, got {cos_sim:.3f}"


def test_quantum_natural_gradient_metric():
    """Verifies Fubini-Study Quantum Fisher Information metric is symmetric positive semi-definite."""
    qnn = ParameterizedQNN(n_qubits=2, n_layers=1, seed=99)
    x = np.array([0.4, -0.6])

    def circuit_builder(w: np.ndarray) -> QuantumCircuit:
        return qnn.build_circuit(x, w)

    QFI = compute_quantum_fisher_information(circuit_builder, qnn.weights)

    # Check symmetry
    assert np.allclose(QFI, QFI.T, atol=1e-8), "QFI matrix must be symmetric"

    # Check positive semi-definiteness: all eigenvalues >= -1e-6
    evals = np.linalg.eigvalsh(QFI)
    assert np.all(evals >= -1e-6), f"Eigenvalues must be non-negative, got min: {np.min(evals)}"


def test_barren_plateau_variance_decay():
    """Verifies that gradient variance decays significantly from n=2 to n=6."""
    obs_2 = SparsePauliOp.from_list([("ZZ", 1.0)])
    obs_6 = SparsePauliOp.from_list([("IIIIZZ", 1.0)])

    def build_test_circuit(n: int, params: np.ndarray) -> QuantumCircuit:
        qc = QuantumCircuit(n)
        idx = 0
        depth = 2 * n
        for _ in range(depth):
            for q in range(n):
                qc.ry(params[idx], q)
                qc.rz(params[idx + 1], q)
                idx += 2
            for q in range(n - 1):
                qc.cx(q, q + 1)
        return qc

    # Sample gradients for n=2
    grads_2 = []
    for s in range(25):
        rng = np.random.RandomState(s)
        p = rng.uniform(0, 2 * np.pi, size=2 * 4 * 2)
        pp, pm = p.copy(), p.copy()
        pp[0] += np.pi / 2
        pm[0] -= np.pi / 2
        ep = Statevector.from_instruction(build_test_circuit(2, pp)).expectation_value(obs_2).real
        em = Statevector.from_instruction(build_test_circuit(2, pm)).expectation_value(obs_2).real
        grads_2.append((ep - em) / 2.0)

    # Sample gradients for n=6
    grads_6 = []
    for s in range(25):
        rng = np.random.RandomState(s + 50)
        p = rng.uniform(0, 2 * np.pi, size=6 * 12 * 2)
        pp, pm = p.copy(), p.copy()
        pp[0] += np.pi / 2
        pm[0] -= np.pi / 2
        ep = Statevector.from_instruction(build_test_circuit(6, pp)).expectation_value(obs_6).real
        em = Statevector.from_instruction(build_test_circuit(6, pm)).expectation_value(obs_6).real
        grads_6.append((ep - em) / 2.0)

    var_2 = float(np.var(grads_2, ddof=1))
    var_6 = float(np.var(grads_6, ddof=1))

    assert var_6 < var_2, f"Barren plateau condition violated: var_6 ({var_6:.2e}) >= var_2 ({var_2:.2e})"
    assert var_2 / var_6 > 3.0, f"Expected variance decay ratio > 3.0, got {var_2 / var_6:.2f}"
