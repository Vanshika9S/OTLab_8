"""
qaoa_maxcut.py
--------------
Quantum Approximate Optimization Algorithm (QAOA) for Max-Cut on QUBO/Ising models.

Mathematical Formulation:
  For an undirected graph G = (V, E) with edge weights w_{uv} > 0:
    Max-Cut Objective: Maximize C(x) = sum_{(u,v) in E} w_{uv} * (x_u(1 - x_v) + x_v(1 - x_u))
    Binary-to-Spin:    x_i = (1 - s_i) / 2 where s_i in {-1, +1}
    Ising Operator:    C = sum_{(u,v) in E} (w_{uv}/2) * (I - Z_u Z_v)
    Minimization Cost: H_C = -C = sum_{(u,v) in E} (w_{uv}/2) * Z_u Z_v - (W_total / 2) * I

QAOA Circuit Architecture:
  State: |gamma, beta> = prod_{l=1}^p [ U(B, beta_l) U(C, gamma_l) ] |+>^n
  Problem Unitary: U(C, gamma) = exp(-i * gamma * H_C) = prod_{(u,v)} R_ZZ(w_{uv} * gamma)_{u,v}
  Mixer Unitary:   U(B, beta)  = exp(-i * beta * sum_u X_u) = prod_u R_X(2 * beta)_u
  Initial State:   |+>^n = H^{otimes n} |0>^n
"""

import sys
import os
import json
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


def build_maxcut_hamiltonian(n_qubits: int, edges: List[Tuple[int, int, float]]) -> Tuple[SparsePauliOp, SparsePauliOp, float]:
    """
    Constructs the Cut operator C and the Cost Hamiltonian H_C = -C for QAOA.
    
    Returns:
      (H_C, C_op, constant_offset)
      where H_C = -C_op is minimized.
    """
    pauli_cost = []
    pauli_cut = []
    total_weight = 0.0

    for u, v, w in edges:
        total_weight += w
        # Qiskit qubit index string is reversed: q_{n-1} ... q_0
        label_zz = ["I"] * n_qubits
        label_zz[u] = "Z"
        label_zz[v] = "Z"
        pauli_str = "".join(reversed(label_zz))

        # Cost: + 0.5 * w * Z_u Z_v
        pauli_cost.append((pauli_str, 0.5 * w))
        # Cut: - 0.5 * w * Z_u Z_v
        pauli_cut.append((pauli_str, -0.5 * w))

    # Add constant identity term: -0.5 * total_weight for Cost, +0.5 * total_weight for Cut
    pauli_cost.append(("I" * n_qubits, -0.5 * total_weight))
    pauli_cut.append(("I" * n_qubits, 0.5 * total_weight))

    H_C = SparsePauliOp.from_list(pauli_cost).simplify()
    C_op = SparsePauliOp.from_list(pauli_cut).simplify()

    return H_C, C_op, total_weight


def compute_cut_from_bitstring(bitstring: str, edges: List[Tuple[int, int, float]], n_qubits: int) -> float:
    """
    Computes classical cut value for a binary bitstring.
    Note: bitstring from Qiskit is ordered q_{n-1} ... q_0.
    """
    cut = 0.0
    for u, v, w in edges:
        val_u = int(bitstring[n_qubits - 1 - u])
        val_v = int(bitstring[n_qubits - 1 - v])
        if val_u != val_v:
            cut += w
    return cut


def create_qaoa_circuit(
    n_qubits: int,
    edges: List[Tuple[int, int, float]],
    gammas: List[float],
    betas: List[float],
    measure: bool = False
) -> QuantumCircuit:
    """
    Constructs a depth-p QAOA quantum circuit.
    
    Parameters:
      n_qubits: number of vertices/qubits
      edges: list of (u, v, weight)
      gammas: list of length p problem unitary angles
      betas: list of length p mixer unitary angles
      measure: whether to append computational basis measurements
    """
    p = len(gammas)
    assert len(betas) == p, f"Mismatch: {len(gammas)} gammas vs {len(betas)} betas"

    qc = QuantumCircuit(n_qubits)
    # Initial equal superposition state |+>^n
    qc.h(range(n_qubits))

    for layer in range(p):
        g = gammas[layer]
        b = betas[layer]

        # Problem Unitary: exp(-i * g * (w/2) * Z_u Z_v) = R_ZZ(g * w)
        for u, v, w in edges:
            qc.rzz(g * w, u, v)

        # Mixer Unitary: exp(-i * b * X_u) = R_X(2 * b)
        for i in range(n_qubits):
            qc.rx(2.0 * b, i)

    if measure:
        qc.measure_all()

    return qc


