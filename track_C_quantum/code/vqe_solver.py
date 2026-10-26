"""
vqe_solver.py
-------------
Variational Quantum Eigensolver (VQE) implementation for finding the ground state
of a physical 2-qubit Hamiltonian (molecular H2 / Transverse-Field Ising model).

Mathematical Principle:
  Ritz Variational Principle:
    For any normalized trial wavefunction |psi(theta)>,
    <psi(theta)| H |psi(theta)> >= E_0 (ground state energy).
    Equality holds iff |psi(theta)> is the true ground state.

  Ansatz: Hardware-Efficient Ansatz (HEA):
    q0: -[RY(t0)]-[RZ(t1)]---*---[RY(t4)]-
                              |
    q1: -[RY(t2)]-[RZ(t3)]--(X)--[RY(t5)]-
"""

import sys
import os
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Ensure repo root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from scipy.optimize import minimize


def build_h2_hamiltonian(interatomic_dist_approx: float = 0.735) -> Tuple[SparsePauliOp, float, np.ndarray]:
    """
    Constructs the minimal-basis (STO-3G) 2-qubit effective Hamiltonian for H2
    near equilibrium bond length (R ~ 0.735 Angstroms).
    
    H = g0 * II + g1 * Z0 + g2 * Z1 + g3 * Z0 Z1 + g4 * X0 X1
    
    Returns:
      (H_op, exact_ground_energy, exact_ground_statevector)
    """
    # Standard STO-3G parity mapping coefficients for H2 at 0.735 A
    # Qiskit qubit string order: q1 q0
    pauli_list = [
        ("II", -1.0523732),
        ("IZ",  0.3979374),  # Z0
        ("ZI", -0.3979374),  # Z1
        ("ZZ", -0.0112801),  # Z0 Z1
        ("XX",  0.1809312),  # X0 X1
    ]
    H_op = SparsePauliOp.from_list(pauli_list).simplify()

    # Exact diagonalization
    H_mat = H_op.to_matrix()
    evals, evecs = np.linalg.eigh(H_mat)
    exact_ground_energy = float(evals[0])
    exact_ground_state = evecs[:, 0]

    return H_op, exact_ground_energy, exact_ground_state


def create_vqe_ansatz(theta: np.ndarray, n_qubits: int = 2) -> QuantumCircuit:
    """
    Builds a 2-qubit Hardware-Efficient Ansatz (HEA) with 6 trainable parameters:
      theta[0]: RY on q0
      theta[1]: RZ on q0
      theta[2]: RY on q1
      theta[3]: RZ on q1
      CNOT(0 -> 1)
      theta[4]: RY on q0
      theta[5]: RY on q1
    """
    assert len(theta) == 6, f"Expected 6 parameters, got {len(theta)}"
    qc = QuantumCircuit(n_qubits)

    # Layer 1 rotations
    qc.ry(theta[0], 0)
    qc.rz(theta[1], 0)
    qc.ry(theta[2], 1)
    qc.rz(theta[3], 1)

    # Entangler
    qc.cx(0, 1)

    # Layer 2 rotations
    qc.ry(theta[4], 0)
    qc.ry(theta[5], 1)

    return qc


def solve_vqe(
    hamiltonian: SparsePauliOp,
    exact_energy: float,
    optimizer_method: str = "COBYLA",
    max_iter: int = 250,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Executes VQE optimization to find the ground state of the given Hamiltonian.
    
    Returns:
      Dictionary with convergence trajectory, final energy, ground state error,
      circuit evaluations, and runtime.
    """
    rng = np.random.RandomState(seed)
    init_theta = rng.uniform(-np.pi, np.pi, size=6)

    history = []
    eval_count = 0
    t0 = time.perf_counter()

    def loss_func(theta: np.ndarray) -> float:
        nonlocal eval_count
        eval_count += 1
        qc = create_vqe_ansatz(theta)
        sv = Statevector.from_instruction(qc)
        E = float(sv.expectation_value(hamiltonian).real)
        history.append(E)
        return E

    res = minimize(
        loss_func,
        init_theta,
        method=optimizer_method,
        options={"maxiter": max_iter, "tol": 1e-6}
    )
    t_elapsed = time.perf_counter() - t0

    vqe_energy = float(res.fun)
    energy_error = abs(vqe_energy - exact_energy)

    # Compute fidelity with exact ground state
    final_qc = create_vqe_ansatz(res.x)
    final_sv = np.array(Statevector.from_instruction(final_qc).data)
    
    H_mat = hamiltonian.to_matrix()
    evals, evecs = np.linalg.eigh(H_mat)
    exact_psi = evecs[:, 0]
    fidelity = float(abs(np.vdot(final_sv, exact_psi))**2)

    return {
        "vqe_energy": vqe_energy,
        "exact_energy": exact_energy,
        "energy_error": energy_error,
        "state_fidelity": fidelity,
        "optimal_theta": res.x.tolist(),
        "eval_count": eval_count,
        "iterations": len(history),
        "history": history,
        "runtime_ms": t_elapsed * 1000.0,
        "converged": bool(energy_error < 1e-3)
    }