def evaluate_qaoa_energy_statevector(
    qc: QuantumCircuit,
    H_C: SparsePauliOp
) -> Tuple[float, float, Dict[str, float]]:
    """
    Evaluates exact expectation values using Qiskit Statevector.
    
    Returns:
      (expected_cost, expected_cut, probability_distribution)
    """
    sv = Statevector.from_instruction(qc)
    cost = float(sv.expectation_value(H_C).real)
    cut = -cost
    probs = sv.probabilities_dict()
    return cost, cut, probs


def evaluate_qaoa_shots(
    qc: QuantumCircuit,
    edges: List[Tuple[int, int, float]],
    n_shots: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, float, Dict[str, int]]:
    """
    Evaluates QAOA expectation value using shot-based measurement simulation.
    
    Returns:
      (mean_cut, cut_std, counts_dict)
    """
    from qiskit_aer import AerSimulator
    
    qc_meas = qc.copy()
    if qc_meas.num_clbits == 0:
        qc_meas.measure_all()

    sim = AerSimulator()
    job = sim.run(qc_meas, shots=n_shots, seed_simulator=seed)
    counts = job.result().get_counts()

    n_qubits = qc.num_qubits
    cut_samples = []
    for bitstr, count in counts.items():
        cut_val = compute_cut_from_bitstring(bitstr, edges, n_qubits)
        cut_samples.extend([cut_val] * count)

    mean_cut = float(np.mean(cut_samples))
    std_cut = float(np.std(cut_samples))
    return mean_cut, std_cut, counts


def optimize_qaoa_parameters(
    n_qubits: int,
    edges: List[Tuple[int, int, float]],
    p: int = 1,
    exact_max_cut: Optional[float] = None,
    method: str = "COBYLA",
    max_iter: int = 200,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Optimizes QAOA angles (gamma, beta) classically using Nelder-Mead or COBYLA.
    
    Returns:
      Dictionary of results including optimal params, expected cut, approx ratio,
      circuit evaluations count, and execution time.
    """
    H_C, C_op, _ = build_maxcut_hamiltonian(n_qubits, edges)
    rng = np.random.RandomState(seed)

    # Initial parameter guess: gamma in [0, pi], beta in [0, pi/2]
    init_gamma = rng.uniform(0.1, np.pi / 2, size=p)
    init_beta = rng.uniform(0.1, np.pi / 4, size=p)
    init_params = np.concatenate([init_gamma, init_beta])

    eval_count = 0
    t0 = time.perf_counter()

    def loss_func(params: np.ndarray) -> float:
        nonlocal eval_count
        eval_count += 1
        g = params[:p]
        b = params[p:]
        qc = create_qaoa_circuit(n_qubits, edges, g, b, measure=False)
        sv = Statevector.from_instruction(qc)
        cost = sv.expectation_value(H_C).real
        return float(cost)

    res = minimize(loss_func, init_params, method=method, options={"maxiter": max_iter})
    t_elapsed = time.perf_counter() - t0

    opt_gamma = res.x[:p].tolist()
    opt_beta = res.x[p:].tolist()
    optimal_cost = float(res.fun)
    expected_cut = -optimal_cost

    # Extract final quantum state and ground state probability
    final_qc = create_qaoa_circuit(n_qubits, edges, opt_gamma, opt_beta, measure=False)
    final_sv = Statevector.from_instruction(final_qc)
    probs = final_sv.probabilities_dict()

    # Find highest probability bitstring and exact ground state probability
    best_bitstring = max(probs, key=probs.get)
    best_bitstring_cut = compute_cut_from_bitstring(best_bitstring, edges, n_qubits)

    ground_state_prob = 0.0
    if exact_max_cut is not None:
        approx_ratio = expected_cut / exact_max_cut
        # Sum probabilities of all bitstrings achieving the exact max cut
        for bitstr, prob in probs.items():
            if np.isclose(compute_cut_from_bitstring(bitstr, edges, n_qubits), exact_max_cut):
                ground_state_prob += prob
    else:
        approx_ratio = None

    return {
        "depth_p": p,
        "n_qubits": n_qubits,
        "optimal_gamma": opt_gamma,
        "optimal_beta": opt_beta,
        "optimal_cost": optimal_cost,
        "expected_cut": expected_cut,
        "exact_max_cut": exact_max_cut,
        "approx_ratio": approx_ratio,
        "ground_state_prob": ground_state_prob,
        "best_bitstring": best_bitstring,
        "best_bitstring_cut": best_bitstring_cut,
        "eval_count": eval_count,
        "runtime_ms": t_elapsed * 1000.0,
        "converged": res.success
    }
